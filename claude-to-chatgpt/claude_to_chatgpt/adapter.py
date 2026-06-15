"""Translation layer between the OpenAI Chat Completions API and the Anthropic
Messages API.

Everything in this module operates on plain dicts so it can be unit-tested
without a network connection or the Anthropic SDK. ``app.py`` wires these
functions to FastAPI and the SDK; ``cloudflare-worker.js`` reimplements the same
logic for an edge deployment.
"""

from __future__ import annotations

import base64
import time
import uuid
from typing import Any

# Default Claude model used when the caller's model can't be mapped to anything
# more specific. Opus 4.8 is Anthropic's most capable Opus-tier model.
DEFAULT_MODEL = "claude-opus-4-8"

# Anthropic requires max_tokens; OpenAI treats it as optional. Pick a value that
# stays well under the SDK's non-streaming HTTP-timeout guard (~16k).
DEFAULT_MAX_TOKENS = 4096

# Models that reject the sampling parameters (temperature / top_p / top_k) with
# a 400. Forwarding an OpenAI client's temperature to one of these would break
# every request, so we drop sampling params for them.
NO_SAMPLING_PARAM_MODELS = {
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-fable-5",
    "claude-mythos-5",
}

# Explicit OpenAI -> Claude name mappings. Anything not listed falls through to
# the heuristics in ``map_model``.
MODEL_MAP = {
    "gpt-4": "claude-opus-4-8",
    "gpt-4o": "claude-opus-4-8",
    "gpt-4-turbo": "claude-opus-4-8",
    "gpt-4.1": "claude-opus-4-8",
    "gpt-4.5": "claude-opus-4-8",
    "o1": "claude-opus-4-8",
    "o3": "claude-opus-4-8",
    "gpt-4o-mini": "claude-haiku-4-5",
    "gpt-4.1-mini": "claude-haiku-4-5",
    "gpt-4.1-nano": "claude-haiku-4-5",
    "o1-mini": "claude-haiku-4-5",
    "o3-mini": "claude-haiku-4-5",
    "gpt-3.5-turbo": "claude-haiku-4-5",
}

# Anthropic stop_reason -> OpenAI finish_reason.
FINISH_REASON_MAP = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "max_tokens": "length",
    "tool_use": "tool_calls",
    "refusal": "content_filter",
    "pause_turn": "stop",
}


def map_model(requested: str | None) -> str:
    """Map an OpenAI-style model name onto a Claude model id.

    Claude model ids are passed through untouched, so callers can target a
    specific Claude model directly (e.g. ``claude-sonnet-4-6``).
    """
    if not requested:
        return DEFAULT_MODEL
    if requested.startswith("claude-"):
        return requested
    if requested in MODEL_MAP:
        return MODEL_MAP[requested]

    low = requested.lower()
    if "haiku" in low:
        return "claude-haiku-4-5"
    if "sonnet" in low:
        return "claude-sonnet-4-6"
    if "opus" in low:
        return "claude-opus-4-8"
    if "fable" in low:
        return "claude-fable-5"
    if "mini" in low or "nano" in low or "3.5" in low:
        return "claude-haiku-4-5"
    return DEFAULT_MODEL


def _text_of(content: Any) -> str:
    """Flatten OpenAI message ``content`` (string or content-part array) to text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    return str(content)


def _image_block(image_url: Any) -> dict | None:
    """Convert an OpenAI ``image_url`` content part to an Anthropic image block."""
    url = image_url.get("url") if isinstance(image_url, dict) else image_url
    if not url or not isinstance(url, str):
        return None
    if url.startswith("data:"):
        # data:<media_type>;base64,<data>
        try:
            header, data = url.split(",", 1)
            media_type = header.split(";")[0].removeprefix("data:") or "image/png"
            # Validate it actually decodes; let bad data surface as a skipped block.
            base64.b64decode(data)
        except (ValueError, base64.binascii.Error):
            return None
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data},
        }
    return {"type": "image", "source": {"type": "url", "url": url}}


def _convert_content(content: Any) -> Any:
    """Convert OpenAI message content to Anthropic content (string or block list)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        blocks: list[dict] = []
        for part in content:
            if isinstance(part, str):
                blocks.append({"type": "text", "text": part})
            elif isinstance(part, dict):
                ptype = part.get("type")
                if ptype == "text":
                    blocks.append({"type": "text", "text": part.get("text", "")})
                elif ptype == "image_url":
                    block = _image_block(part.get("image_url"))
                    if block:
                        blocks.append(block)
        # Fall back to a single empty text block so we never send [] content.
        return blocks or ""
    return str(content)


def convert_messages(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """Split OpenAI messages into an Anthropic ``system`` string + message list.

    System/developer messages are concatenated into the top-level system prompt.
    Tool-role messages are folded into user turns as plain text — enough for
    chat use; full OpenAI tool-calling translation is intentionally out of scope.
    """
    system_parts: list[str] = []
    converted: list[dict] = []

    for msg in messages or []:
        role = msg.get("role")
        content = msg.get("content")
        if role in ("system", "developer"):
            text = _text_of(content)
            if text:
                system_parts.append(text)
            continue
        if role == "tool":
            text = _text_of(content)
            converted.append({"role": "user", "content": text})
            continue
        anth_role = "assistant" if role == "assistant" else "user"
        converted.append({"role": anth_role, "content": _convert_content(content)})

    system = "\n\n".join(system_parts) if system_parts else None
    return system, converted


def build_anthropic_request(payload: dict) -> dict:
    """Build kwargs for ``messages.create`` from an OpenAI chat-completions body."""
    model = map_model(payload.get("model"))
    system, messages = convert_messages(payload.get("messages", []))

    max_tokens = (
        payload.get("max_tokens")
        or payload.get("max_completion_tokens")
        or DEFAULT_MAX_TOKENS
    )

    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": int(max_tokens),
    }
    if system:
        request["system"] = system

    stop = payload.get("stop")
    if stop:
        request["stop_sequences"] = [stop] if isinstance(stop, str) else list(stop)

    # Sampling params: drop entirely for models that reject them, and never send
    # both temperature and top_p (Claude 4+ 400s on both at once).
    if model not in NO_SAMPLING_PARAM_MODELS:
        temperature = payload.get("temperature")
        top_p = payload.get("top_p")
        if temperature is not None:
            # OpenAI temperature is 0..2; Anthropic is 0..1. Clamp.
            request["temperature"] = max(0.0, min(float(temperature), 1.0))
        elif top_p is not None:
            request["top_p"] = float(top_p)

    return request


def _new_completion_id() -> str:
    return "chatcmpl-" + uuid.uuid4().hex


def anthropic_to_openai_response(message: dict, requested_model: str) -> dict:
    """Convert an Anthropic message dict to an OpenAI chat-completion object."""
    text = "".join(
        block.get("text", "")
        for block in message.get("content", [])
        if block.get("type") == "text"
    )
    usage = message.get("usage") or {}
    prompt_tokens = usage.get("input_tokens", 0) or 0
    completion_tokens = usage.get("output_tokens", 0) or 0
    finish = FINISH_REASON_MAP.get(message.get("stop_reason"), "stop")

    return {
        "id": _new_completion_id(),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": requested_model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": finish,
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def openai_chunk(
    completion_id: str,
    model: str,
    delta: dict,
    finish_reason: str | None = None,
) -> dict:
    """Build a single OpenAI ``chat.completion.chunk`` object for streaming."""
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {"index": 0, "delta": delta, "finish_reason": finish_reason}
        ],
    }
