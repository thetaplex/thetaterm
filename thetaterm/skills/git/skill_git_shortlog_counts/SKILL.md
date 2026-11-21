---
name: skill_git_shortlog_counts
description: Count commits per author or committer with git shortlog -sn, not a log|sort|uniq pipeline
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [commits per author, count commits, commits by author, top contributors, who committed most, author commit count, contributors]
  programs: [git]
---

# Domain Knowledge
- `git shortlog` groups commits by author. It has built-in counting: `-s` (--summary) prints only counts, `-n` (--numbered) sorts by count with the highest first, and `-e` adds emails.
- `git shortlog -sn HEAD` does the whole job in one command. You don't need sort, uniq or awk.
- If no revision is given and stdin is not a terminal, shortlog reads from stdin and prints nothing. Always pass `HEAD`, `--all`, or a range.
- Options: `--all` counts every branch, `-c` groups by committer, `--since=DATE` limits the dates, and `-- PATH` limits to a path.

# Step-by-Step
1. If the query asks to count, rank or list commits per person, use `git shortlog`.
2. Add `-sn` (add `e` to make `-sne` if emails are wanted).
3. Add a revision: `HEAD`, or `--all` for all branches.
4. Add any filters (`--since`, `-c`, `-- path`). Output exactly one command.

# Feedback / Lessons
- Rule: For per-author commit counts, write `git shortlog -sn HEAD`, not `git log --pretty=%an | sort | uniq -c | sort -nr`.
  Why: shortlog already groups, counts and sorts, so the pipeline just rebuilds it.
- Rule: Never run `git shortlog` without a revision.
  Why: when it isn't run in a terminal it reads stdin and returns empty output.
