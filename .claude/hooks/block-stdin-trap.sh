#!/usr/bin/env bash
# PreToolUse guard - refuse a Bash command that feeds a program through stdin
# the harness cannot supply: a heredoc (`<<EOF`, `<<'EOF'`, `<<-EOF`) or a
# bare `python -` / `python3 -` reading its program from stdin.
#
# WHY. On this workstation a heredoc through the Bash tool breaks - the body
# is mangled or the command waits on a stdin that never closes - and a
# `python -` waits for a program that never arrives. Sessions kept rediscovering
# it by hand (the user's memory "Shell heredocs break": write scripts to the
# scratchpad and run the file). A rule a session can skip is a wish, so the
# rule is a hook.
#
# Matched (in .claude/settings.json) on the Bash tool, so it sees every Bash
# call and SELF-SCOPES: only the two stdin shapes are refused. `a << 2` (a
# shift) is not a heredoc - the delimiter must start with a letter or `_` -
# and `python -m`, `python -c`, `python script.py` are untouched. It greps the
# JSON payload, where a newline is the two characters `\n` and a double quote
# is `\"`, the same way the other Bash hooks here do.
#
# Deny, don't rewrite: exit 2 blocks the call and feeds the reason back.
payload="$(cat)"

heredoc='<<-?[[:space:]]*(\\?["'"'"'])?[A-Za-z_]'
py_stdin='(^|[^A-Za-z0-9_./-])python3?(\.exe)?[[:space:]]+-([[:space:]]|\\[nrt]|\\?"|[;&|)]|$)'

if printf '%s' "$payload" | grep -qE -- "$heredoc"; then
  why="a heredoc (<<)"
elif printf '%s' "$payload" | grep -qE -- "$py_stdin"; then
  why="a bare 'python -' reading its program from stdin"
else
  exit 0
fi
echo "Blocked: this command uses $why, which breaks under this harness. Write the script or the text to a file in the scratchpad with the Write tool, then run the file (python <path>.py, or cmd < <file>) - never a heredoc and never 'python -'." >&2
exit 2
