/**
 * claude-to-chatgpt — Cloudflare Worker
 *
 * Exposes an OpenAI-compatible Chat Completions API at the edge and translates
 * requests to Anthropic's Claude Messages API. Mirrors the logic in the Python
 * package (claude_to_chatgpt/adapter.py).
 *
 * Deploy:
 *   wrangler deploy
 *   wrangler secret put ANTHROPIC_API_KEY   # optional (closed-proxy mode)
 *
 * Auth: if the ANTHROPIC_API_KEY secret/var is set it is always used. Otherwise
 * the incoming `Authorization: Bearer <key>` is used as the Anthropic key.
 */

const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";
const ANTHROPIC_VERSION = "2023-06-01";

const DEFAULT_MODEL = "claude-opus-4-8";
const DEFAULT_MAX_TOKENS = 4096;

const NO_SAMPLING_PARAM_MODELS = new Set([
  "claude-opus-4-8",
  "claude-opus-4-7",
  "claude-fable-5",
  "claude-mythos-5",
]);

const MODEL_MAP = {
  "gpt-4": "claude-opus-4-8",
  "gpt-4o": "claude-opus-4-8",
  "gpt-4-turbo": "claude-opus-4-8",
  "gpt-4.1": "claude-opus-4-8",
  "gpt-4.5": "claude-opus-4-8",
  o1: "claude-opus-4-8",
  o3: "claude-opus-4-8",
  "gpt-4o-mini": "claude-haiku-4-5",
  "gpt-4.1-mini": "claude-haiku-4-5",
  "gpt-4.1-nano": "claude-haiku-4-5",
  "o1-mini": "claude-haiku-4-5",
  "o3-mini": "claude-haiku-4-5",
  "gpt-3.5-turbo": "claude-haiku-4-5",
};

const FINISH_REASON_MAP = {
  end_turn: "stop",
  stop_sequence: "stop",
  max_tokens: "length",
  tool_use: "tool_calls",
  refusal: "content_filter",
  pause_turn: "stop",
};

const ADVERTISED_MODELS = [
  "claude-opus-4-8",
  "claude-opus-4-7",
  "claude-sonnet-4-6",
  "claude-haiku-4-5",
  "claude-fable-5",
];

function mapModel(requested) {
  if (!requested) return DEFAULT_MODEL;
  if (requested.startsWith("claude-")) return requested;
  if (MODEL_MAP[requested]) return MODEL_MAP[requested];
  const low = requested.toLowerCase();
  if (low.includes("haiku")) return "claude-haiku-4-5";
  if (low.includes("sonnet")) return "claude-sonnet-4-6";
  if (low.includes("opus")) return "claude-opus-4-8";
  if (low.includes("fable")) return "claude-fable-5";
  if (low.includes("mini") || low.includes("nano") || low.includes("3.5"))
    return "claude-haiku-4-5";
  return DEFAULT_MODEL;
}

function textOf(content) {
  if (content == null) return "";
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part) => {
        if (typeof part === "string") return part;
        if (part && part.type === "text") return part.text || "";
        return "";
      })
      .join("");
  }
  return String(content);
}

function imageBlock(imageUrl) {
  const url = imageUrl && typeof imageUrl === "object" ? imageUrl.url : imageUrl;
  if (!url || typeof url !== "string") return null;
  if (url.startsWith("data:")) {
    const comma = url.indexOf(",");
    if (comma === -1) return null;
    const header = url.slice(0, comma);
    const data = url.slice(comma + 1);
    const mediaType = header.split(";")[0].replace(/^data:/, "") || "image/png";
    return {
      type: "image",
      source: { type: "base64", media_type: mediaType, data },
    };
  }
  return { type: "image", source: { type: "url", url } };
}

function convertContent(content) {
  if (content == null) return "";
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    const blocks = [];
    for (const part of content) {
      if (typeof part === "string") {
        blocks.push({ type: "text", text: part });
      } else if (part && part.type === "text") {
        blocks.push({ type: "text", text: part.text || "" });
      } else if (part && part.type === "image_url") {
        const block = imageBlock(part.image_url);
        if (block) blocks.push(block);
      }
    }
    return blocks.length ? blocks : "";
  }
  return String(content);
}

function convertMessages(messages) {
  const systemParts = [];
  const converted = [];
  for (const msg of messages || []) {
    const role = msg.role;
    const content = msg.content;
    if (role === "system" || role === "developer") {
      const text = textOf(content);
      if (text) systemParts.push(text);
      continue;
    }
    if (role === "tool") {
      converted.push({ role: "user", content: textOf(content) });
      continue;
    }
    const anthRole = role === "assistant" ? "assistant" : "user";
    converted.push({ role: anthRole, content: convertContent(content) });
  }
  const system = systemParts.length ? systemParts.join("\n\n") : null;
  return { system, messages: converted };
}

function buildAnthropicRequest(payload) {
  const model = mapModel(payload.model);
  const { system, messages } = convertMessages(payload.messages);
  const maxTokens =
    payload.max_tokens || payload.max_completion_tokens || DEFAULT_MAX_TOKENS;

  const request = { model, messages, max_tokens: Number(maxTokens) };
  if (system) request.system = system;

  if (payload.stop) {
    request.stop_sequences =
      typeof payload.stop === "string" ? [payload.stop] : payload.stop;
  }

  if (!NO_SAMPLING_PARAM_MODELS.has(model)) {
    if (payload.temperature != null) {
      request.temperature = Math.max(0, Math.min(Number(payload.temperature), 1));
    } else if (payload.top_p != null) {
      request.top_p = Number(payload.top_p);
    }
  }

  return request;
}

function newCompletionId() {
  return "chatcmpl-" + crypto.randomUUID().replace(/-/g, "");
}

function anthropicToOpenAIResponse(message, requestedModel) {
  const text = (message.content || [])
    .filter((b) => b.type === "text")
    .map((b) => b.text || "")
    .join("");
  const usage = message.usage || {};
  const promptTokens = usage.input_tokens || 0;
  const completionTokens = usage.output_tokens || 0;
  return {
    id: newCompletionId(),
    object: "chat.completion",
    created: Math.floor(Date.now() / 1000),
    model: requestedModel,
    choices: [
      {
        index: 0,
        message: { role: "assistant", content: text },
        finish_reason: FINISH_REASON_MAP[message.stop_reason] || "stop",
      },
    ],
    usage: {
      prompt_tokens: promptTokens,
      completion_tokens: completionTokens,
      total_tokens: promptTokens + completionTokens,
    },
  };
}

function openaiChunk(id, model, delta, finishReason = null) {
  return {
    id,
    object: "chat.completion.chunk",
    created: Math.floor(Date.now() / 1000),
    model,
    choices: [{ index: 0, delta, finish_reason: finishReason }],
  };
}

function resolveApiKey(request, env) {
  if (env && env.ANTHROPIC_API_KEY) return env.ANTHROPIC_API_KEY;
  const auth = request.headers.get("authorization") || "";
  if (auth.toLowerCase().startsWith("bearer ")) {
    return auth.slice(7).trim() || null;
  }
  return null;
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...corsHeaders() },
  });
}

function errorResponse(status, message, type = "invalid_request_error") {
  return jsonResponse({ error: { message, type, code: null } }, status);
}

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "authorization, content-type",
  };
}

function sse(data) {
  return `data: ${JSON.stringify(data)}\n\n`;
}

/**
 * Transform an Anthropic SSE stream (ReadableStream) into an OpenAI SSE stream.
 */
function transformStream(anthropicBody, completionId, requestedModel) {
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();
  const reader = anthropicBody.getReader();
  let buffer = "";
  let finishReason = "stop";
  let leadSent = false;

  return new ReadableStream({
    async pull(controller) {
      const { done, value } = await reader.read();

      if (!leadSent) {
        controller.enqueue(
          encoder.encode(
            sse(openaiChunk(completionId, requestedModel, { role: "assistant" }))
          )
        );
        leadSent = true;
      }

      if (done) {
        controller.enqueue(
          encoder.encode(
            sse(openaiChunk(completionId, requestedModel, {}, finishReason))
          )
        );
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
        return;
      }

      buffer += decoder.decode(value, { stream: true });
      // Anthropic SSE events are separated by a blank line.
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const block of events) {
        const dataLine = block
          .split("\n")
          .find((line) => line.startsWith("data:"));
        if (!dataLine) continue;
        const json = dataLine.slice(5).trim();
        if (!json) continue;
        let event;
        try {
          event = JSON.parse(json);
        } catch {
          continue;
        }
        if (
          event.type === "content_block_delta" &&
          event.delta &&
          event.delta.type === "text_delta"
        ) {
          controller.enqueue(
            encoder.encode(
              sse(
                openaiChunk(completionId, requestedModel, {
                  content: event.delta.text,
                })
              )
            )
          );
        } else if (
          event.type === "message_delta" &&
          event.delta &&
          event.delta.stop_reason
        ) {
          finishReason = FINISH_REASON_MAP[event.delta.stop_reason] || "stop";
        }
      }
    },
    cancel() {
      reader.cancel();
    },
  });
}

async function handleChatCompletions(request, env) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return errorResponse(400, "Request body is not valid JSON.");
  }
  if (!payload || !Array.isArray(payload.messages) || !payload.messages.length) {
    return errorResponse(400, "'messages' is required.");
  }

  const apiKey = resolveApiKey(request, env);
  if (!apiKey) {
    return errorResponse(
      401,
      "No API key provided. Set the ANTHROPIC_API_KEY secret or send an " +
        "'Authorization: Bearer <anthropic-key>' header.",
      "authentication_error"
    );
  }

  const anthropicRequest = buildAnthropicRequest(payload);
  const requestedModel = payload.model || anthropicRequest.model;
  const stream = Boolean(payload.stream);

  const upstream = await fetch(ANTHROPIC_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": ANTHROPIC_VERSION,
    },
    body: JSON.stringify({ ...anthropicRequest, stream }),
  });

  if (!upstream.ok) {
    const detail = await upstream.text();
    return errorResponse(upstream.status, detail || "Anthropic API error", "api_error");
  }

  if (stream) {
    const completionId = newCompletionId();
    return new Response(
      transformStream(upstream.body, completionId, requestedModel),
      {
        headers: {
          "content-type": "text/event-stream",
          "cache-control": "no-cache",
          ...corsHeaders(),
        },
      }
    );
  }

  const message = await upstream.json();
  return jsonResponse(anthropicToOpenAIResponse(message, requestedModel));
}

function handleListModels() {
  const created = Math.floor(Date.now() / 1000);
  return jsonResponse({
    object: "list",
    data: ADVERTISED_MODELS.map((id) => ({
      id,
      object: "model",
      created,
      owned_by: "anthropic",
    })),
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/") {
      return jsonResponse({ status: "ok", service: "claude-to-chatgpt" });
    }
    if (request.method === "GET" && url.pathname === "/v1/models") {
      return handleListModels();
    }
    if (request.method === "POST" && url.pathname === "/v1/chat/completions") {
      return handleChatCompletions(request, env);
    }

    return errorResponse(404, `No route for ${request.method} ${url.pathname}`, "not_found_error");
  },
};
