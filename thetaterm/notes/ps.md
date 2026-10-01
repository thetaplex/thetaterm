--sort is GNU (procps, on Linux) only; BSD ps, as on macOS, and BusyBox ps
reject it. On BSD, -m sorts by memory and -r by CPU. In the output of ps aux,
%CPU is column 3 and %MEM column 4.
