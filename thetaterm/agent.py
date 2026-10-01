"""Turn natural language into a shell command using the OS's own docs.

Small models can't memorise the differences between GNU, BSD and BusyBox
userlands, so we don't ask them to: the model suggests commands, the machine
says which are installed, and the man page of the chosen one goes into the
prompt. The model only has to read and fill in.
"""

import json
import math
import os
import platform
import re
import shlex
import shutil
import subprocess
import urllib.error
import urllib.request
from urllib.parse import urlsplit

# problem() and outside() read commands as sh words, so only shells that parse like sh
POSIX_SHELLS = {"sh", "bash", "zsh", "ksh", "dash"}


def user_shell() -> str:
    """The login shell if it parses like sh, else bash, else /bin/sh."""
    login = os.environ.get("SHELL", "")
    if os.path.basename(login) in POSIX_SHELLS and shutil.which(login):
        return login
    return shutil.which("bash") or "/bin/sh"


SHELL = user_shell()
_STOPWORDS = (
    "a an the to of in on for from with and or all any my me i this that these those "
    "is are be it its by as at into using use how what which show get make do"
)
STOPWORDS = set(_STOPWORDS.split())
# `!` negates a pipeline in command position; elsewhere (find ! -name) it is an argument
PREFIXES = {"sudo", "env", "time", "nohup", "command", "!"}
MAX_REFERENCE_CHARS = 3500
RETRIES = 2
# devices that hold no files; anything else under /dev (disks) counts as outside
SAFE_DEVICE = re.compile(r"/dev/(null|zero|u?random|tty|std(in|out|err)|fd/\d+)")
# variables that can't name a directory
SAFE_VARIABLES = {"PWD", "USER", "LOGNAME", "UID", "RANDOM", "IFS"}


def sh(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    env = os.environ | {"PAGER": "cat", "MANPAGER": "cat", "MANWIDTH": "100"}
    try:
        return subprocess.run(  # noqa: S603 an argv list, no shell
            args, capture_output=True, text=True, timeout=timeout, env=env, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(args, 1, "", str(e))


def environment() -> str:
    """One line describing the OS and which userland flavour its tools are."""
    system = platform.system()
    if system == "Darwin":
        name = f"macOS {platform.mac_ver()[0]}"
    elif system == "Linux":
        try:
            name = platform.freedesktop_os_release().get("PRETTY_NAME", "Linux")
        except OSError:
            name = "Linux"
    else:
        name = f"{system} {platform.release()}"

    ls = shutil.which("ls") or ""
    if os.path.realpath(ls).endswith("busybox"):
        userland = "BusyBox"
    elif "GNU" in sh(["ls", "--version"]).stdout:
        userland = "GNU coreutils"
    else:
        userland = "BSD"
    return f"{name}, {userland} userland, {os.path.basename(SHELL)} shell"


def keywords(query: str) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9._+-]*", query.lower())
    # ponytail: crude plural stripping, a real stemmer if excerpts miss too much
    return [
        w[:-1] if len(w) > 3 and w.endswith("s") else w
        for w in words
        if w not in STOPWORDS
    ]


def reference(command: str, query: str) -> str:
    """The parts of a command's man page relevant to the query.

    Never `command --help`: a program that doesn't honour it would run before
    the user agreed to anything (ADR 0005).
    """
    text = re.sub(r".\x08", "", sh(["man", command]).stdout)  # strip overstrike bold
    return excerpt(text, query)


def entries(text: str) -> list[tuple[int, str]]:
    """Split docs into (first line number, text) paragraphs and option entries."""
    found, current, start, indent, blank = [], [], 0, 0, False
    for n, line in enumerate(text.splitlines()):
        line = line.rstrip()
        body = line.lstrip()
        if not body:
            blank = True
            continue
        depth = len(line) - len(body)
        # an option at or left of the entry's own indent starts a new one, even
        # without a blank line between (--help output rarely has them); after a
        # blank line only text indented under an option continues it (-type's list)
        under_option = current[:1] and current[0].lstrip().startswith("-")
        if current and (
            (blank and not (under_option and depth > indent))
            or (body.startswith("-") and depth <= indent)
        ):
            found.append((start, "\n".join(current)))
            current = []
        if not current:
            start, indent = n, depth
        current.append(line)
        blank = False
    if current:
        found.append((start, "\n".join(current)))
    return found


def excerpt(text: str, query: str) -> str:
    """Whole entries that best match the query, rare words counting most."""
    chunks = entries(text)
    words = set(keywords(query))
    matches = [{w for w in words if w in chunk.lower()} for _, chunk in chunks]
    df = {w: sum(w in m for m in matches) for w in words}
    idf = {w: math.log(len(chunks) / n) for w, n in df.items() if n}

    def score(i: int) -> float:
        if chunks[i][0] < 20:  # NAME + SYNOPSIS
            return math.inf
        return sum(idf[w] for w in matches[i])

    keep, used = set(), 0
    # stable sort: ties go to whatever comes first on the page
    for i in sorted(range(len(chunks)), key=score, reverse=True):
        size = len(chunks[i][1]) + 1
        if score(i) and used + size <= MAX_REFERENCE_CHARS:
            keep.add(i)
            used += size
    return "\n".join(chunks[i][1] for i in sorted(keep))


def clean(response: str) -> str:
    """Pull the bare command out of whatever the model wrapped it in."""
    # a fenced block beats any prose around it
    fenced = re.search(r"```\w*\n(.*?)```", response, re.DOTALL)
    text = fenced[1] if fenced else re.sub(r"```\w*", "", response).strip()
    line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    # some models echo the prompt's "Command:" label
    line = re.sub(r"^command:\s*", "", line, flags=re.IGNORECASE).strip("`")
    for prefix in ("$ ", "# ", "> "):
        line = line.removeprefix(prefix)
    return line.strip()


def tokens(command: str) -> list[str]:
    """Shell words and operators; raises ValueError on unbalanced quotes."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def outside(command: str) -> str | None:
    """Why this command may reach beyond the current directory, or None.

    ponytail: pattern match on the words, catches the model's honest mistakes, not
    obfuscation (`cat $(printf '\\x2f')etc`); a real sandbox if that matters.
    """
    words = tokens(command)
    for i, token in enumerate(words):
        # --output=/tmp/x, of=/dev/sda, -C/tmp
        path = re.sub(r"^-[A-Za-z]", "", token.split("=", 1)[-1])
        if token == "sudo":  # noqa: S105 a shell word, not a password
            return "runs as root"
        # bare `cd` goes home, `cd -` and `popd` go back to an earlier directory
        target = words[i + 1] if i + 1 < len(words) else ";"
        if token in {"cd", "pushd", "popd"} and target in {
            "-",
            ";",
            "&&",
            "||",
            "&",
            ")",
        }:
            return f"{token} leaves for the home or previous directory"
        if path.startswith("~"):
            return f"home path {token}"
        if path.startswith("/") and not SAFE_DEVICE.fullmatch(path):
            return f"absolute path {token}"
        if ".." in path.split("/"):
            return f"parent path {token}"
    # any variable may hold a path; single quotes don't expand, loop and read
    # variables are the command's own
    unquoted = re.sub(r"'[^']*'", "", command)
    own = set(re.findall(r"\bfor\s+(\w+)\s+in\b", unquoted))
    own |= set(re.findall(r"\bread\s+(?:-\w+\s+)*(\w+)", unquoted))
    own |= set(re.findall(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=", unquoted))
    for name in re.findall(r"\$\{?([A-Za-z_]\w*)", unquoted):
        if name not in own | SAFE_VARIABLES:
            return f"uses ${name}"
    return None


def problem(command: str) -> str | None:
    """Why this command would fail before it even runs, or None."""
    if not command:
        return "empty command"
    # stderr, not the exit status: zsh -n returns 1 for a valid `! cmd`
    r = sh([SHELL, "-n", "-c", command])
    if r.returncode and r.stderr.strip():
        return r.stderr.strip()
    try:
        # shlex unquotes find's `\;` into a bare `;`, which would read as a separator
        words = tokens(re.sub(r"\\;|';'|\";\"", "_", command))
    except ValueError as e:
        return str(e)
    at_command = True
    for token in words:
        if token in {"|", "||", "&&", ";", "&", "(", "{"}:
            at_command = True
        elif at_command:
            if re.match(r"\w+=", token) or token in PREFIXES:
                continue
            if sh([SHELL, "-c", f"command -v {shlex.quote(token)}"]).returncode:
                return f"{token}: command not found"
            at_command = False
    return None


class Agent:
    """Talks to any OpenAI-compatible chat endpoint (Ollama, llama.cpp, vLLM, ...)."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None = None,
        thinking: bool = False,
    ):
        # urlopen also reads file: and ftp: URLs; only talk to a server
        if urlsplit(base_url).scheme not in {"http", "https"}:
            raise ValueError(f"{base_url}: not an http(s) URL")
        self.model = model
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self.env = environment()
        # Thinking models reason for minutes over a man page to write one command.
        # Dropped if the server rejects it.
        self.thinking = thinking
        self.thinking_off = {} if thinking else {"reasoning_effort": "none"}

    def ask(self, prompt: str, max_tokens: int | None = None) -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        } | self.thinking_off
        # reasoning counts against max_tokens, so a cap would cut thinking short
        if max_tokens and not self.thinking:
            body["max_tokens"] = max_tokens
        request = urllib.request.Request(  # noqa: S310 scheme checked in __init__
            self.url, json.dumps(body).encode(), self.headers
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as r:  # noqa: S310 scheme checked in __init__
                reply = json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:200]
            if e.code == 400 and self.thinking_off and "reasoning" in detail:
                self.thinking_off = {}
                return self.ask(prompt, max_tokens)
            raise RuntimeError(f"{self.url}: {e.code} {detail}")
        except OSError as e:
            raise RuntimeError(f"cannot reach {self.url}: {getattr(e, 'reason', e)}")
        except ValueError:
            raise RuntimeError(f"{self.url}: reply is not JSON") from None
        try:
            return reply["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            # some servers answer 200 with {"error": ...}
            raise RuntimeError(
                f"{self.url}: unexpected reply {json.dumps(reply)[:200]}"
            ) from None

    def choose(self, query: str) -> str | None:
        """The main command for the task: the model suggests, the OS confirms."""
        answer = self.ask(
            f"System: {self.env}\nTask: {query}\n"
            "Which commands can do this? List up to 5 command names only, one per line, best first.",
            # some models repeat the last name until the context runs out
            max_tokens=60,
        )
        # one name per line or comma: "1. `ifconfig` - shows ..." -> ifconfig
        for item in re.split(r"[\n,]", answer):
            name = next(iter(re.findall(r"[A-Za-z][\w.+-]*", item)), None)
            if name and shutil.which(name):
                return name
        return None

    def generate(self, query: str) -> str:
        """Best command for the query; raises RuntimeError if none passes checks."""
        prompt = f"System: {self.env}\n"
        # a thinking model works out the platform's flags itself; the extra
        # round trip and man page only slow it down (evals: 49/50 vs 48/50)
        chosen = None if self.thinking else self.choose(query)
        if chosen:
            ref = reference(chosen, query)
            prompt += f"\nReference for `{chosen}` on this system:\n{ref}\n"
        prompt += (
            f"\nTask: {query}\nWrite one {os.path.basename(SHELL)} command for this system. "
            "Use real paths, never placeholders like /path/to; if the task names no location, use the current directory (.). "
            "Reply with the command only.\n"
        )

        attempt = prompt
        for _ in range(RETRIES + 1):
            command = clean(self.ask(attempt + "Command:"))
            error = problem(command)
            if error is None:
                return command
            attempt = f"{prompt}\nThe command `{command}` fails: {error}\nWrite a corrected command.\n"
        raise RuntimeError(f"no working command found (last: `{command}`: {error})")
