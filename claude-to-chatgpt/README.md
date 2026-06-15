# claude-to-chatgpt

A small proxy that exposes an **OpenAI-compatible** Chat Completions API and
translates every request to Anthropic's **Claude Messages API**. Point any tool
that speaks the OpenAI API (SDKs, LangChain, chat UIs, etc.) at this proxy and
it talks to Claude instead.

This is a modernized take on the idea behind
[jtsang4/claude-to-chatgpt](https://github.com/jtsang4/claude-to-chatgpt):
it targets the current Claude models (`claude-opus-4-8` and friends) and the
current Messages API rather than the legacy text-completion endpoint.

Two deployments are provided, sharing identical translation logic:

| Form | Files | Backed by |
|------|-------|-----------|
| **Python service (FastAPI)** | `claude_to_chatgpt/`, `Dockerfile`, `docker-compose.yml` | the official `anthropic` SDK |
| **Cloudflare Worker** | `cloudflare-worker.js`, `wrangler.toml` | `fetch` to `api.anthropic.com` |

## What it does

- `POST /v1/chat/completions` — Chat Completions, **streaming and non-streaming**
- `GET /v1/models` — lists the available Claude models in OpenAI's format
- `GET /` — health check

### Translation highlights

- **Model mapping** — OpenAI names map to Claude (`gpt-4*` → `claude-opus-4-8`,
  `gpt-4o-mini` / `gpt-3.5-turbo` → `claude-haiku-4-5`, `*sonnet*` →
  `claude-sonnet-4-6`). Any `claude-*` id passes through untouched, so you can
  target a specific model directly.
- **System messages** are lifted into the top-level Anthropic `system` prompt.
- **Vision** — OpenAI `image_url` parts (URL or `data:` base64) become Anthropic
  image blocks.
- **Sampling params** — `temperature`/`top_p` are dropped for models that reject
  them (Opus 4.8/4.7, Fable 5) and never sent together (Claude 4+ rejects both
  at once); `temperature` is clamped from OpenAI's 0–2 range to Anthropic's 0–1.
- **`max_tokens`** defaults to 4096 (the Messages API requires it; OpenAI does not).
- **Finish reasons** map back: `end_turn`→`stop`, `max_tokens`→`length`,
  `refusal`→`content_filter`, etc.

## Authentication

| `ANTHROPIC_API_KEY` set on the server? | Behavior |
|---|---|
| **Yes** | Closed proxy — the server key is always used. Clients may send any placeholder `Authorization` header. |
| **No** | Pass-through proxy — the client's `Authorization: Bearer <key>` is used as the Anthropic key. |

## Run the Python service

```bash
cd claude-to-chatgpt
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # optional (closed-proxy mode)
uvicorn claude_to_chatgpt.app:app --reload --port 8000
```

Or with Docker:

```bash
ANTHROPIC_API_KEY=sk-ant-... docker compose up --build
```

## Deploy the Cloudflare Worker

```bash
cd claude-to-chatgpt
npm install -g wrangler
wrangler secret put ANTHROPIC_API_KEY      # optional (closed-proxy mode)
wrangler deploy
```

## Use it

With the OpenAI Python SDK:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="sk-ant-...")
resp = client.chat.completions.create(
    model="gpt-4",                          # -> claude-opus-4-8
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)
```

With curl (streaming):

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-ant-..." \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "stream": true,
       "messages": [{"role": "user", "content": "Write a haiku about Claude."}]}'
```

## Tests

The translation layer is pure (dict-in, dict-out) and tested without a network:

```bash
cd claude-to-chatgpt
pip install pytest
pytest
```

## Scope & limitations

- Chat-style messages, system prompts, vision, and streaming are supported.
- OpenAI **function/tool calling** is not translated — tool-role messages are
  folded into the conversation as plain text. Adding full tool-call translation
  would be a natural next step.
- `n > 1`, `logprobs`, and other OpenAI-only knobs are ignored.
