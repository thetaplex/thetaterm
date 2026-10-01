# thetaterm

Supercharge your terminal with AI: describe what you want, get a shell command
that is correct for *your* system, confirm, run.

## Why

You shouldn't have to remember whether it's `tar -xzf` or `tar -zxvf`, or
which `sed -i` your Mac accepts. Say what you want in plain words and **thetaterm**
writes the command for you. It's right for *your* system, because **thetaterm**
checks whether your tools are GNU, BSD or BusyBox and shows the model the
installed tool's `man` page. It runs on a small model on your own machine, so
there is no subscription and no per-token bill. And it stays private: you're
not pasting commands full of file paths, hostnames and project names into a
chat website to work out what they do. With the default local model, your
requests never leave your computer.

## Requirements

- macOS or Linux
- [uv](https://docs.astral.sh/uv/getting-started/installation/). It installs
  Python 3.13 or later for you if needed.
- A model served over an OpenAI-compatible API. The default is `gemma4:e4b` on
  [Ollama](https://ollama.com/download): `ollama pull gemma4:e4b`

## Install

```bash
uv tool install thetaterm
```

## Quickstart

```bash
tterm -q "list files in this directory, largest first"
```

```
$ ls -lS .
Run it? [Y/n]:
```

New to it? Follow the [tutorial](https://github.com/thetaplex/thetaterm/blob/main/docs/tutorials/first-command.md).

## Usage

```bash
tterm                                  # interactive
tterm -q "find files modified in the last 2 days"
tterm -m qwen2.5-coder:3b -q "replace foo with bar in notes.txt in place"   # another model
tterm -y -q "show git status"          # run without confirming
tterm --think -q "show the date 30 days from now"   # model reasons first, about 2x slower
```

> **Warning:** `-y` runs whatever the model writes, unreviewed. In interactive
> mode that applies to every line you type. Commands pass a syntax check, not a
> safety check.

Commands that look like they reach outside the current directory (absolute,
`~` or `..` paths, variables such as `$HOME`, `cd` home or back, or `sudo`) are shown in red and always ask first,
defaulting to no, even with `-y`. This is a pattern match, not a sandbox. See
the [safety model](https://github.com/thetaplex/thetaterm/blob/main/docs/explanation/safety.md).

Settings (`THETATERM_MODEL`, `THETATERM_BASE_URL`, `THETATERM_API_KEY`) are
read from the environment or `~/.config/thetaterm/.env`, never from a `.env`
in the current directory. See the
[command-line reference](https://github.com/thetaplex/thetaterm/blob/main/docs/reference/cli.md) and
[how to use another model server](https://github.com/thetaplex/thetaterm/blob/main/docs/how-to/use-another-model-server.md).

## Documentation

- [Documentation index](https://github.com/thetaplex/thetaterm/blob/main/docs/README.md): tutorial, how-to guides, reference,
  explanation and design decisions
- [Contributing](https://github.com/thetaplex/thetaterm/blob/main/CONTRIBUTING.md): development setup, needs
  [just](https://just.systems/man/en/packages.html)
- [Security policy](https://github.com/thetaplex/thetaterm/blob/main/SECURITY.md)
- [Changelog](https://github.com/thetaplex/thetaterm/blob/main/CHANGELOG.md)

## License

[Apache-2.0](https://github.com/thetaplex/thetaterm/blob/main/LICENSE)
