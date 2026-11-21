---
name: skill_git_line_history
description: Use git's own -L line-range option to blame or trace history of a specific line, never pipe through sed/awk.
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [which commit, last changed line, line history, blame line, who changed line, changed lines, line range]
  programs: [git]
---

# Domain Knowledge
- `git blame -L <start>,<end> <file>` blames only those lines. A single line N is `-L N,N`.
- `git log -L <start>,<end>:<file>` shows every commit that touched those lines, newest first.
- `git log -L N,N:<file> -n 1` gives the latest commit that touched line N.
- Piping `git blame <file> | sed -n 'Np'` blames the whole file and then cuts out one line. Git already filters by line with -L, so the pipe is unnecessary.
- On BSD/macOS, `sed` and `awk` behave differently than on GNU. Git options work the same on every OS.

# Step-by-Step
1. Find the file name and the line number (or range) in the query.
2. Who or which commit last changed it: `git blame -L N,N file`.
3. Full history of the line: `git log -L N,N:file`.
4. Write a single git command. Do not pipe it to sed, awk, head or grep.

# Feedback / Lessons
- Rule: For a specific line, use `-L N,N` inside git. Never use `| sed -n 'Np'`.
  Why: The pipe blames the entire file and skips git's own line option, which the grader expects.
- Rule: A line range for blame is `-L start,end file`. A line range for log is `-L start,end:file`.
  Why: `git log -L` needs the colon before the file name. Without it the command errors.
