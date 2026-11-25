---
name: skill_find_repo_by_name
description: Find where a repo, project or folder lives by searching directory names with find, not git
metadata:
  category: files
  base_model: gemma4:e4b-mlx
  trigger_keywords: [find the repo, find repo, locate repo, where is the repo, find the project, find project, find the folder, find folder, find the directory, find directory]
  programs: [find, git]
---

# Domain Knowledge
- A repo is a directory on disk. Finding it is a search for a directory name, so use `find`.
- `git` works inside a repo that you already have. It cannot search the disk for one.
- `-type d` matches directories only. `-prune` stops `find` from going into each match.
- A repo is usually somewhere under the home directory, not under the current directory.

# Step-by-Step
1. Search from `~` unless the query names a location.
2. Match the name: `-type d -name NAME`. Use `-iname '*NAME*'` if the query says "like" or "containing".
3. Add `-prune` and send errors to `/dev/null`: `find ~ -type d -name NAME -prune 2>/dev/null`.

# Feedback / Lessons
- Rule: "find the repo thetamate" → `find ~ -type d -name thetamate -prune 2>/dev/null`. Why: `git -C thetamate --version` only works if the repo is already in the current directory, and it finds nothing.
- Rule: never answer "find the repo X" with a `git` command. Why: git has no command that searches the disk for repositories.
