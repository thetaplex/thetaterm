"""Turn natural language into a shell command using the OS's own docs.

Small models can't memorise the differences between GNU, BSD and BusyBox
userlands, so we don't ask them to: the model suggests commands, the machine
says which are installed, and the man pages of the first two go into the
prompt. The model only has to read and fill in.
"""

import functools
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
from importlib.resources import files
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
# a note leaves most of the reference to the man page
MAX_NOTE_CHARS = 600
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
    # ValueError: a NUL byte in an argument
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
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


def note(command: str) -> str:
    """Our note on what the command's man page excerpt tends to miss (ADR 0006)."""
    path = files("thetaterm") / "notes" / f"{command}.md"
    return path.read_text().strip() if path.is_file() else ""


def reference(command: str, query: str) -> str:
    """The command's note, then the parts of its man page relevant to the query.

    Never `command --help`: a program that doesn't honour it would run before
    the user agreed to anything (ADR 0005).
    """
    head = note(command)
    head = f"Notes:\n{head}\n\n" if head else ""
    return head + excerpt(man_page(command), query, MAX_REFERENCE_CHARS - len(head))


@functools.cache
def man_page(command: str) -> str:
    """The installed man page as plain text, "" if there is none."""
    text = re.sub(r".\x08", "", sh(["man", command]).stdout)  # strip overstrike bold
    # groff may print an option's dash as a hyphen or minus sign
    return text.translate({0x2010: "-", 0x2212: "-"})


# -x as a word of its own: -a, -B blocksize, -v[+|-]val; not -type or --all
SHORT_OPTION = re.compile(r"(?<![\w-])-([\w@%,])(?![\w-])")
# -Aclnx in [-Aclnx], -H in [-H | -L]
CLUSTER = re.compile(r"(?<![\w-])-([\w@%,]+)")
# documented with an argument: -d depth, -v[+|-]val, -k, --key=KEYDEF, -o, --output <file>
WITH_ARGUMENT = re.compile(
    r"(?<![\w-])-([\w@%])(?:,\s*--[\w-]+)?(?:[=\[<]| (?:[a-z<\[]|[A-Z]{2}))"
)


def scan_options(page: str, args: list[str]) -> tuple[str | None, int]:
    """The first short option the man page doesn't list, and where options end.

    Options end at the first operand, `--` or `-`, as BSD getopt reads them; GNU
    lets options follow operands, and those go unchecked. Any option on the page
    counts, even one only named in passing: a page that leaves one out of its
    SYNOPSIS (BSD grep's -r) mustn't turn a working command away.
    """
    synopsis = re.search(r"^SYNOPSIS\n(.*?)^\S", page, re.MULTILINE | re.DOTALL)
    synopsis = synopsis[1] if synopsis else ""
    flags = set(SHORT_OPTION.findall(page))
    flags |= {c for cluster in CLUSTER.findall(synopsis) for c in cluster}
    # only the synopsis and entries: "the -a option" in prose takes no argument
    entries = [line for line in page.splitlines() if line.lstrip().startswith("-")]
    with_argument = set(WITH_ARGUMENT.findall("\n".join([synopsis, *entries])))
    i = 0
    while i < len(args):
        word = args[i]
        if word == "--":
            return None, i + 1
        if not word.startswith("-") or word == "-":
            return None, i
        i += 1
        # ponytail: long options go unchecked; GNU-only ones get through
        # spelled out on the page: java -version, clang -O2
        if (
            not flags
            or word.startswith("--")
            or re.fullmatch(r"-\d+", word)  # an old-style count: head -5
            or len(word) > 2
            and re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", page)
        ):
            continue
        for j, c in enumerate(word[1:], 1):
            if c not in flags:
                return f"-{c}", i - 1
            if c in with_argument:
                i += j == len(word) - 1  # its argument is the next word
                break
    return None, i


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


def excerpt(text: str, query: str, budget: int = MAX_REFERENCE_CHARS) -> str:
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
        if score(i) and used + size <= budget:
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
    if not command.strip():
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
    # zsh's `autoload -Uz zmv && zmv ...` defines the function it then calls
    loaded = {
        name
        for names in re.findall(r"\bautoload((?:\s+[\w-]+)+)", command)
        for name in names.split()
        if not name.startswith("-")
    }
    at_command = True
    for token in words:
        if token in {"|", "||", "&&", ";", "&", "(", "{"}:
            at_command = True
        elif at_command:
            if re.match(r"\w+=", token) or token in PREFIXES:
                continue
            # `$cmd` or `$(...)`'s `$`: the program is only known when it runs
            if token.startswith(("$", "`")):
                at_command = False
                continue
            if (
                token not in loaded
                and sh([SHELL, "-c", f"command -v {shlex.quote(token)}"]).returncode
            ):
                return f"{token}: command not found"
            at_command = False
    return bad_option(words)


def bad_option(words: list[str]) -> str | None:
    """Why a program in the command would reject an option, or None."""
    commands, current = [], []
    for word in words:
        if word in {"|", "||", "&&", ";", "&", "(", ")", "{", "}"} or word.startswith(
            ("<", ">")
        ):
            commands.append(current)
            current = []
        else:
            current.append(word)
    commands.append(current)
    while commands:
        args = commands.pop()
        while args and (re.match(r"\w+=", args[0]) or args[0] in PREFIXES):
            args = args[1:]
        if not args:
            continue
        program, args = args[0], args[1:]
        # a builtin, function or alias prints its name, not a path; their man
        # page, if any, is another program's
        found = sh([SHELL, "-c", f"command -v {shlex.quote(program)}"]).stdout
        if not found.startswith("/"):
            continue
        page = man_page(program)
        option, end = scan_options(page, args)
        if option:
            return f"{program} has no {option} option on this system (see its man page)"
        # the programs they run
        if os.path.basename(program) == "xargs":
            commands.append(args[end:])
        if os.path.basename(program) == "find":
            # its tests (-type, -printf) follow the paths, as words on its page
            i = end
            while i < len(args):
                word, i = args[i], i + 1
                if word in {"-exec", "-execdir", "-ok", "-okdir"}:
                    # problem() turned \; into _
                    stop = next(
                        (k for k in range(i, len(args)) if args[k] in {"_", "+"}),
                        len(args),
                    )
                    commands.append(args[i:stop])
                    i = stop + 1
                elif (
                    page
                    and re.fullmatch(r"-[a-z]+", word)
                    and not re.search(rf"(?<![\w-]){word}(?![\w-])", page)
                ):
                    return f"find has no {word} test on this system (see its man page)"
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

    def choose(self, query: str) -> list[str]:
        """Commands for the task, best first: the model suggests, the OS confirms."""
        answer = self.ask(
            "You are a CLI assistant choosing which command-line tools to use for a task. "
            "Your answer will be parsed by a program, so follow the output format exactly.\n\n"
            f"<environment>\n{self.env}\n</environment>\n\n"
            f"<task>\n{query}\n</task>\n\n"
            "List up to 3 programs that could perform this task on this system, best choice first. "
            "Output only the program names, one per line, with no numbering, bullets, backticks, or other text.",
            # some models repeat the last name until the context runs out
            max_tokens=60,
        )
        # one name per line or comma: "1. `ifconfig` - shows ..." -> ifconfig
        names = []
        for item in re.split(r"[\n,]", answer):
            name = next(iter(re.findall(r"[A-Za-z][\w.+-]*", item)), None)
            if name and name not in names and shutil.which(name):
                names.append(name)
        return names[:2]

    def generate(self, query: str) -> str:
        """Best command for the query; raises RuntimeError if none passes checks."""
        prompt = (
            "You are a CLI assistant generating shell commands that will be run directly on the user's machine. "
            "Use the reference below for this system's version of the tool, which may differ from GNU/Linux behavior, "
            "then follow the rules to write the command for the task.\n\n"
        )
        # tags mark where each part ends, so a man page can't read as instructions
        prompt += f"<environment>\n{self.env}\n</environment>\n"
        # a thinking model works out the platform's flags itself; the extra
        # round trip and man page only slow it down (evals: 49/50 vs 48/50)
        # best last, nearest the rules and task
        for chosen in [] if self.thinking else reversed(self.choose(query)):
            ref = reference(chosen, query)
            prompt += f"\n<reference>\n{ref}\n</reference>\n"
        prompt += (
            f"\n<rules>\nWrite one {os.path.basename(SHELL)} command for this system. "
            "Use real paths, never placeholders like /path/to; if the task names no location, use the current directory (.). "
            # small models chain programs they don't need, and break the chain (evals)
            "Prefer a single program; use a pipeline or && only when one program can't do the task. "
            # small models skip what they don't write down (evals)
            "First list the steps, and check each option you use exists in this system's version of the program. "
            "Then give the command in a single code block, the only one in your reply.\n</rules>\n"
            f"\n<task>\n{query}\n</task>\n"
        )

        attempt = prompt
        for _ in range(RETRIES + 1):
            command = clean(self.ask(attempt))
            error = problem(command)
            if error is None:
                return command
            attempt = f"{prompt}\nThe command `{command}` fails: {error}\nWrite a corrected command.\n"
        raise RuntimeError(f"no working command found (last: `{command}`: {error})")
