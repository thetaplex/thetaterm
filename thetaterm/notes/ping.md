ping keeps sending until it is stopped, on both Linux and macOS. -c COUNT
stops after COUNT replies. The exit status is 0 when the host answered. Some
networks block ping, so no reply doesn't always mean the host is down.
