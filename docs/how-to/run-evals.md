# How to run the evals

The evals ask models for commands and check the answers, so you can compare
models or see whether a change helped. Commands are generated but never run.

## Before you start

- A development setup: see [CONTRIBUTING.md](../../CONTRIBUTING.md).
- [Node.js](https://nodejs.org/). `just` runs promptfoo through `npx`.
- The models enabled in `evals/promptfoo/configs/local.yaml`, pulled in Ollama
  (`ollama pull <model>`).
- For runs with an OpenRouter judge: an [OpenRouter](https://openrouter.ai/)
  key in `.env` at the repo root, `OPENROUTER_API_KEY=...`.

## Run them

Run every query against every local model:

```bash
just eval
```

Each enabled model runs on its own, one after another, so only one is loaded
at a time. To skip a model, set `enabled: false` on it in its config. The command exits non-zero if any model fails any query.

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
just eval local tests judge     # only the judges
just eval local tests both      # the assertions and every judge must pass
```

Assertions are regexes: fast, free and offline, but they pass a command that
looks right and uses an option the program doesn't have. A judge is a model
that reads the task and the command and decides. It catches those, but it
costs money and can be wrong too. When a judge and the assertions disagree in
a `both` run, check which one is right; often the regex needs fixing.

The judges are in `evals/promptfoo/configs/judges.yaml`, each with
`enabled: true` or `false`. Every enabled judge checks every answer, in
parallel, and shows as its own row in `just view`; an answer must pass all of
them. Only `sonnet` (`anthropic/claude-sonnet-5`) is enabled by default.

**Warning:** `judge` and `both` send the queries and generated commands to
each enabled judge's provider, OpenRouter for the judges listed today.

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
   `evals/promptfoo/tests/git.yaml`, or to `evals/promptfoo/tests/tests.yaml`
   if the area has no file. Follow the existing entries. `tests.yaml` keeps a sample
   of each area; copy the query there only if the sample needs it.
2. If an assertion depends on GNU or BSD tools, check `--version` in the
   assertion, as the `find`, `sed`, `ps` and `date` entries do.
3. If a model has failed it, copy it to `evals/promptfoo/tests/regression.yaml` too.
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
| `evals/promptfoo/configs/local.yaml` | local models, each enabled or not |
| `evals/promptfoo/configs/cloud.yaml` | Ollama Cloud models, each enabled or not |
| `evals/promptfoo/configs/judges.yaml` | the judges, each enabled or not, and what they check |
| `evals/promptfoo/tests/tests.yaml` | a sample of queries from every area, with their assertions |
| `evals/promptfoo/tests/regression.yaml` | queries some model has failed |
| `evals/promptfoo/tests/git.yaml` | all git queries: branches, rebases, stashes, conflicts, history |
| `evals/promptfoo/checks.py` | builds a run's config from the enabled models, the queries and the checks |
| `evals/promptfoo/provider.py` | runs thetaterm for promptfoo and traces each step |
