# Safety model

Thetaterm runs commands a language model writes. Models make mistakes, and a
wrong shell command can delete or overwrite files. This page explains what
protects you, and where that protection stops.

## You are the safeguard

The main protection is you reading the command before you answer. Thetaterm
always shows the full command and, unless you pass `-y`, waits for your
answer. Nothing else on this page replaces that.

## What the checks do

Before you see a command, Thetaterm checks that it's valid shell syntax and
that every program it calls is installed. These checks exist to catch commands
that can't work, so the model can try again. **They don't judge whether a
command is safe.** `rm -rf .` passes them.

## The outside-the-current-directory guard

Most requests are about the directory you're in. A command that reaches
further, through `sudo`, a variable such as `$HOME`, a bare `cd` or `cd -`,
or a path that's absolute, under `~` or contains `..`, is more likely to be a mistake and more likely to do damage. So
Thetaterm:

- shows it in red with the reason
- makes the default answer no
- asks even if you passed `-y`

The guard only reads the words of the command, so it's a pattern match, not a
sandbox. It catches the model's honest mistakes, such as writing `/tmp/out`
when you meant `./out`. It won't catch a command built to hide where it reaches,
for example a path assembled at run time by `$(…)`. The full list of patterns
is in [Messages](../reference/messages.md). Once a command runs, it has all the
permissions you have.

Nothing runs before you answer the prompt. Thetaterm reads man pages to help
the model, but it never runs a program to read its docs
([ADR 0005](../adr/0005-never-run-a-program-to-read-its-docs.md)). See
[ADR 0002](../adr/0002-check-outside-paths-by-pattern-not-sandbox.md) for why
it's built this way.

## `-y`

`-y` removes the question for commands that stay inside the current
directory. Use it only where a wrong command can't cost you anything, such as a
throwaway directory or a container. In interactive mode it applies to every
request you type.

## What leaves your machine

Each request sends the model server your request, the system description and
the man page excerpt. With the default Ollama setup, the server is on your
machine and nothing leaves it. With a hosted API, all of that goes to the
provider. File contents and command output are never sent.

The API key is only sent to `THETATERM_BASE_URL`. Settings are only read from
your own config directory, never from a `.env` in the directory you're working
in. That stops a cloned repository from redirecting your key to its own server.
See [ADR 0003](../adr/0003-read-config-only-from-the-user-config-dir.md).

## Reporting a problem

If the guard misses a plain path, or a command runs without asking when it
should have, report it privately as described in
[SECURITY.md](../../SECURITY.md).
