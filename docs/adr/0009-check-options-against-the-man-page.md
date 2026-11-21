# 9. Check a command's options against the man page

Date: 2026-11-07

## Status

Accepted

Amends [ADR 0001](0001-read-docs-from-the-installed-system.md)

## Context

Asked to "find me the largest file", `gemma4:e4b-mlx` on macOS wrote
`du -b` in 6 of 10 tries. `-b` is GNU only. BSD du's man page was in the
prompt, without `-b`, and the model used it anyway. The command checks passed
it, since the syntax was valid and `du` was installed, so the user saw it fail
once for each batch `xargs` ran.

Small models copy the GNU options they were trained on, whatever the
reference says. A note (ADR 0006) for du cut `-b` to 2 of 10 tries, but notes
are written one program at a time, after a failure is found.

Options considered:

- **More notes.** They help, but only for programs someone has written one
  for.
- **A larger or thinking model.** It works out the options itself, but
  that's slower, and thetaterm is meant to work with small local models.
- **Run the command, or `<program> --help`, to see whether it fails.** It runs
  code before the user agrees (ADR 0005).
- **Ask for several commands and keep the first that passes.** It takes 3 to 5
  times as long on a local model, and without an option check nothing tells
  the bad ones apart.
- **Check each program's short options against its installed man page.**

## Decision

The command check reads the man page of each program the command runs,
including those run by `xargs` and `find -exec`, and rejects a short option
the page doesn't list. The model is told
`du has no -b option on this system`, and asked again. find's tests, such as
`-printf`, are checked against find's page in the same way.

The check reads options as BSD getopt does. They end at the first operand,
`--` or `-`. It leans towards accepting a command:

- An option counts as listed if the page names it anywhere. BSD grep's
  SYNOPSIS leaves out `-r`, which the text describes.
- A word the page spells out, such as `-version` or `-O2`, is accepted whole.
- Long options, counts such as `head -5`, and programs without a man page are
  not checked. Neither are shell builtins, whose man page, if any, belongs to
  another program.

## Consequences

- `du -b`, `grep -P`, `stat -c` and `find -printf` are caught on macOS
  without a note. With the check, no command in 10 tries used a missing
  option. A test set of 70 working macOS commands had no false rejections.
- GNU-only long options such as `ls --sort` still get through.
- A program whose man page belongs to another version of it, such as GNU du
  from Homebrew first in `PATH` with BSD's man page, may be turned away for an
  option it has.
- An option that exists but does the wrong thing, such as `sort -h` on
  `ls -l` output, still gets through. Notes and evals cover that.
- Each check reads a man page per program, about 70 ms per command. Pages are
  read once per session.
