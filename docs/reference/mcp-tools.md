# MCP tools reference

`tterm-mcp` is a stdio MCP server, installed with `thetaterm[mcp]`. It offers
these tools. All are marked read-only, and none runs a command. Setup is in
[How to use thetaterm from an AI agent](../how-to/use-from-an-agent.md).

| Tool | Parameters | Returns | Needs a model |
|---|---|---|---|
| `system_info` | none | the system description, as text | no |
| `docs` | `program`, `task` | the reference for `program`, as text | no |
| `check` | `command` | `{"problem": …, "outside": …}` | no |
| `suggest_command` | `task`, `think` (default `false`) | `{"command": …, "outside": …}` | yes |

## `system_info`

The [system description](glossary.md): OS, userland and shell, for example
`macOS 26.6.2, BSD userland, zsh shell`.

## `docs`

The [reference](glossary.md) for `program`: thetaterm's note on it, if there is
one, then the parts of its installed man page that best match `task`, up to
3,500 characters. It reads the man page and never runs the program.

**Errors:** `PROGRAM: not an installed program` when `program` isn't the name
of a program on `PATH`. Paths and names that start with `-` are refused too.
`PROGRAM: no man page or note` when the program is installed but has neither.

## `check`

Checks `command` without running it.

- `problem`: why the command would fail, such as a syntax error or
  `NAME: command not found`. `null` if none was found.
- `outside`: why the command reaches outside the current directory, such as
  `absolute path /tmp/x`. `null` if none was found. The reasons are listed in
  [Messages](messages.md).

Two `null`s mean the command would start and stays in the current directory
as far as its words show. They don't mean it is safe. See the
[safety model](../explanation/safety.md).

## `suggest_command`

Writes one command for `task` the way `tterm -q` does, with the model set by
`THETATERM_MODEL` and `THETATERM_BASE_URL`. `think` is `--think`. Takes from a
few seconds to a minute.

- `command`: the command. It has passed `check`'s `problem` test.
- `outside`: as in `check`.

**Errors:** the messages `tterm -q` prints when no command can be made, such as
`cannot reach …`, `404 … model not found` and `no working command found …`.
See [Messages](messages.md).
