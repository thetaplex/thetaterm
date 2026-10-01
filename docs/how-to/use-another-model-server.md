# How to use another model server

thetaterm works with any server that offers the OpenAI-compatible
`/chat/completions` endpoint. This page shows how to point it at one.

## Set the endpoint and model

1. Find your server's base URL. It usually ends in `/v1`. Common defaults:

   | Server | Base URL |
   |---|---|
   | Ollama | `http://localhost:11434/v1` (thetaterm's default) |
   | llama.cpp (`llama-server`) | `http://localhost:8080/v1` |
   | LM Studio | `http://localhost:1234/v1` |
   | vLLM | `http://localhost:8000/v1` |

2. Put the settings in your config file, `~/.config/thetaterm/.env`:

   ```bash
   THETATERM_BASE_URL=http://localhost:8080/v1
   THETATERM_MODEL=your-model-name
   ```

   Use the model name exactly as your server lists it.

3. Run a test request:

   ```bash
   tterm -q "show the current date"
   ```

To try a server once without changing the file, set the variables on the
command line. They take priority over the file:

```bash
THETATERM_BASE_URL=http://localhost:8080/v1 tterm -m your-model-name -q "show the current date"
```

## Use a hosted API that needs a key

**Warning:** with a hosted API, your request, a description of your system and
excerpts from your man pages are sent to that provider.

1. Add the endpoint, model and key to `~/.config/thetaterm/.env`:

   ```bash
   THETATERM_BASE_URL=https://api.example.com/v1
   THETATERM_MODEL=provider-model-name
   THETATERM_API_KEY=your-key
   ```

2. Make the file readable only by you:

   ```bash
   chmod 600 ~/.config/thetaterm/.env
   ```

Use an `https://` URL. If you set a key with a plain `http://` URL that isn't
`localhost`, thetaterm warns that the key is sent unencrypted.

## If it doesn't work

See [Messages](../reference/messages.md) for `cannot reach …` and HTTP errors
such as `404 … model not found`.
