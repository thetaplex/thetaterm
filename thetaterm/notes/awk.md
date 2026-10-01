Fields ($1, $2, ...) are split on runs of spaces and tabs by default, not on
commas. For comma-separated (CSV) files, set the separator with -F, as in
awk -F, '{print $1}' file.csv; for tab-separated files use -F'\t'. -F does not
understand quoted fields that contain the separator.
