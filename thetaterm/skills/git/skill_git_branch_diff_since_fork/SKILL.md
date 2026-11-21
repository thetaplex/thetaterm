---
name: skill_git_branch_diff_since_fork
description: Show what a branch changed since it forked from a base branch by diffing against the merge-base
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: ["since it split", "branched off", "forked from", "diverged from main", "my branch changed", "compared to main", "since branching"]
  programs: [git]
---

# Domain Knowledge
- "What changed" asks about content, so use `git diff`. "Which commits" asks for a list, so use `git log`.
- `git diff main...HEAD` (three dots) compares HEAD to the merge-base, which means only your branch's changes.
- `git diff main..HEAD` (two dots) is the same as `git diff main HEAD`. It compares the two tips and also shows main's newer work reversed.
- `git merge-base main HEAD` prints the commit where the branch split off.
- git behaves the same on macOS/BSD and Linux.

# Step-by-Step
1. Phrases like "split off", "branched", "forked" or "diverged" mean the base is the merge-base.
2. If the user asks for changes, a diff or files, run `git diff main...HEAD`. Add `--stat` or `--name-only` when they ask for a summary or a file list.
3. Use `git log main..HEAD` only when they ask for the commits themselves.
4. Replace `main` with the base branch the user names (master, develop).

# Feedback / Lessons
- Rule: "show what my branch changed since it split off main" means `git diff main...HEAD`. Why: `git log` lists commit messages, not the changes.
- Rule: use three dots with `git diff` to see branch-only changes. Why: two dots compares the tips and mixes in main's changes.
