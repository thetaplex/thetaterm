# Glossary

**Request**: What you ask for, in plain language, with `-q` or at the `>` prompt.
_Avoid:_ prompt (that's what Thetaterm sends to the model).

**Command**: The one shell command line Thetaterm proposes for a request. It may contain
pipes and `&&`.

**Prompt**: The text Thetaterm sends to the model. It holds the system description, the
reference and the request.

**System description**: One line naming your OS, userland and shell, for example
`macOS 26.6.2, BSD userland, zsh shell`. It's shown in interactive mode.

**Userland**: The family of the basic command-line tools (`ls`, `find`, `sed`, …) on your
system: GNU coreutils (most Linux), BSD (macOS) or BusyBox (Alpine, embedded).
Their options differ.

**Chosen command**: The program the request is built around, such as `find`. The model suggests
up to five, and Thetaterm takes the first one installed.

**Reference**: The parts of the chosen command's man page that best
match the request, put in the prompt.
_Avoid:_ context, docs.

**Checks**: What a command must pass before you're asked to run it: valid shell syntax,
and every program it calls is installed.
_Avoid:_ validation, safety check (the checks don't judge safety).

**Outside the current directory**: A command that names `sudo`, a variable, a bare `cd`, `cd -` or `popd`, or a
path that's absolute, under `~`, or contains `..`. These always ask, defaulting to no.

**Model server**: The program serving the model over an OpenAI-compatible API, such as Ollama.
_Avoid:_ backend, provider.

**Thinking**: Letting the model reason before it answers, turned on with `--think`.
