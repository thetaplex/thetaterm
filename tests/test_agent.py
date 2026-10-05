import io
import json
import re
import shutil
import urllib.error
import urllib.request
from importlib.resources import files
from types import SimpleNamespace

import pytest

from thetaterm import agent
from thetaterm.agent import (
    MAX_NOTE_CHARS,
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


@pytest.mark.skipif(not shutil.which("zsh"), reason="needs zsh")
def test_problem_accepts_functions_autoloaded_by_the_command(monkeypatch):
    monkeypatch.setattr("thetaterm.agent.SHELL", shutil.which("zsh"))
    assert problem("autoload -Uz zmv && zmv '(*).jpeg' '$1.jpg'") is None
    assert "not found" in problem("zmv '(*).jpeg' '$1.jpg'")


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
    # the review's misses: home or previous directory, other variables, disks,
    # paths glued to a short option
    for command in (
        "cd && rm -rf *",
        "cd; ls",
        "cd - && ls",
        "popd",
        "cp x $OLDPWD",
        "rm -rf $TMPDIR/*",
        'cp x "${XDG_CONFIG_HOME}/y"',
        "dd if=x.iso of=/dev/disk4 bs=4m",
        "tar -xf a.tar -C/tmp",
        "git -C.. status",
    ):
        assert outside(command) is not None, command
    # the command's own variables, quoted awk fields and harmless devices pass
    for command in (
        "cd src && ls",
        'for f in *.txt; do mv "$f" "$f.bak"; done',
        "ls | while read -r name; do echo $name; done",
        "n=3; head -n $n notes.txt",
        "awk '{print $NF}' notes.txt",
        "ps -u $USER",
        "head -c 10 /dev/urandom > key.bin",
    ):
        assert outside(command) is None, command


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


def test_reference_puts_the_note_first_within_the_same_budget(monkeypatch):
    page = "\n\n".join(f"     -{c}  search {'x' * 900}" for c in "abcdef")
    monkeypatch.setattr(agent, "sh", lambda args: SimpleNamespace(stdout=page))
    monkeypatch.setattr(agent, "note", lambda command: "Fields split on spaces.")
    out = agent.reference("awk", "search")
    assert out.startswith("Notes:\nFields split on spaces.\n\n")
    assert "-a  search" in out
    assert len(out) <= MAX_REFERENCE_CHARS


def test_reference_without_a_man_page_is_just_the_note(monkeypatch):
    monkeypatch.setattr(agent, "sh", lambda args: SimpleNamespace(stdout=""))
    assert agent.reference("awk", "q").startswith("Notes:\n")
    assert agent.reference("no_such_command_xyz", "q") == ""


def test_shipped_notes_are_short_facts_not_examples():
    notes = list((files("thetaterm") / "notes").iterdir())
    assert notes
    for path in notes:
        assert path.name.endswith(".md")
        text = path.read_text().strip()
        assert 0 < len(text) <= MAX_NOTE_CHARS, path.name
        # an example command is an answer the model copies (ADR 0006)
        program = path.name.removesuffix(".md")
        assert not re.search(rf"\b{program}\s+-|[|`]|'\{{", text), path.name


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


def test_ask_turns_unexpected_replies_into_runtime_errors(monkeypatch):
    agent = Agent.__new__(Agent)
    agent.model, agent.url, agent.headers = "m", "http://x/chat/completions", {}
    agent.thinking, agent.thinking_off = False, {}
    for body in (b"<html>", b'{"error": "overloaded"}', b'{"choices": []}', b"[]"):
        monkeypatch.setattr(
            urllib.request,
            "urlopen",
            lambda request, timeout, body=body: io.BytesIO(body),
        )
        with pytest.raises(RuntimeError):
            agent.ask("hi")


def test_base_url_must_be_http_or_https():
    for url in ("file:///etc", "ftp://example.com", "localhost:11434"):
        with pytest.raises(ValueError):
            Agent("m", url)


def test_choose_takes_the_installed_suggestions():
    agent = Agent("m", "http://localhost")
    agent.ask = lambda prompt, max_tokens=None: (
        "1. `ip` - Linux\n2. definitely_not_xyz, ls\n3. cat\n4. ls\n5. echo"
    )
    expected = (["ip"] if shutil.which("ip") else []) + ["ls", "cat", "echo"]
    assert agent.choose("show the IP addresses of this machine") == expected[:2]
    agent.ask = lambda prompt, max_tokens=None: "definitely_not_xyz"
    assert agent.choose("anything") == []


def test_thinking_skips_suggestions_and_man_page():
    agent = Agent("m", "http://localhost", thinking=True)
    prompts = []
    agent.ask = lambda prompt, max_tokens=None: prompts.append(prompt) or "ls -la"
    assert agent.generate("list files") == "ls -la"
    assert len(prompts) == 1 and "<reference>" not in prompts[0]
