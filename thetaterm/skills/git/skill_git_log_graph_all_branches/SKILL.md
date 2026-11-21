---
name: skill_git_log_graph_all_branches
description: Build git log graph commands that include every branch, not only the current one.
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [graph, all branches, one line per commit, commit history, branch tree, git log, every branch]
  programs: [git]
---

# Domain Knowledge
- `git log` shows only commits reachable from HEAD (the current branch) by default.
- `--all` adds every ref: all local branches, remote branches and tags.
- `--graph` draws the ASCII branch/merge tree.
- `--oneline` puts each commit on one line (short hash and subject).
- `--decorate` shows branch names next to commits. It is optional.
- git behaves the same on BSD/macOS and GNU, so you need no OS-specific flags.

# Step-by-Step
1. Start with `git log`.
2. Map each phrase in the query to a flag: "graph"/"tree" → `--graph`; "all/every branch(es)" → `--all`; "one line per commit"/"compact" → `--oneline`.
3. Before you answer, check that every phrase has its flag. If one is missing, add it.
4. Output: `git log --graph --all --oneline`. Add `--decorate` only if the query asks for branch names.

# Feedback / Lessons
- Rule: If the query says "all branches", the command must contain `--all`.
  Why: Without `--all`, git only shows the current branch, so the student's `git log --graph --oneline` left out the other branches.
- Rule: Turn every scope word ("all", "every", "remote", "tags") into its own flag.
  Why: When a scope word is dropped, the command still runs but answers a narrower question than the user asked.
