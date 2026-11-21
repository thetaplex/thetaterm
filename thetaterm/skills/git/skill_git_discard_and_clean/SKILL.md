---
name: skill_git_discard_and_clean
description: Throw away all local git changes, both tracked edits and untracked files and directories, without touching ignored files. Not for stashing.
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [discard all uncommitted, discard changes, throw away changes, delete untracked, remove untracked, git clean, reset hard, clean working tree]
  programs: [git]
---

# Scope
Use this skill ONLY to delete changes forever.
If the query says "stash", this skill does not apply. Use: `git stash push -u`

# Answer
Copy this command exactly:
`git reset --hard && git clean -fd`

# Domain Knowledge
- `git reset --hard` undoes tracked edits, staged and unstaged.
- `git clean -fd` deletes untracked files AND untracked folders.
- `-x` and `-X` also delete ignored files like .env. Leave them out.
- Use only git. Never `rm`.

# Step-by-Step
1. Does the query say "stash"? Yes → write `git stash push -u` and stop.
2. Otherwise write `git reset --hard && git clean -fd`.
3. Check: the clean part ends in `-fd`, not just `-f`.

# Feedback / Lessons
- Rule: `git clean -f` is WRONG. `git clean -fd` is RIGHT. Why: `-f` leaves untracked folders.
- Rule: no `-x`, no `-X`. Why: they delete ignored secrets.
- Rule: stash with untracked = `git stash push -u`, never `-a`. Why: `-a` also stashes ignored files.
