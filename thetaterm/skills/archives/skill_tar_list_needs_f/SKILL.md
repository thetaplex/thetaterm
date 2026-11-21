---
name: skill_tar_list_needs_f
description: List or extract tar archives correctly by always naming the archive with -f placed right before the filename.
metadata:
  category: archives
  base_model: gemma4:e4b-mlx
  trigger_keywords: [list files in archive, tar.gz contents, without extracting, show archive contents, tgz, tar list, what is inside tar]
  programs: [tar]
---

# Domain Knowledge
- tar treats a bare filename as a member pattern, not as the archive. The archive file must come after `-f`.
- Without `-f`, tar reads from the tape device or stdin, so `tar -t file.tar.gz` hangs or fails.
- macOS tar (bsdtar) detects gzip, bzip2 and xz by itself, so `z` is optional. `-tzf` works too.
- Modes: `t` lists the contents, `x` extracts, `c` creates. Listing extracts nothing.

# Step-by-Step
1. Pick the mode letter. For "list", "show contents" or "without extracting", use `t`.
2. Optional: add `v` for a detailed listing.
3. Put `f` LAST in the flag bundle. The archive name must come right after it.
4. Output `tar -tf ARCHIVE`, for example `tar -tf backup.tgz` or `tar -tvf data.tar.xz`.

# Feedback / Lessons
- Rule: Every tar command that reads or writes an archive file needs `-f ARCHIVE`, with `f` as the last flag. Why: `tar -t archive.tar.gz` has no `-f`, so tar ignored the file and tried to read the tape device.
- Rule: To see what is inside a .tar.gz, use `tar -tf`, not zgrep or gunzip. Why: zgrep searches the decompressed bytes for text. It does not list the members of the archive.
