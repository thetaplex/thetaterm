# 10. Brew skills from failures with UpSkill

Date: 2026-11-21

## Status

Accepted

Supersedes [ADR 0006](0006-put-a-short-note-before-the-man-page-excerpt.md)

## Context

Notes (ADR 0006) fixed failures the man page excerpt caused, such as `awk`
splitting fields on spaces and `du -b` being GNU only. But someone wrote each
note by hand, one program at a time, after finding the failure (ADR 0009).
Eight programs had a note. Every other failure stayed until someone noticed
it and wrote one.

Failures happen in two places: in `just eval`, and when people use `tterm`,
where nobody sees them.

Options considered:

- **Keep writing notes by hand.** They work, but only for failures someone
  finds, and only as fast as someone writes them.
- **A larger or thinking model.** It is slower, and thetaterm is meant to work
  with small local models (ADR 0009).
- **Fine-tune the small model.** It needs a training pipeline and new weights
  for each model, and the result can't be read or reviewed in a PR.
- **[UpSkill](https://github.com/HKUDS/UpSkill): a large teacher model writes
  a `SKILL.md` for each failure, and the small student model must then pass
  with it.**

## Decision

thetaterm loads `SKILL.md` files from `thetaterm/skills/` and
`~/.config/thetaterm/skills/`. It picks up to two skills whose trigger keywords
match the request, also scoring the programs the model chose, and adds them in
`<skill>` tags after the man page excerpts, up to 1,800 characters in all.

`just upskill` runs the Ralph Loop on an eval file. For each query the student
fails, the teacher writes a skill. The student runs the query again with it.
If the student fails, the teacher revises the skill, for a few rounds. The
skill is saved only if the student then passes and no query in
`regression.yaml` that the skill matches starts to fail.

Failures from real use go back into the same loop. With `--log-failures` or
`THETATERM_LOG_FAILURES=1`, `tterm` appends commands that you decline, that
fail, or that you mark with `?bad` to `~/.config/thetaterm/failures.jsonl`.
The log stays on this machine. `just upskill-failures` shows each entry so you
can edit out private details before it goes to the teacher. With `--yes`, it
skips that review, and only a local teacher is allowed.

The notes are deleted.

## Consequences

- Fixing a failure takes a teacher run, not someone writing a note.
- Skills may contain example commands. ADR 0006 banned them in notes, because
  the model copies them. A skill is kept only if the student passes with it
  and no matching regression query starts to fail, which checks whether the
  copy is right.
- Skills are brewed from the eval queries themselves. That is intended: it is
  an ongoing loop, not a one-off fit. It means the eval pass rate on those
  queries overstates how well thetaterm does on new requests. Logged real
  failures are requests no skill was brewed from.
- The regression check misses a skill that has programs but no trigger
  keywords. It matches without the chosen programs, so no regression query
  matches that skill.
- The awk, curl, du, grep, ping, ps, sed and wc notes are gone. Until the loop
  brews skills for those programs, the failures the notes fixed can come back.
- Agents using thetaterm over MCP (ADR 0008) get no skills. The `docs` tool
  returns only the man page excerpt.
- A cloud teacher sees the queries and commands it is asked to fix.
- Skills are matched by keyword, so a skill can miss a request that is worded
  differently.
