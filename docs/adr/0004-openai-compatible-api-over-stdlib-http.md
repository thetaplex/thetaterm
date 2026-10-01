# 4. Talk to models over the OpenAI-compatible API with the standard library

Date: 2026-09-29

## Status

Accepted

## Context

Thetaterm started with the Ollama client library. Users also run llama.cpp,
LM Studio and vLLM, or use hosted APIs. Most of these offer the
OpenAI-compatible `/chat/completions` endpoint.

Options considered:

- **One client library per server.** More dependencies, and more code paths to
  test.
- **The `openai` Python package.** One dependency, but a large one, for a
  single request type.
- **An abstraction library over many providers.** Heavy, and changes often.
- **A direct HTTP request to `<base_url>/chat/completions`** with `urllib`.

## Decision

Send one JSON request per model call with `urllib.request` to
`THETATERM_BASE_URL` + `/chat/completions`, with an optional bearer token from
`THETATERM_API_KEY`. Ollama on `localhost` remains the default.

## Consequences

- Any OpenAI-compatible server works, and model calls add no dependencies.
- Thetaterm handles only what it uses: non-streaming chat completions, with
  `temperature`, `max_tokens` and `reasoning_effort`. When a server rejects
  `reasoning_effort`, Thetaterm drops it and retries.
- Servers that only offer a different API, or features such as streaming and
  tool calls, need a proxy or a new decision.
