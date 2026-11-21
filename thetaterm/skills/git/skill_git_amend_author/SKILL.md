---
name: skill_git_amend_author
description: Change the author or message of the last commit with git commit --amend --author="Name <email>", not with env vars or --reset-author.
metadata:
  category: git
  base_model: gemma4:e4b-mlx
  trigger_keywords: [change the author, commit author, amend, last commit, fix author, rewrite commit, edit commit message]
  programs: [git]
---

# Domain Knowledge
- git works the same on macOS and Linux, so BSD vs GNU makes no difference here.
- `git commit --amend` rewrites only the last commit (`HEAD`).
- To set an author, use `--author="Name <email>"`. It is one quoted argument: the name, a space, then the email in angle brackets.
- `--reset-author` sets the author to your own configured identity, not the one in the request.
- `--no-edit` keeps the old message. `-m "text"` replaces it.
- Commits older than `HEAD` need `git rebase -i`, because amend can't reach them.

# Step-by-Step
1. Start with `git commit --amend`.
2. For a new author, add `--author="Name <email>"`. Copy the name and email exactly as the request gives them.
3. To keep the message, add `--no-edit`. For a new message, add `-m "text"`.
4. Check the result: one git command, no `VAR=value` prefix, no `--reset-author`.

# Feedback / Lessons
- Rule: When asked to "change the author", write `git commit --amend --author="Name <email>" --no-edit`.
  Why: `GIT_AUTHOR_*` env vars plus `--reset-author` is an indirect hack that leaves out the `--author` flag.
- Rule: Never set git identity through environment variables when a flag exists.
  Why: The flag is explicit and works the same in every shell.
