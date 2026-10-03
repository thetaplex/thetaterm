# How to run the evals

The evals ask models for commands and check the answers, so you can compare
models or see whether a change helped. Commands are generated but never run.

## Before you start

- A development setup: see [CONTRIBUTING.md](../../CONTRIBUTING.md).
- [Node.js](https://nodejs.org/). `just` runs promptfoo through `npx`.
- The models listed in `evals/promptfoo/local.yaml`, pulled in Ollama
  (`ollama pull <model>`).

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
| `evals/promptfoo/provider.py` | runs thetaterm for promptfoo and traces each step |
