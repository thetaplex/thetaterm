---
name: skill_git_rebase_autosquash
description: Rebase and fold fixup!/squash! commits with --autosquash; fetch first when rebasing onto origin/main.
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [fixup, squash, autosquash, fold commits, fold the fixup, latest main, from origin]
  programs: [git]
---

# Domain Knowledge
- `git commit --fixup=<sha>` makes `fixup! <msg>` commits. Plain `git rebase -i` does NOT fold them.
- `--autosquash` moves each `fixup!`/`squash!` commit after its target and folds it.
- `GIT_SEQUENCE_EDITOR=:` accepts the todo list with no editor.
- `origin/main` is only as new as the last `git fetch`.

# Step-by-Step
1. Query says fixup/fold/squash → output exactly: `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <base>`. Base = branch named, else `main`.
2. Query says "latest", "from origin" or "remote" (no fixup) → output exactly: `git fetch origin && git rebase origin/main`.
3. NEVER output bare `git rebase origin/main`. Always put `git fetch origin &&` before it.
4. No `git log`, no `git push`.

# Feedback / Lessons
- Rule: Fold fixups with `--autosquash`. Why: plain `-i` leaves them as separate commits.
- Rule: "latest main from origin" → `git fetch origin && git rebase origin/main`. Why: without fetch, origin/main is stale.
- Rule: Base branch goes last, after all flags.
