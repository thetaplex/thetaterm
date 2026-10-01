# Thetaterm documentation

Thetaterm turns a plain-language request into one shell command that fits
your system, shows it to you, and runs it if you agree.

## Who this is for

- **Users** who run commands in a terminal on macOS or Linux and want help
  writing them. You don't need to know Python.
- **Contributors** who want to change Thetaterm or measure how well models do.
  Read [CONTRIBUTING.md](../CONTRIBUTING.md) first.

## How it's organised

Each page does one job, following [Diátaxis](https://diataxis.fr/):

| If you want to… | Read |
|---|---|
| learn by doing, from nothing | [Tutorial: your first command](tutorials/first-command.md) |
| use a server other than Ollama | [How to use another model server](how-to/use-another-model-server.md) |
| measure models against the test queries | [How to run the evals](how-to/run-evals.md) |
| look up an option, setting or exit status | [Command-line reference](reference/cli.md) |
| find out what a message means and what to do | [Messages](reference/messages.md) |
| check what a term means | [Glossary](reference/glossary.md) |
| understand how a command is made | [How it works](explanation/how-it-works.md) |
| understand what is and isn't checked | [Safety model](explanation/safety.md) |
| know why it was built this way | [Architecture decision records](adr/) |

## Conventions

- `Monospace` is something you type or something Thetaterm prints.
- `$ ` at the start of a line is the command Thetaterm proposes. Don't type it.
- Warnings come before the step they apply to, marked **Warning**.
- Dates follow ISO 8601 (`YYYY-MM-DD`).
- Terms are used as defined in the [glossary](reference/glossary.md).

## Standards

These pages are structured along the lines of ISO/IEC/IEEE 26514 (information
for users). That means separate conceptual, task and reference information,
warnings placed before the hazard, documented messages with recovery actions,
and a glossary. They haven't been formally assessed for conformance.

## Feedback

If a page is wrong or unclear, open an
[issue](https://github.com/thetaplex/thetaterm/issues) naming the page.
