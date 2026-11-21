---
name: skill_largest_files_top_n
description: List the N largest (or smallest) files in a directory on BSD/macOS using ls -S and head with the exact N.
metadata:
  category: files
  base_model: gemma4:e4b-mlx
  trigger_keywords: [largest files, biggest files, top files by size, sort by size, smallest files, files taking space]
  programs: [ls, head, grep]
---

# Domain Knowledge
- `ls -lS` sorts by size, largest first, on BSD and GNU. Add `-r` for smallest first.
- `ls -l` prints a `total` line first, and it lists directories too.
- `grep '^-'` keeps regular files only, so the `total` line and directories drop out.
- `du` reports disk usage in blocks, not file size. It does not rank single files well, so avoid it here.
- GNU-only flags like `du -b`, `--max-depth` and `sort -h` are not safe on macOS.

# Step-by-Step
1. Take N straight from the query. Words like "top"/"largest" with no number mean 10.
2. Sort and keep regular files: `ls -lS | grep '^-'`.
3. Cut to exactly N: `| head -n N`.
4. Final form: `ls -lS | grep '^-' | head -n N`.

# Feedback / Lessons
- Rule: Use the user's number exactly in `head -n N`. Never write N+1 to skip a header line.
  Why: `head -n 6` for "5 largest" prints the wrong count, and the check failed because 5 was missing.
- Rule: Remove header lines with `grep '^-'`, not by changing the count.
  Why: it also drops directories, so only files are ranked.
