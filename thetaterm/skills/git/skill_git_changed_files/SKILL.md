---
name: skill_git_changed_files
description: List the files changed in a commit or range with git's --name-only, --name-status or --stat, not the full diff.
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [which files changed, files changed, last commit, changed files, files modified, list files in commit, what changed]
  programs: [git]
---

# Domain Knowledge
- git is the same on macOS and Linux. BSD vs GNU makes no difference here.
- `git show HEAD` and `git diff` print the full patch, not a list of files.
- `--name-only` prints file paths only. `--name-status` adds the change type (A/M/D/R). `--stat` adds per-file line counts.
- Last commit: `HEAD`. Earlier commits: `HEAD~N`. A range is `A..B`.
- Uncommitted changes: `git diff --name-only`. Staged changes: add `--cached`.

# Step-by-Step
1. Pick the target: last commit = `HEAD`, N commits back = `HEAD~N`, working tree = no ref.
2. Pick the flag. Just names: `--name-only`. Names with change type: `--name-status`. Line counts: `--stat`.
3. For a commit: `git show --name-only --format= HEAD`. For a range: `git diff --name-only A B`.
4. Check that the command has exactly one of those three flags.

# Feedback / Lessons
- Rule: When asked "which files changed", always add `--name-only`, `--name-status` or `--stat`.
  Why: `git show HEAD` alone dumps the whole diff, not the list of files.
- Rule: Add `--format=` to `git show` to hide the commit header.
  Why: Then the output is only the file list.
