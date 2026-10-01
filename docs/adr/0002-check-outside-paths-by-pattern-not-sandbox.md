# 2. Guard paths outside the current directory with a pattern match, not a sandbox

Date: 2026-09-29

## Status

Accepted

## Context

A model sometimes writes a command that reaches further than the request
meant, such as an absolute path where a relative one was intended, `~` instead
of `.`, or an unneeded `sudo`. Users approving many commands, or running with
`-y`, may not notice.

Options considered:

- **Sandbox the command** (containers, `sandbox-exec`, namespaces). This is
  strong, but platform-specific, heavy to set up, and it breaks the many
  legitimate commands that read outside the directory.
- **Parse the command fully and resolve every path.** Shell expansion makes
  this unsound without running the command.
- **Match the command's words against patterns** for `sudo`, `$HOME`, `~`,
  absolute paths (except `/dev/`) and `..`.
- **Do nothing**, and rely on the confirmation prompt.

## Decision

Match words. A command that matches is shown in red with the reason, the
prompt defaults to no, and it always asks, even with `-y`.

## Consequences

- It catches the model's honest mistakes at almost no cost, on every platform.
- It doesn't catch commands built to hide their target, such as a path
  assembled with `$(…)`. The README, the safety page and `SECURITY.md` say so,
  and that case is out of scope for security reports.
- Some harmless commands, such as `ls /tmp`, ask with a default of no.
- If Thetaterm ever runs commands without a person reading them, this guard
  isn't enough, and the decision needs revisiting.
