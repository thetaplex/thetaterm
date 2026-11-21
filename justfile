# Loads ./.env if present, for local settings (see .env.example)
set dotenv-load

promptfoo := "uv run npx promptfoo@0.123.1"

default:
    @just --list

setup:
    uv sync --locked --all-extras

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

# Run evals/promptfoo/tests/<tests>.yaml on each enabled configs/<config>.yaml model, one at a time so each loads once.
# checks: static (each query's assertions), judge (the enabled judges in configs/judges.yaml) or both
# tests=--all runs every tests/*.yaml, one after another; `just eval --all [checks]` uses the local config
eval config="local" tests="tests" checks="static":
    #!/usr/bin/env bash
    config={{config}} tests={{tests}} checks={{checks}}
    # `just eval --all judge`: the words after --all shift one place left
    if [ "$config" = --all ]; then
        [ "$tests" != tests ] && checks=$tests
        config=local tests=--all
    fi
    [ "$tests" = --all ] && tests=$(cd evals/promptfoo/tests && ls *.yaml | sed 's/\.yaml$//')
    # promptfoo runs one empty test instead of failing on a missing file
    for f in evals/promptfoo/configs/$config.yaml $(printf 'evals/promptfoo/tests/%s.yaml ' $tests); do
        [ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }
    done
    status=0
    for t in $tests; do
        run=$(mktemp -d)/run.yaml
        uv run python evals/promptfoo/checks.py "$config" "$t" "$checks" > "$run" || exit 1
        # only the enabled models are in the built config
        for model in $(sed -n 's/^  label: //p' "$run"); do
            {{promptfoo}} eval -c "$run" --filter-providers "^${model//./\\.}\$" || status=$?
        done
    done
    exit $status

# Browse eval results, including a run in progress
view:
    {{promptfoo}} view

# Run ThetaTerm UpSkill Ralph Loop (configurable teacher -> local student)
upskill tests="regression" *args="":
    uv run python evals/upskill.py --tests {{tests}} {{args}}

# Triage, sanitize, and brew skills from ~/.config/thetaterm/failures.jsonl
upskill-failures *args="":
    uv run python evals/upskill.py --from-failures {{args}}
