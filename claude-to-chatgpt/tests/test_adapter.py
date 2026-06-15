"""Unit tests for the pure translation layer (no network required)."""

from claude_to_chatgpt.adapter import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    anthropic_to_openai_response,
    build_anthropic_request,
    convert_messages,
    map_model,
)


def test_map_model_passthrough_for_claude_ids():
    assert map_model("claude-sonnet-4-6") == "claude-sonnet-4-6"


def test_map_model_known_openai_names():
    assert map_model("gpt-4") == "claude-opus-4-8"
    assert map_model("gpt-4o") == "claude-opus-4-8"
    assert map_model("gpt-3.5-turbo") == "claude-haiku-4-5"
    assert map_model("gpt-4o-mini") == "claude-haiku-4-5"


def test_map_model_heuristics_and_default():
    assert map_model("some-sonnet-thing") == "claude-sonnet-4-6"
    assert map_model("mystery-model") == DEFAULT_MODEL
    assert map_model(None) == DEFAULT_MODEL


def test_convert_messages_extracts_system():
    system, messages = convert_messages(
        [
            {"role": "system", "content": "be terse"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
    )
    assert system == "be terse"
    assert messages == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_convert_messages_joins_multiple_system_messages():
    system, _ = convert_messages(
        [
            {"role": "system", "content": "rule one"},
            {"role": "developer", "content": "rule two"},
            {"role": "user", "content": "hi"},
        ]
    )
    assert system == "rule one\n\nrule two"


def test_convert_messages_vision_content():
    _, messages = convert_messages(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "what is this?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/cat.png"},
                    },
                ],
            }
        ]
    )
    assert messages[0]["content"] == [
        {"type": "text", "text": "what is this?"},
        {
            "type": "image",
            "source": {"type": "url", "url": "https://example.com/cat.png"},
        },
    ]


def test_build_request_drops_sampling_params_for_opus_48():
    req = build_anthropic_request(
        {
            "model": "gpt-4",  # -> claude-opus-4-8
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 0.7,
            "top_p": 0.9,
        }
    )
    assert req["model"] == "claude-opus-4-8"
    assert "temperature" not in req
    assert "top_p" not in req
    assert req["max_tokens"] == DEFAULT_MAX_TOKENS


def test_build_request_keeps_and_clamps_temperature_for_sonnet():
    req = build_anthropic_request(
        {
            "model": "claude-sonnet-4-6",
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 1.8,  # OpenAI range; must clamp to <= 1.0
            "top_p": 0.5,
        }
    )
    assert req["temperature"] == 1.0
    # Never send both temperature and top_p to Claude 4+.
    assert "top_p" not in req


def test_build_request_stop_sequences():
    req = build_anthropic_request(
        {
            "model": "claude-sonnet-4-6",
            "messages": [{"role": "user", "content": "hi"}],
            "stop": "STOP",
        }
    )
    assert req["stop_sequences"] == ["STOP"]


def test_anthropic_to_openai_response_shape():
    message = {
        "id": "msg_123",
        "model": "claude-opus-4-8",
        "content": [{"type": "text", "text": "hello world"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }
    result = anthropic_to_openai_response(message, "gpt-4")
    assert result["object"] == "chat.completion"
    assert result["model"] == "gpt-4"
    assert result["choices"][0]["message"]["content"] == "hello world"
    assert result["choices"][0]["finish_reason"] == "stop"
    assert result["usage"] == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }


def test_finish_reason_max_tokens_maps_to_length():
    message = {
        "id": "msg_1",
        "content": [{"type": "text", "text": "x"}],
        "stop_reason": "max_tokens",
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    result = anthropic_to_openai_response(message, "gpt-4")
    assert result["choices"][0]["finish_reason"] == "length"
