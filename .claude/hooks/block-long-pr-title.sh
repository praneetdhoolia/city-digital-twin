#!/usr/bin/env bash
# PreToolUse guard - refuse a `gh pr create` / `gh pr edit` whose --title runs past
# the convention's cap (CLAUDE.md: `P<phase>: <concise plain-English summary>`,
# at most about 72 characters).
#
# Why a hook and not advice: the sixteenth project report counted 61 of 94 merged
# titles over the cap with nothing refusing one; a title that long is a summary
# that was not written. The cap is the kernel's own (72 columns in `git log`), so
# the reader of the history sees the whole summary on one line.
#
# Matched on the Bash tool, so it must SELF-SCOPE: act only on gh PR-writing
# commands that carry a --title, and leave every other command alone. Deny, don't
# trim: exit 2 feeds the reason back to the agent, who rewrites the title.
payload="$(cat)"

if ! printf '%s' "$payload" | grep -qiE 'gh[[:space:]]+pr[[:space:]]+(create|edit)\b'; then
  exit 0
fi

# the title's text: --title "..." / --title '...' / --title=... / -t "...". The
# payload is the tool call's JSON, so a quote inside the command arrives as \" -
# the optional backslash before the opening quote, and the stop at the first
# quote or backslash, read both the raw and the escaped form.
title="$(printf '%s' "$payload" | sed -nE 's/.*(--title|-t)(=|[[:space:]]+)\\?["'"'"']([^"'"'"'\\]*).*/\3/p' | head -n 1)"
[ -z "$title" ] && exit 0

# a title passed through a shell variable or a file cannot be measured here; the
# CI workflow (commit-trailers.yml) measures the landed title as the second line.
n="${#title}"
if [ "$n" -gt 72 ]; then
  echo "Blocked: this PR title is $n characters; the convention caps it at about 72 (CLAUDE.md, Git: 'P<phase>: <concise plain-English summary>'). Shorten the title; issue refs go in parentheses at the end and detail in the body." >&2
  exit 2
fi
exit 0
