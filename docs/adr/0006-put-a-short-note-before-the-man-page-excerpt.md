# 6. Put a short note before the man page excerpt

Date: 2026-10-01

## Status

Accepted

Amends [ADR 0001](0001-read-docs-from-the-installed-system.md)

## Context

The man page excerpt (ADR 0001) keeps the entries that share the most rare
words with the request. A fact the model needs can sit in a paragraph that
shares none. Asked to "print the second column of data.csv", `gemma4:26b`
wrote `awk '{print $2}' ./data.csv`. The paragraph saying `awk` splits fields
on white space was cut, because it says "fields", not "column".

Options considered:

- **Better ranking**, such as synonyms. It helps only where someone thought of
  the synonym, and a fact like "CSV needs `-F,`" is on no man page at all.
- **Remember past commands that worked** and show similar ones as examples. It
  needs storage, matching and a policy for wrong commands that were accepted.
- **Learn from errors**, and have the command check reject what failed before.
  A command that runs and prints the wrong column raises no error.
- **A short hand-written note per program, put before the excerpt.**

## Decision

thetaterm ships notes in `thetaterm/notes/<program>.md`. When a program is
chosen, its note goes first in the reference, and the man page excerpt gets
the rest of the same 3,500-character budget. A note is at most 600 characters.

Notes state general facts about the program, never the answer to an eval
query, or the evals would measure the notes and not the model. One note covers
all systems: it names GNU or BSD where they differ, and the prompt already
says which one the system has.

There are no personal notes.

## Consequences

- A failure found in the evals can be fixed with a few lines of text, reviewed
  in a pull request like any other change.
- Notes are not read from the installed system, which ADR 0001 rejected for
  documentation. They add to the installed man page; they don't replace it.
- With `--think`, there is no reference, so there are no notes either.
- A wrong note misleads every model, on every system. Notes need the same care
  as code.
