ping keeps sending until you stop it, on both Linux and macOS. Use -c COUNT to
stop after COUNT replies, such as -c 3, and check the exit status: 0 means the
host answered. Some networks block ping, so no reply doesn't always mean the
host is down.
