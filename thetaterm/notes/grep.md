The shell expands an unquoted file-name pattern before grep runs, and only to
matches in the current directory, so with -r it never reaches subdirectories.
To search recursively for some kinds of file, use --include with a quoted
pattern and give a directory to search.
