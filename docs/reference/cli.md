# Command-line reference

## Synopsis

```
tterm [-q QUERY] [-m MODEL] [-y] [--think]
tterm --help
```

With `-q`, thetaterm handles one request and exits. Without it, thetaterm starts
interactive mode.

## Options

| Option | Argument | Default | Description |
|---|---|---|---|
| `-q`, `--query` | text | none | The request. Without it, interactive mode starts. |
| `-m`, `--model` | name | `gemma4:e4b` | Model to use. Overrides `THETATERM_MODEL`. |
| `-y`, `--yes` | | off | Run the command without asking. See the warning below. |
| `--think` | | off | Let the model reason before answering. About twice as slow. Skips the man page lookup. |
| `--install-completion` | | | Install tab completion for your shell. |
| `--show-completion` | | | Print the completion script. |
| `--help` | | | Print usage and exit. |

**Warning:** `-y` runs whatever the model writes, unreviewed. In interactive
mode it applies to every request. Commands only pass a syntax check before
running. Commands that reach outside the current directory still ask, even with
`-y`. See [Safety model](../explanation/safety.md).

## Interactive mode

thetaterm prints the model and the detected system, then shows a `>` prompt.
Each line you type is one request. Empty lines are ignored. Ctrl-D or Ctrl-C at
the `>` prompt exits. Errors are printed and the session carries on.

## Confirmation prompt

| Prompt | When | Enter means |
|---|---|---|
| `Run it? [Y/n]` | normal command | yes |
| `Run it? [y/N]` | command reaches outside the current directory (shown in red, with the reason) | no |

The command runs in your login shell (`$SHELL`) if it's `sh`, `bash`, `zsh`,
`ksh` or `dash`, otherwise in `bash`, or `/bin/sh` if bash isn't installed. It
runs in the current directory. See
[Which shell](../explanation/how-it-works.md#which-shell). Its output goes straight to your terminal.

## Exit status

| Status | Meaning |
|---|---|
| the command's own status | `-q`: the command ran |
| `0` | `-q`: you declined to run it. Interactive: you pressed Ctrl-D or Ctrl-C at the `>` prompt |
| `1` | `-q`: no command was produced (server unreachable, server error, or no command passed the checks) |
| `1` | you pressed Ctrl-D or Ctrl-C at `Run it?`. thetaterm prints `Aborted.` and exits, in interactive mode too |
| `2` | invalid option or argument |
| `130` | `-q`: you pressed Ctrl-C while the model was thinking or the command was running. Interactive: the same stops that request and returns to the `>` prompt |

## Settings

| Variable | Default | Description |
|---|---|---|
| `THETATERM_MODEL` | `gemma4:e4b` | Model name. `-m` overrides it. |
| `THETATERM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint. `/chat/completions` is appended. |
| `THETATERM_API_KEY` | none | Sent as `Authorization: Bearer <key>`. Only set it for servers that need one. |
| `XDG_CONFIG_HOME` | `~/.config` | Where to look for the config directory. |
| `SHELL` | set by your system | Shell commands are written for and run in, if it's `sh`, `bash`, `zsh`, `ksh` or `dash`. |

Settings are read from, in priority order:

1. the command line (`-m` only)
2. environment variables
3. `$XDG_CONFIG_HOME/thetaterm/.env`, or `~/.config/thetaterm/.env`

A `.env` file in the current directory is **not** read. See
[ADR 0003](../adr/0003-read-config-only-from-the-user-config-dir.md).

The config file uses one `NAME=value` per line, with `#` comments. The
repository's [`.env.example`](../../.env.example) lists every setting.

## Limits

| Limit | Value |
|---|---|
| Time allowed per model request | 300 s |
| Attempts to produce a command that passes the checks | 3 |
| Man page excerpt size | 3,500 characters |
| Time allowed for a `man` lookup | 10 s |
