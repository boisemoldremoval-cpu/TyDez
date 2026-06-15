# Free LLM API Resources

A quick reference of providers that offer **free** or **trial-credit** access to
large language model APIs. Useful for this project when generating or polishing
script copy, scene descriptions, voiceover lines, and brand messaging without
paying for inference.

> Source & full details: [cheahjs/free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources)
>
> Please don't abuse these services — if they get hammered, the free tiers
> disappear for everyone. Rate limits and offerings change often; always check
> the upstream list and each provider's pricing page before relying on one.

## Always-free tiers (no card / no spend required)

| Provider | What you get | Notes |
| --- | --- | --- |
| **OpenRouter** | ~50 requests/day across a pool of free models | Single API, many models behind one key; OpenAI-compatible. |
| **Google AI Studio** | Gemini & Gemma models | Per-model rate limits; generous free quota. |
| **Groq** | Llama, Qwen, and more | Very fast inference; per-model daily/limited quotas. |
| **Cerebras** | GPT-OSS, Llama 3.1 variants | Fast inference; rate-limited free tier. |
| **Mistral** | Open + proprietary models | Requires phone verification. |
| **HuggingFace Inference** | ~$0.10/month in serverless credits | Access to many serverless models. |
| **Cohere** | Command models | Monthly request quotas. |
| **Cloudflare Workers AI** | 10,000 "neurons"/day | Runs at the edge; many open models. |
| **GitHub Models** | Tier-dependent limits | Free for GitHub users; limits scale with plan. |

## Trial-credit providers ($1–$30 one-time)

These give a block of starting credit rather than a recurring free tier:

- **Fireworks**
- **Baseten**
- **Nebius**
- **Novita**
- **AI21**
- **Upstage**
- **NLP Cloud**
- **Modal**

## How this helps TyDez

This repo renders promo/story videos from Python (see `make_promo.py`,
`veo_story.py`, the various `make_*.py` scripts). A free LLM API can help with
the *writing* side of that pipeline:

- Drafting or rewriting ad copy, hooks, and calls-to-action in `CONFIG` blocks.
- Generating scene beats / shot lists for the story scripts (`STORY_5MIN.md`,
  `FLOW_GUIDE*.md`).
- Producing voiceover line variations to feed into `voices.py`.

**Picking one:** for quick scriptwriting, **Groq** or **Google AI Studio** are
the easiest starting points (fast, generous free quota, OpenAI- or
Gemini-compatible SDKs). **OpenRouter** is handy if you want to swap between many
models behind a single key.

> Note: these are **text/chat** LLM providers. They do **not** cover image or
> video generation — for that, this project already uses dedicated tooling
> (e.g. `veo_gen.py`).
</content>
</invoke>
