# How to run the evals

The evals ask models for commands and check the answers, so you can compare
models or see whether a change helped. Commands are generated but never run.

## Before you start

- A development setup: see [CONTRIBUTING.md](../../CONTRIBUTING.md).
- [Node.js](https://nodejs.org/). `just` runs promptfoo through `npx`.
- The models listed in `evals/promptfoo/local.yaml`, pulled in Ollama
  (`ollama pull <model>`).
- For judged runs only: an [OpenRouter](https://openrouter.ai/) key in
  `.env` at the repo root, `OPENROUTER_API_KEY=...`.

## Run them

Run every query against every local model:

```bash
just eval
```

Each model runs on its own, one after another, so only one is loaded at a
time. The command exits non-zero if any model fails any query.

Other runs:

```bash
just eval local regression    # only queries some model has failed before
just eval local git           # git through a regular development flow
just eval cloud               # Ollama Cloud models
```

**Warning:** `just eval cloud` sends the test prompts to Ollama Cloud. Run
`ollama signin` first.

## Choose the checks

Each run checks answers in one of three ways, given as the third argument:

```bash
just eval local tests static    # each query's own assertions (the default)
just eval local tests judge     # only a judge model
just eval local tests both      # the assertions and the judge must both pass
```

Assertions are regexes: fast, free and offline, but they pass a command that
looks right and uses an option the program doesn't have. The judge,
`anthropic/claude-sonnet-5` on OpenRouter, reads the task and the command and
decides. It catches those, but it costs money and can be wrong too. When the
two disagree in a `both` run, check which one is right; often the regex needs
fixing.

**Warning:** `judge` and `both` send the queries and generated commands to
OpenRouter.

## See the results

```bash
just view
```

This opens promptfoo's viewer, including any run still in progress. There's one
eval per model. Click 🔎 on a result to see every step: the model calls, the
man page excerpt and the checks. To keep a run as a file, download it from the
viewer.

## Add a query

1. Add an entry, with assertions on the command, to its area's file, such as
   `evals/promptfoo/git.yaml`, or to `evals/promptfoo/tests.yaml` if the
   area has no file. Follow the existing entries. `tests.yaml` keeps a sample
   of each area; copy the query there only if the sample needs it.
2. If an assertion depends on GNU or BSD tools, check `--version` in the
   assertion, as the `find`, `sed`, `ps` and `date` entries do.
3. If a model has failed it, copy it to `evals/promptfoo/regression.yaml` too.
4. Run `just eval` and check the new query passes or fails for the reason you
   expect.

## Fix a failure with a note

If a model fails because the man page excerpt left out a fact about the
program, add a note for it:

1. Write the fact in `thetaterm/notes/<program>.md`, in 600 characters or
   fewer. If GNU and BSD differ, say which is which.
2. Write facts, never an example command. "Fields are split on spaces and
   tabs; -F sets the separator" is a note. Any command line, even one unlike
   the query, is an example, and `just test` rejects it.
3. Run `just eval` and check the query now passes and nothing else fails.

See [ADR 0006](../adr/0006-put-a-short-note-before-the-man-page-excerpt.md).

## Files

| File | Holds |
|---|---|
| `evals/promptfoo/tests.yaml` | a sample of queries from every area, with their assertions |
| `evals/promptfoo/regression.yaml` | queries some model has failed |
| `evals/promptfoo/git.yaml` | all git queries: branches, rebases, stashes, conflicts, history |
| `evals/promptfoo/local.yaml` | local models |
| `evals/promptfoo/cloud.yaml` | Ollama Cloud models |
| `evals/promptfoo/judge.yaml` | the judge model and what it checks |
| `evals/promptfoo/checks.py` | builds a run's config from the models, queries and checks |
| `evals/promptfoo/provider.py` | runs thetaterm for promptfoo and traces each step |
