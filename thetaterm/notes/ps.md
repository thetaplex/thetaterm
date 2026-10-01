--sort is GNU (procps, on Linux) only; BSD ps, as on macOS, and BusyBox ps
reject it. On BSD, -m sorts by memory and -r by CPU. Anywhere, sort ps aux
output instead: %CPU is column 3 and %MEM column 4, as in
ps aux | sort -nrk 4 | head.
