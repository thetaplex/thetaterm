---
name: skill_count_lines_across_files
description: Count the total lines in many files as one number, without skipping blank lines or counting the total twice.
metadata:
  category: text
  base_model: gemma4:e4b-mlx
  trigger_keywords: [total lines, number of lines, line count, count lines, all files, lines in all, how many lines]
  programs: [awk, wc, cat]
---

# Domain Knowledge
- A blank line is still a line. `grep .` and `grep -v '^$'` drop blank lines, so they undercount.
- `grep -c ''` prints one count per file, not a single total.
- `wc -l a b` prints a line for each file and then a `total` line. If you add up its output with awk, the total gets counted twice.
- `awk 'END{print NR}' files...` prints one number. NR keeps counting across all files, and it also counts a last line that has no newline.
- BSD and GNU behave the same here.

# Step-by-Step
1. Pass the files straight to awk: `awk 'END{print NR}' *.txt`.
2. To use wc instead, join the files first so there is only one count: `cat *.txt | wc -l`.
3. Use the glob from the query, such as `*.txt` or `*.log`.

# Feedback / Lessons
- Rule: Never filter lines with grep when the task is counting lines.
  Why: `grep . | wc -l` skips blank lines, so the total comes out too low.
- Rule: Never pipe `wc -l` output into an awk `+=` sum.
  Why: wc already prints a total line, so the sum comes out double.
