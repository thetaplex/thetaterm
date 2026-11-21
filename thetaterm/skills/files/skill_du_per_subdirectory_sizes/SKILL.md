---
name: skill_du_per_subdirectory_sizes
description: Get disk usage for each subdirectory by giving du path arguments or -d 1, never by piping names into it
metadata:
  category: files
  base_model: gemma4:e4b-mlx
  trigger_keywords: [size of each subdirectory, folder sizes, directory size, disk usage, how big, du]
  programs: [du, sort]
---

# Domain Knowledge
- du takes paths as arguments and never reads stdin. `ls */ | du -s` ignores the pipe and only measures `.`.
- The shell expands `*/` into every subdirectory, so you don't need ls.
- `-s` prints one total for each argument. `-h` gives human units and `-k` gives KiB.
- On BSD du (macOS) the depth option is `-d 1`. `--max-depth` only works with GNU du.
- `sort -n` doesn't order `-h` output correctly. Use `-k` when you sort.

# Step-by-Step
1. For the size of each subdirectory, write `du -sh */`.
2. To also show the total for `.`, write `du -h -d 1`.
3. Always give du its paths as arguments. Never pipe names into du.
4. To sort by size, write `du -sk */ | sort -n`.

# Feedback / Lessons
- Rule: Don't pipe ls into du. Write `du -sh */`. Why: du ignored stdin, so it summed only `.`.
- Rule: On macOS, write `-d 1`, not `--max-depth=1`. Why: BSD du rejects GNU long options.
