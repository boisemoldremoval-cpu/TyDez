"""FastAPI service exposing an OpenAI-compatible API backed by Claude.

Endpoints
---------
- ``POST /v1/chat/completions`` — OpenAI Chat Completions (streaming + non-stream)
- ``GET  /v1/models``           — lists the Claude models, in OpenAI's shape
- ``GET  /``                    — health check

Authentication
--------------
If ``ANTHROPIC_API_KEY`` is set in the environment it is always used (closed
proxy — clients can send any placeholder key). Otherwise the bearer token from
the incoming ``Authorization`` header is used as the Anthropic key (pass-through
proxy — each client supplies their own key).
"""

from __future__ import annotations

import json
import os
import time

import anthropic
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .adapter import (
    FINISH_REASON_MAP,
    anthropic_to_openai_response,
    build_anthropic_request,
    map_model,
    openai_chunk,
    _new_completion_id,
)

app = FastAPI(title="claude-to-chatgpt", version="0.1.0")

# Claude models advertised by GET /v1/models.
ADVERTISED_MODELS = [
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-fable-5",
]


def _resolve_api_key(request: Request) -> str | None:
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def _error_response(status: int, message: str, err_type: str = "invalid_request_error"):
    return JSONResponse(
        status_code=status,
        content={"error": {"message": message, "type": err_type, "code": None}},
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@app.get("/")
async def health() -> dict:
    return {"status": "ok", "service": "claude-to-chatgpt"}


@app.get("/v1/models")
async def list_models() -> dict:
    created = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "created": created,
                "owned_by": "anthropic",
            }
            for model in ADVERTISED_MODELS
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, ValueError):
        return _error_response(400, "Request body is not valid JSON.")

    if not isinstance(payload, dict) or not payload.get("messages"):
        return _error_response(400, "'messages' is required.")

    api_key = _resolve_api_key(request)
    if not api_key:
        return _error_response(
            401,
            "No API key provided. Set ANTHROPIC_API_KEY on the server or send "
            "an 'Authorization: Bearer <anthropic-key>' header.",
            "authentication_error",
        )

    anthropic_request = build_anthropic_request(payload)
    requested_model = payload.get("model") or anthropic_request["model"]
    client = anthropic.AsyncAnthropic(api_key=api_key)

    if payload.get("stream"):
        return StreamingResponse(
            _stream(client, anthropic_request, requested_model),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    try:
        message = await client.messages.create(**anthropic_request)
    except anthropic.APIStatusError as exc:
        return _error_response(exc.status_code, exc.message, "api_error")
    except anthropic.APIError as exc:
        return _error_response(502, str(exc), "api_error")

    return JSONResponse(
        anthropic_to_openai_response(message.model_dump(), requested_model)
    )


async def _stream(client, anthropic_request: dict, requested_model: str):
    """Yield OpenAI-format SSE chunks from an Anthropic streaming response."""
    completion_id = _new_completion_id()
    finish_reason = "stop"

    # Lead chunk announcing the assistant role, matching OpenAI's stream shape.
    yield _sse(openai_chunk(completion_id, requested_model, {"role": "assistant"}))

    try:
        async with client.messages.stream(**anthropic_request) as stream:
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield _sse(
                            openai_chunk(
                                completion_id,
                                requested_model,
                                {"content": event.delta.text},
                            )
                        )
                elif event.type == "message_delta":
                    stop_reason = getattr(event.delta, "stop_reason", None)
                    if stop_reason:
                        finish_reason = FINISH_REASON_MAP.get(stop_reason, "stop")
    except anthropic.APIError as exc:
        # Surface the error inline, then close the stream cleanly.
        yield _sse(
            {
                "error": {
                    "message": str(exc),
                    "type": "api_error",
                    "code": None,
                }
            }
        )
        yield "data: [DONE]\n\n"
        return

    yield _sse(openai_chunk(completion_id, requested_model, {}, finish_reason))
    yield "data: [DONE]\n\n"
