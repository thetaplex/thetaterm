import io
import json
import shutil
import urllib.error
import urllib.request

from thetaterm.agent import (
    MAX_REFERENCE_CHARS,
    Agent,
    clean,
    entries,
    excerpt,
    keywords,
    outside,
    problem,
    user_shell,
)


def test_keywords_drop_stopwords_and_plurals():
    assert keywords("Show all the files in my home") == ["file", "home"]


def test_clean_strips_model_wrapping():
    assert clean("```bash\n$ ls -la\n```") == "ls -la"
    assert clean("`du -sh .`") == "du -sh ."
    assert clean("\n\nfind . -name '*.py'\nThis finds files") == "find . -name '*.py'"
    assert clean("Command: `wc -l < README.md`") == "wc -l < README.md"
    # granite: prose, then the fenced command, then an explanation
    reply = (
        "To do this, run:\n\n```bash\nkill $(lsof -ti :3000)\n```\n\nExplanation: ..."
    )
    assert clean(reply) == "kill $(lsof -ti :3000)"


def test_user_shell_follows_login_shell_if_it_parses_like_sh(monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/sh")
    assert user_shell() == "/bin/sh"
    bash = shutil.which("bash") or "/bin/sh"
    for login in ("/usr/bin/fish", "/no/such/zsh", ""):
        monkeypatch.setenv("SHELL", login)
        assert user_shell() == bash
    monkeypatch.delenv("SHELL")
    assert user_shell() == bash


def test_problem_catches_bad_commands():
    assert problem("ls -la | grep 'a|b' && echo ok") is None
    assert problem("FOO=1 sudo ls; (cd /tmp && pwd)") is None
    assert problem("find . ! -exec test -e {} \\; -print && ! false") is None
    assert problem("find . -exec grep -l x {} ';' -print") is None
    assert "not found" in problem("ls | definitely_not_a_command_xyz")
    assert problem("echo 'unterminated") is not None
    assert problem("") == "empty command"


def test_outside_flags_commands_leaving_cwd():
    assert outside("find . -name '*.log' 2>/dev/null | sort") is None
    assert outside("sed -i 's/a/b/' notes.txt && ls src/lib") is None
    assert outside("curl https://example.com -o page.html") is None
    assert outside("find / -name '*.log' -delete") is not None
    assert outside("rm -rf ~/logs") is not None
    assert outside("cp x ../y") is not None
    assert outside("tar -cf out.tar --directory=/etc .") is not None
    assert outside('echo "$HOME"') is not None
    assert outside("sudo ls") is not None


def test_excerpt_keeps_whole_entries_and_prefers_rare_words():
    head = "\n".join(f"HEAD {i}" for i in range(20))
    common = "\n\n".join(
        f"     -{c}      Treat the file as a file, {'x' * 900}." for c in "abcd"
    )
    page = (
        f"{head}\n\n{common}\n\n"
        "     -r, --recursive\n"
        "             Recursively search subdirectories\n"
        "             listed on the command line.\n"
        "  -q  quiet\n"
        "  -s  silent\n"
    )
    out = excerpt(page, "search files recursively")
    assert "HEAD 19" in out
    assert (
        "Recursively search subdirectories\n             listed on the command line."
        in out
    )
    assert "  -q  quiet" not in out  # option lines split without blank lines
    assert len(out) <= MAX_REFERENCE_CHARS


def test_entries_keep_an_options_indented_paragraphs():
    page = (
        "     -type t\n"
        "             True if the file is of the specified type:\n"
        "\n"
        "             l       symbolic link\n"
        "\n"
        "     -uid uname\n"
        "             True if the file belongs to uname.\n"
        "\n"
        "EXAMPLES\n"
        "\n"
        "     find . -type l\n"
    )
    assert [text.split()[0] for _, text in entries(page)] == [
        "-type",
        "-uid",
        "EXAMPLES",
        "find",
    ]
    assert "symbolic link" in entries(page)[0][1]


def test_ask_drops_reasoning_effort_if_server_rejects_it(monkeypatch):
    sent = []

    def urlopen(request, timeout):
        body = json.loads(request.data)
        sent.append(body)
        if "reasoning_effort" in body:
            raise urllib.error.HTTPError(
                request.full_url, 400, "", {}, io.BytesIO(b"unknown reasoning_effort")
            )
        return io.BytesIO(b'{"choices": [{"message": {"content": "ls"}}]}')

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    agent = Agent.__new__(Agent)
    agent.model, agent.url, agent.headers = "m", "http://x/chat/completions", {}
    agent.thinking_off = {"reasoning_effort": "none"}
    assert agent.ask("hi") == "ls"
    assert agent.ask("hi") == "ls"  # remembered: no second rejected request
    assert ["reasoning_effort" in body for body in sent] == [True, False, False]


def test_choose_takes_the_first_installed_suggestion():
    agent = Agent("m", "http://localhost")
    agent.ask = lambda prompt, max_tokens=None: (
        "1. `ip` - Linux\n2. definitely_not_xyz, ls\n3. cat"
    )
    expected = "ip" if shutil.which("ip") else "ls"
    assert agent.choose("show the IP addresses of this machine") == expected
    agent.ask = lambda prompt, max_tokens=None: "definitely_not_xyz"
    assert agent.choose("anything") is None


def test_thinking_skips_suggestions_and_man_page():
    agent = Agent("m", "http://localhost", thinking=True)
    prompts = []
    agent.ask = lambda prompt, max_tokens=None: prompts.append(prompt) or "ls -la"
    assert agent.generate("list files") == "ls -la"
    assert len(prompts) == 1 and "Reference for" not in prompts[0]
