---
name: skill_git_merge_conflict_files
description: List only the files that have unresolved merge conflicts, using git's unmerged filters instead of plain git status.
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [merge conflict, conflicted files, unmerged files, conflicts, unresolved, rebase conflict, both modified]
  programs: [git]
---

# Domain Knowledge
- Plain `git status` prints every change, not just the conflicts. It does not answer "which files conflict".
- Conflicted files are "unmerged" (status U). There are two exact ways to list them:
  - `git diff --name-only --diff-filter=U` prints one path per line.
  - `git ls-files -u` (or `--unmerged`) prints staged entries for each conflict stage.
- These are git built-ins, so they behave the same on macOS/BSD and GNU. Don't use grep pipes on status output.

# Step-by-Step
1. If the query says conflict, unmerged, or unresolved, the target is files with status U.
2. To list file names, output `git diff --name-only --diff-filter=U`.
3. If the query asks for stages or index details, output `git ls-files -u`.
4. Output one command only and don't add a pager.

# Feedback / Lessons
- Rule: Never answer "files with merge conflicts" with bare `git status`. Use `--diff-filter=U`.
  Why: `git status` mixes conflicts in with all the other changes, and a filtered list was asked for.
- Rule: For any "only files that are X" git query, use git's own filter flags (`--diff-filter`, `ls-files` options).
  Why: These flags are exact and portable, while parsing status text breaks.
