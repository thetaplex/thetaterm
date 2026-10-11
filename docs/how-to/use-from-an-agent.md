# How to use thetaterm from an AI agent

thetaterm can run as an MCP server, so agents such as Claude Code can ask it
about this system's tools before they write a command. This page shows how to
connect one. The tools are described in the [MCP tools reference](../reference/mcp-tools.md).

## Install the server

```bash
uv tool install 'thetaterm[mcp]'
```

This installs `tterm-mcp` alongside `tterm`. If you already installed
thetaterm, the same command adds the server.

## Connect your agent

For Claude Code:

```bash
claude mcp add thetaterm -- tterm-mcp
```

For other clients, add a stdio server to their MCP configuration. Most accept
this shape:

```json
{
  "mcpServers": {
    "thetaterm": { "command": "tterm-mcp" }
  }
}
```

If the client can't find `tterm-mcp`, give the full path that
`command -v tterm-mcp` prints.

## Set the model for `suggest_command`

Only `suggest_command` uses a model. MCP clients start servers with few
environment variables, so put settings in `~/.config/thetaterm/.env` rather
than your shell profile:

```bash
THETATERM_MODEL=gemma4:e4b
```

The other settings work as in
[How to use another model server](use-another-model-server.md). The other
tools work without any model server.

## Check that it works

Ask your agent something that depends on your system, for example "using the
thetaterm tools, how do I edit a file in place with sed here?" It should call
`docs` and answer with the form your `sed` accepts.

## If it doesn't work

- `install the MCP extra` in the client's log: the server was installed
  without the `mcp` extra. Run the install command above.
- `suggest_command` fails with `cannot reach …` or `model … not found`: see
  [Messages](../reference/messages.md). The other tools keep working.
