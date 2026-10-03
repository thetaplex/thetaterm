# Loads ./.env if present, for local settings (see .env.example)
set dotenv-load

promptfoo := "uv run npx promptfoo@0.123.1"

default:
    @just --list

setup:
    uv sync --locked

test:
    uv run pytest

lint:
    uv run ruff check

fmt:
    uv run ruff format

check: lint test
    uv run ruff format --check

# "$@" keeps quoted arguments whole: just run -q "find big files"
[positional-arguments]
run *args:
    uv run tterm "$@"

# Run evals/promptfoo/<tests>.yaml on each <config>.yaml model, one at a time so each loads once.
# checks: static (each query's assertions), judge (a model on OpenRouter) or both
eval config="local" tests="tests" checks="static":
    #!/usr/bin/env bash
    # promptfoo runs one empty test instead of failing on a missing file
    for f in evals/promptfoo/{{config}}.yaml evals/promptfoo/{{tests}}.yaml; do
        [ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }
    done
    run=$(mktemp -d)/run.yaml
    uv run python evals/promptfoo/checks.py {{config}} {{tests}} {{checks}} > "$run" || exit 1
    status=0
    for model in $(grep -oE 'label: [^,} ]+' evals/promptfoo/{{config}}.yaml | cut -d' ' -f2); do
        {{promptfoo}} eval -c "$run" --filter-providers "^${model//./\\.}\$" || status=$?
    done
    exit $status

# Browse eval results, including a run in progress
view:
    {{promptfoo}} view
