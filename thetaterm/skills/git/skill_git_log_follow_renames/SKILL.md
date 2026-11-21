---
name: skill_git_log_follow_renames
description: Show a file's full git history across renames by using git log --follow
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [history of, before it was renamed, renamed, moved file, file history, follow renames, old name]
  programs: [git]
---

# Domain Knowledge
- `git log -- FILE` stops at the commit where FILE got its current name. Commits from before a rename or move are left out.
- `git log --follow -- FILE` detects renames and keeps going through the file's older names.
- `--follow` takes exactly one file path. It does not work on a directory or on several paths.
- Git behaves the same on macOS/BSD and GNU, so no OS-specific flags are needed.
- Add `-p` to show the diffs or `--oneline` for one line per commit, but only if the query asks for that.

# Step-by-Step
1. Find the single file path in the query, such as `src/app.py`.
2. If the query says renamed, moved, old name, before or full history, add `--follow`.
3. Put the options first, then `--`, then the path: `git log --follow -- PATH`.
4. Output only that one command. Do not pipe it to grep.

# Feedback / Lessons
- Rule: For a file's history "including before it was renamed", always use `git log --follow -- PATH`.
  Why: Plain `git log -- PATH` stops at the rename and drops the older commits.
- Rule: Do not add grep when git can answer on its own.
  Why: Extra pipes add mistakes and do not help git find renames.
