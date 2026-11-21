---
name: skill_tar_gzip_archive
description: Create a .tar.gz/.tgz archive of a file or directory with one tar command using -czf, without piping to gzip.
metadata:
  category: archives
  base_model: gemma4:e4b-mlx
  trigger_keywords: [compress directory, tar.gz, tgz, archive folder, gzip a folder, make tarball, compress into]
  programs: [tar]
---

# Domain Knowledge
- tar on macOS (bsdtar) and GNU tar both have `-z`, which gzips the archive. You never need `gzip` or a pipe.
- `-f NAME` takes the very next word as the archive name. The archive name comes before the sources.
- `gzip` by itself only compresses single files and cannot pack a directory.
- Other compressions work the same way: `-j` gives .tar.bz2 and `-J` gives .tar.xz.

# Step-by-Step
1. Find the SOURCE (the directory or files) and the ARCHIVE name (for example `x.tar.gz`). If no name is given, use `SOURCE.tar.gz`.
2. Pick the flag from the extension: .tar.gz/.tgz → `z`, .bz2 → `j`, .xz → `J`.
3. Write exactly: `tar -czf ARCHIVE SOURCE`
4. Check: one tar command, no `|`, no `gzip`, ARCHIVE written right after `f`.

# Feedback / Lessons
- Rule: Use `tar -czf logs.tar.gz logs`, never `tar -cf - logs | gzip > logs.tar.gz`.
  Why: `-z` already gzips. The pipe version is longer, and it hides the archive name from tar.
- Rule: Keep `f` as the last letter of the bundled flags, with the archive name right after it.
  Why: `-cfz x.tar.gz` treats `z` as the archive name.
