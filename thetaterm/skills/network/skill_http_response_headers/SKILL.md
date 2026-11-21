---
name: skill_http_response_headers
description: Show HTTP response headers on stdout with curl -I or -D -, never a temp file
metadata:
  category: network
  base_model: gemma4:e4b-mlx
  trigger_keywords: [http headers, response headers, show headers, header of url, http status, content-type, server header]
  programs: [curl]
---

# Domain Knowledge
- `curl -I URL` (`--head`) sends a HEAD request and prints only the response headers.
- `curl -sD - -o /dev/null URL` sends a normal GET, writes the headers to stdout (`-` means stdout), and throws away the body.
- `-D FILE` (`--dump-header`) writes headers to a file. Don't use a file when the user asked to see the headers.
- `-i` prints the headers followed by the body, so the output is noisy.
- `openssl s_client` is for TLS and certificates, not HTTP headers.
- These flags work the same on macOS/BSD and Linux curl.

# Step-by-Step
1. Pick `curl` alone. Don't use openssl, `&&`, or temp files.
2. Default command: `curl -I https://HOST`.
3. If the server rejects HEAD or the user says GET: `curl -sD - -o /dev/null https://HOST`.
4. Put the flags before the URL, and quote the URL if it has `?` or `&`.

# Feedback / Lessons
- Rule: Use `-I`, or `-D -` (dash = stdout). Never `-D file && cat file`.
  Why: A temp file adds clutter and a second command, and the body still floods stdout.
- Rule: Write one curl command with no pipes.
  Why: Headers are a single curl flag, so extra tools only add ways to fail.
