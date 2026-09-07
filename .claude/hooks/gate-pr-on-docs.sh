#!/usr/bin/env bash
# PreToolUse guard - a pull request cannot open while the living documents are
# red.
#
# TWO PATHS OPEN A PR, AND BOTH ARE GATED. This hook is registered on the Bash
# tool AND on mcp__github__create_pull_request / update_pull_request (see
# .claude/settings.json), because until 7 September 2026 it matched only
# `gh pr create` on Bash - so the MCP path, which .claude/settings.json already
# registered for the session-link hook, opened a pull request entirely ungated.
# It still SELF-SCOPES: on Bash it leaves every command that is not `gh pr
# create`/`gh pr edit` alone.
#
# Why a hook and not a skill instruction: the board said "not a diary" on its
# line 9 and became one; the brief's contract said "rewritten in place" and it
# was patched across five families. A rule a session can skip is a wish. The
# two document gates below are the same ones CI runs, so this only moves the
# failure earlier - to before the PR exists.
#
# Deny, don't fix: exit 2 blocks the call and feeds the reason back to the agent.
payload="$(cat)"

# `gh pr create` / `gh pr edit` on the Bash path, or either PR tool on the MCP
# path. Anything else is none of this hook's business.
if ! printf '%s' "$payload" | grep -qiE \
     'gh[[:space:]]+pr[[:space:]]+(create|edit)\b|mcp__github__(create|update)_pull_request'; then
  exit 0
fi

# FAIL CLOSED. This used to be `|| exit 0`: if the project directory could not
# be entered - an unset CLAUDE_PROJECT_DIR, a renamed checkout - the hook
# silently allowed the PR, which is the one outcome it exists to prevent.
if ! cd "${CLAUDE_PROJECT_DIR:-.}"; then
  echo "Blocked: the document gate could not enter CLAUDE_PROJECT_DIR (${CLAUDE_PROJECT_DIR:-.}), so it cannot tell whether the living documents are current. Run the checks by hand, or fix the path, before opening a PR." >&2
  exit 2
fi
if [ ! -f tests/check_doc_currency.py ]; then
  echo "Blocked: the document gate is not in the repository it was pointed at (no tests/check_doc_currency.py under ${CLAUDE_PROJECT_DIR:-.}), so it cannot verify anything." >&2
  exit 2
fi
out_currency="$(python tests/check_doc_currency.py --strict 2>&1)"; rc1=$?
out_shape="$(python tests/check_doc_shape.py --strict 2>&1)"; rc2=$?
out_board="$(python src/analyse/build_status_board.py --check 2>&1)"; rc3=$?

if [ "$rc1" -ne 0 ] || [ "$rc2" -ne 0 ] || [ "$rc3" -ne 0 ]; then
  {
    echo "Blocked: the living documents are not current, so this PR cannot open yet."
    [ "$rc1" -ne 0 ] && { echo "--- check_doc_currency.py --strict"; printf '%s\n' "$out_currency" | tail -12; }
    [ "$rc2" -ne 0 ] && { echo "--- check_doc_shape.py --strict"; printf '%s\n' "$out_shape" | tail -12; }
    [ "$rc3" -ne 0 ] && { echo "--- build_status_board.py --check (run it without --check to regenerate)"; printf '%s\n' "$out_board" | tail -6; }
    echo "Fix the documents (or regenerate the board), commit, then re-run gh pr create."
  } >&2
  exit 2
fi
exit 0
