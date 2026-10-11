# 8. Offer thetaterm's system knowledge to agents over MCP, without running anything

Date: 2026-10-11

## Status

Accepted

## Context

Coding agents such as Claude Code write shell commands that are often wrong for
the machine they run on: GNU options on macOS, options BusyBox lacks. thetaterm
already knows which userland the system has, reads the installed program's man
page with our notes, and checks a command before it runs. Other agents could
use that if it were reachable over the Model Context Protocol (MCP).

Options considered:

- **What to offer:**
  - The system description, docs and checks only. They need no model and
    answer in milliseconds.
  - Those, plus command suggestions from thetaterm's model. A capable agent
    usually writes better commands itself than a small local model does, but
    small local agents and unfamiliar systems gain from it.
  - Those, plus running the command. ADR 0002's guard assumes a person reads
    each command, and an agent already has its own shell and permission
    prompts, so a second way to run commands would only weaken them.
- **How to speak MCP:**
  - JSON-RPC over stdio with the standard library, as ADR 0004 did for model
    calls. The protocol has had several revisions since 2024, so every client
    incompatibility would be ours to fix, in code contributors haven't seen
    before.
  - The official `mcp` SDK. It follows the spec and builds tool schemas from
    type hints, but adds about 30 packages, such as pydantic and starlette.
- **Where it lives:**
  - CLI subcommands an agent calls through its shell. They need no protocol,
    but clients without a shell can't use them and agents don't find them.
  - A `tterm mcp` subcommand. It would turn the single `tterm` command into a
    group and change how `tterm -q` parses.
  - A separate `tterm-mcp` program.

## Decision

Ship `tterm-mcp`, a stdio MCP server on the official SDK, installed only with
the optional `mcp` extra. It offers four tools, all marked read-only:
`system_info`, `docs`, `check` and `suggest_command`. No tool runs a command.
`suggest_command` returns the guard's reason along with the command, and its
description tells agents it is slow and that `docs` and `check` may serve them
better.

## Consequences

- An agent can get the right options for this system's tools without
  thetaterm's model, and use thetaterm's model if it wants a command written.
- `uv tool install thetaterm` keeps its three dependencies. MCP users install
  `thetaterm[mcp]`.
- SDK upgrades go through `uv.lock` and Dependabot, like every other dependency.
- `docs` passes an agent's text to `man`, so it accepts only the names of
  installed programs, never options or paths.
- The guard's verdict is advice to the agent. Whether a command runs depends
  on the agent's own permission prompts, not on thetaterm.
- MCP clients start servers with few environment variables, so settings
  belong in `~/.config/thetaterm/.env` or the client's `env` setting.
