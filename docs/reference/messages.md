# Messages

Messages Thetaterm prints, what they mean, and what to do. `…` stands for text
that varies.

## Errors

These stop the request. In one-shot mode Thetaterm exits with status `1`.

### `cannot reach <url>: …`

The model server didn't answer. For example,
`cannot reach http://localhost:11434/v1/chat/completions: [Errno 61] Connection refused`.

- Start the server. For Ollama, open the app or run `ollama serve`.
- Check `THETATERM_BASE_URL`, including the port and the `/v1` path.
- If the reason is `timed out`, the model took longer than 300 s. Try a
  smaller model, or drop `--think`.

### `<url>: <status> …`

The server answered with an HTTP error. The text after the status is the
server's own message.

| Status | Usual cause | Action |
|---|---|---|
| `404` with `model … not found` | the model isn't on the server | `ollama pull <model>`, or fix the name in `-m` or `THETATERM_MODEL` |
| `401` or `403` | missing or wrong API key | set `THETATERM_API_KEY` |
| `400` | the server rejected the request | check that the server supports `/chat/completions` |
| `5xx` | the server failed | check the server's log |

### ``no working command found (last: `<command>`: <reason>)``

The model's answer failed the checks three times. The reason is the last
failure:

| Reason | Meaning |
|---|---|
| `<name>: command not found` | the command uses a program that isn't installed |
| a shell syntax error | the command isn't valid shell |
| `No closing quotation` | the quotes don't match |
| `empty command` | the model gave no command |

Try rewording the request to be more specific, naming the tool you want, or
use a larger model.

## Warnings

### `leaves the current directory: <reason>`

The proposed command may read or change files outside the current directory.
It's shown in red, and the prompt defaults to no, even with `-y`.

| Reason | Triggered by |
|---|---|
| `runs as root` | `sudo` |
| `uses $HOME` | `$HOME` or `${HOME}` |
| `home path …` | a path starting with `~` |
| `absolute path …` | a path starting with `/`, except `/dev/…` |
| `parent path …` | a path containing `..` |

Read the command before you answer. Declining is safe: nothing runs.

### `warning: API key sent unencrypted to <url>`

`THETATERM_API_KEY` is set and the endpoint uses `http://` on a host other than
`localhost`, `127.0.0.1` or `::1`. Anyone on the network path can read the key.
Switch to an `https://` URL, or unset the key if the server doesn't need one.
