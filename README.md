# Thetaterm

Supercharge your terminal with AI: describe what you want, get a shell command
that is correct for *your* system, confirm, run.

## Why

Small local models know what `find` or `sed` does, but not which options your
copy has. GNU, BSD and BusyBox tools differ, so a command that's right on Linux
can fail on a Mac. Thetaterm detects your OS and whether your tools are GNU,
BSD or BusyBox, and gives the model the installed tool's `man` page. Every
command is checked before you're asked to run it. It works with any model
served over an OpenAI-compatible API, including ones on your own machine.

## Requirements

- macOS or Linux
- [uv](https://docs.astral.sh/uv/getting-started/installation/). It installs
  Python 3.13 or later for you if needed.
- A model served over an OpenAI-compatible API. The default is `gemma4:e4b` on
  [Ollama](https://ollama.com/download): `ollama pull gemma4:e4b`

## Install

```bash
uv tool install git+https://github.com/thetaplex/thetaterm
```

## Quickstart

```bash
tterm -q "list files in this directory, largest first"
```

```
$ ls -lS .
Run it? [Y/n]:
```

New to it? Follow the [tutorial](docs/tutorials/first-command.md).

## Usage

```bash
tterm                                  # interactive
tterm -q "find files modified in the last 2 days"
tterm -m qwen2.5-coder:3b -q "replace foo with bar in notes.txt in place"   # another model
tterm -y -q "show git status"          # run without confirming
tterm --think -q "show the date 30 days from now"   # model reasons first, about 2x slower
```

> [!WARNING]
> `-y` runs whatever the model writes, unreviewed. In interactive mode that
> applies to every line you type. Commands pass a syntax check, not a safety
> check.

Commands that look like they reach outside the current directory (absolute,
`~` or `..` paths, variables such as `$HOME`, `cd` home or back, or `sudo`) are shown in red and always ask first,
defaulting to no, even with `-y`. This is a pattern match, not a sandbox. See
the [safety model](docs/explanation/safety.md).

Settings (`THETATERM_MODEL`, `THETATERM_BASE_URL`, `THETATERM_API_KEY`) are
read from the environment or `~/.config/thetaterm/.env`, never from a `.env`
in the current directory. See the
[command-line reference](docs/reference/cli.md) and
[how to use another model server](docs/how-to/use-another-model-server.md).

## Documentation

- [Documentation index](docs/README.md): tutorial, how-to guides, reference,
  explanation and design decisions
- [Contributing](CONTRIBUTING.md): development setup, needs
  [just](https://just.systems/man/en/packages.html)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

[Apache-2.0](LICENSE)
