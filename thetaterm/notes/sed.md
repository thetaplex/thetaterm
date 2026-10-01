-i edits files in place, and BSD and GNU sed take it differently. BSD sed, as
on macOS, requires a backup suffix as the next argument, where an empty
argument means no backup; without one, the script is taken as the suffix. GNU
sed, on Linux, accepts a suffix only attached to -i, so a separate empty
argument is read as the script. -E turns on extended regular expressions in
both; -r is GNU only.
