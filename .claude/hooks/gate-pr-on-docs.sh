#!/usr/bin/env bash
# PreToolUse guard - a pull request cannot open while the living documents are
# red. Matched on the Bash tool (see .claude/settings.json), so it SELF-SCOPES to
# `gh pr create` and leaves every other command alone.
#
# Why a hook and not a skill instruction: the board said "not a diary" on its
# line 9 and became one; the brief's contract said "rewritten in place" and it
# was patched across five families. A rule a session can skip is a wish. The
# two document gates below are the same ones CI runs, so this only moves the
# failure earlier - to before the PR exists.
#
# Deny, don't fix: exit 2 blocks the call and feeds the reason back to the agent.
payload="$(cat)"

if ! printf '%s' "$payload" | grep -qiE 'gh[[:space:]]+pr[[:space:]]+create\b'; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
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
