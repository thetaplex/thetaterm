du reports disk usage, not file size. -b (apparent size in bytes) and
--max-depth are GNU only; BSD du, as on macOS, rejects them. BSD du counts in
512-byte blocks unless given -k, -m, -g or -h, and -A gives the apparent size
instead of disk usage; it has no option for bytes. The file size in bytes is
column 5 of ls -l on both. -h output does not sort correctly with sort -n.
