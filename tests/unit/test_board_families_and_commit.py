"""build_status_board.py: the families block from the ledger (#229), the brief's
Commit stamp and the lane's family pin (the sixteenth report, 8 October 2026)."""
import build_status_board as bsb

LEDGER = {
    "families": {
        "F2-b": {"label": "second | with a pipe", "decisions_ref": "9.44, 9.45", "from_launch": "20260818T190000"},
        "F1-a": {"label": "first", "decisions_ref": "9.42", "from_launch": "20260816T000000", "readings": "none"},
    },
    "overrides": {"aborted_x": {"family": "F1-a", "note": "n"}, "aborted_y": {"family": None, "note": "m"}},
}


def test_families_block_renders_every_key_oldest_first_with_its_record():
    out = bsb.render_families(LEDGER)
    rows = [l for l in out.splitlines() if l.startswith("| `F")]
    assert [r.split("`")[1] for r in rows] == ["F1-a", "F2-b"]
    assert "| §9.44, §9.45 |" in rows[1] and "second / with a pipe" in rows[1]
    assert "2 families" in out and "newest is `F2-b`" in out
    assert "`readings: none`" in out and "`F1-a`" in out.split("Marked")[1]
    assert "`aborted_x` → `F1-a`" in out and "`aborted_y` → unattributed" in out


def test_commit_stamp_replaces_a_placeholder_and_a_sha():
    head = "**Written:** x · **Open family:** `F39-x` · **Commit:** this handoff's\n*A pointer*\n"
    assert bsb.stamp_commit(head, "e25deff2") == "**Written:** x · **Open family:** `F39-x` · **Commit:** `e25deff2`\n*A pointer*\n"
    assert bsb.stamp_commit(head.replace("this handoff's", "`0123abcd`"), "e25deff2").count("`e25deff2`") == 1
    assert bsb.stamp_commit(head, None) == head
    assert bsb.stamp_commit("no header\n", "e25deff2") == "no header\n"


def test_head_sha_is_hex_or_none():
    sha = bsb.head_sha()
    assert sha is None or (len(sha) == 8 and all(c in "0123456789abcdef" for c in sha))
