---
name: skill_ls_hidden_files
description: List directory contents including hidden dotfiles with ls -a/-A instead of find
metadata:
  category: files
  base_model: gemma4:e4b-mlx
  trigger_keywords: [list files, hidden files, dotfiles, all files, show hidden, including hidden, list directory]
  programs: [ls, find]
---

# Domain Knowledge
- Hidden files are names starting with `.`, and plain `ls` skips them.
- `ls -a` shows every file, including `.` and `..`. `ls -A` shows every file except `.` and `..`.
- Add `-l` for details (`ls -la`) and `-R` to go into subdirectories (`ls -laR`).
- BSD `ls` on macOS has no `--all`, so use short flags only.
- `find` searches by name, type, size or age. It is not the tool for a plain listing.

# Step-by-Step
1. If the query says "list" or "show" files or a directory, use `ls`.
2. If it says "hidden", "all", "dotfiles" or "including .", add `-a`.
3. Add `-l` for "details", "sizes" or "permissions", and `-R` for "recursive".
4. Use `find` only when the query filters by name, type, size or time.

# Feedback / Lessons
- Rule: "list all files including hidden" → `ls -a` (or `ls -la`). Why: `find . -maxdepth 1 -print` lists the files but is not the expected answer. `-a` is the standard flag for hidden files.
- Rule: never answer a plain listing request with `find`. Why: `ls` lists files and `find` searches for them, so a listing query needs `ls` plus a flag.
