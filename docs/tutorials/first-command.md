# Tutorial: your first command

In this tutorial you install thetaterm, connect it to a local model, and use it
to list and inspect files. It takes about 10 minutes, plus the time to download
a 10 GB model.

You need a Mac or a Linux machine, a terminal, and about 15 GB of free disk
space.

## 1. Install a model server

thetaterm needs a model to talk to. You'll use Ollama, which runs models on
your own machine, so nothing you type leaves it.

Install Ollama from [ollama.com/download](https://ollama.com/download), then
download the default model:

```bash
ollama pull gemma4:e4b
```

When it finishes, `ollama list` shows `gemma4:e4b`.

## 2. Install thetaterm

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you
don't have it, then:

```bash
uv tool install thetaterm
```

Check it's on your path:

```bash
tterm --help
```

You should see a list of options starting with `--query`.

## 3. Ask for a command

Make a practice directory, so nothing you run touches your real files:

```bash
mkdir -p ~/tterm-practice && cd ~/tterm-practice
touch notes.txt todo.txt && head -c 50000 /dev/urandom > big.bin
```

Now ask thetaterm:

```bash
tterm -q "list files in this directory, largest first"
```

After a few seconds it prints a command and asks before running it:

```
$ ls -lS .
Run it? [Y/n]:
```

Your command may differ a little. That's expected, since the model writes it
for your system. Press Enter to run it. `big.bin` should be first.

## 4. Say no

Ask for something that reaches outside this directory:

```bash
tterm -q "show disk usage of my home directory"
```

```
$ du -sh ~
leaves the current directory: home path ~
Run it? [y/N]:
```

The command is in red, the default has changed to **N**, and thetaterm tells
you why. Press Enter to decline. Nothing runs.

## 5. Use interactive mode

Run `tterm` with no options:

```bash
tterm
```

```
thetaterm · gemma4:e4b · macOS 26.6.2, BSD userland, zsh shell
Describe what you want. Ctrl-D to exit.

>
```

The first line shows what thetaterm detected about your machine. Type a
request at the `>` prompt, for example `count the lines in every txt file`,
and answer the question as before. Press Ctrl-D when you're done.

## What you've learnt

You've installed thetaterm, used it in one-shot and interactive mode, and seen
it ask for extra care before a command reaches outside the current directory.

Next:

- [Command-line reference](../reference/cli.md) for every option and setting
- [Safety model](../explanation/safety.md) for what thetaterm checks, and what it doesn't
- Remove the practice directory with `rm -r ~/tterm-practice`
