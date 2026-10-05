# 7. Put two programs' man pages in the prompt

Date: 2026-10-05

## Status

Accepted

Amends [ADR 0001](0001-read-docs-from-the-installed-system.md)

## Context

ADR 0001 puts the man page of one program in the prompt: the first installed
program the model suggests. When that program is the wrong one, the model has
no reference for the right one. Asked to "show the md5 checksum of image.iso",
`gemma4:e4b-mlx` suggested `shasum` first and `md5` second on every run. With
only the `shasum` page in the prompt, it wrote `shasum -a 1 image.iso`, a SHA-1
checksum.

Options considered, each run on the 50 queries in `tests.yaml` with
`gemma4:e4b-mlx` and judged by `anthropic/claude-opus-5`, checked by running
the commands it failed:

- **One program**, as now: 43 of 50.
- **Two programs**, best last: 46 of 50.
- **Three programs**, best last: 45 of 50.
- **Two or three programs, best first.** Earlier runs, checked by the
  assertions only, did worse than the same number best last: the model
  followed the page nearest the task.
- **Ask for more suggestions and keep the first two installed.** Helps only
  when a suggestion isn't installed. `shasum` is installed, so it doesn't help
  in the case that prompted this.

## Decision

The model suggests up to three programs, and thetaterm keeps the first two
`which` finds. Each gets its own reference, note and man page excerpt, up to
3,500 characters. The references go in the prompt in reverse order, so the
best program's comes last, just before the rules and the task.

## Consequences

- When the model ranks the wrong program first, the right one's man page can
  still reach the prompt: md5, `tar -tf` and `vm_stat` were fixed this way.
- The prompt is up to twice as long, and a query took about twice as long in
  the evals.
- A second page can also draw the model to a program it didn't need: two
  programs wrote `du -s -d 1 .`, which BSD `du` rejects, where one wrote
  `du -s *`.
- The gaps are a few queries in one run each. Another model, or more runs,
  could change the order.
