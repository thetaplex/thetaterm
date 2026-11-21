---
name: skill_git_fixup_squash_commit
description: Create fixup/squash commits that target a named earlier commit instead of amending HEAD
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [fixup commit, fixup, squash commit, autosquash, fix earlier commit, commit for commit]
  programs: [git]
---

# Domain Knowledge
- A fixup commit is a new commit that is marked to merge into an earlier commit: `git commit --fixup=<hash>`. Git sets its message to "fixup! <subject>".
- `--amend` only rewrites HEAD. It never targets an older commit, so it is wrong for "fixup for commit X".
- `git commit --squash=<hash>` works the same way but keeps the message open for editing.
- To merge these commits in later, run `git rebase -i --autosquash <hash>~1`.
- These git flags are the same on macOS/BSD and Linux.

# Step-by-Step
1. Find the commit ref in the query (for example abc1234 or HEAD~2).
2. If the query says "fixup", use `git commit --fixup=<ref>`. If it says "squash", use `git commit --squash=<ref>`.
3. Add `-a` only if the user asks to include all tracked changes.
4. Copy the ref exactly as written and output one command.

# Feedback / Lessons
- Rule: Never answer "fixup commit for X" with `--amend`. Why: amend edits HEAD, ignores X and creates no fixup commit.
- Rule: Always put the named ref in `--fixup=<ref>`. Why: without the ref, git cannot tell which commit is being fixed.
