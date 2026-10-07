"""positions.py --check --stale and --second-homes (the sixteenth report, 8 October 2026).

A page three families behind the record was invisible to every check for a
month (light rail and ferry described F35 under F39); the figures the board
generates had seventeen hand-keyed homes. These pin the two readers.
"""
import positions

BOARD = """# STATUS
<!-- generated:scoreboard start -->
Read from `20260929T072135_250it_25pct` at **iteration 250** (family `F39-walk`, status `completed`, 25% sample, launched x, trips table). **A RESULT** - its `_run.json` says `ran_to_last_iteration` at iteration 250.
| 1 | car | 63.2999 | 58.3222 | +8.5% | ok | share |

Inside 10%: **car, motorbike**. Past the 20% stop bar: **ride, walk**.
<!-- generated:scoreboard end -->
<!-- generated:state start -->
| Input registry | **600 fields**, each with units |
| Data package | **968 files** in `data/MANIFEST.csv` |
<!-- generated:state end -->
The manifest holds **733 CC-BY / 220 ODbL** plus 15 bespoke files.
<!-- generated:lane start -->
1. **Run the treatment** - the control ran 27.9 h against a 27.7 h quote
<!-- generated:lane end -->
"""


def _page(tmp_path, name, read_through, measured):
    p = tmp_path / name
    p.write_text("# T\n\n**Updated:** x · **Record read through:** §9.%d · **Written against family:** `F39`\n\n"
                 "## What is built\n\n- a\n\n## What is measured — the cost\n\n%s\n\n## What is open\n\n- b\n\n## History\n\n- §9.1 — x\n"
                 % (read_through, measured), encoding="utf-8")
    return str(p)


def test_board_figures_are_read_from_the_generated_blocks():
    f = positions.board_figures(BOARD)
    assert f["result run"] == "20260929T072135_250it_25pct"
    assert f["N of 12"] == "2 of 12"
    assert f["registry fields"] == "600" and f["manifest files"] == "968"
    assert f["licence split"] == "733 CC-BY / 220 ODbL"
    assert f["wall hours"] == "27.9 h"


def test_the_newest_family_result_is_the_scoreboard_run_when_it_is_a_result():
    assert positions.newest_family_result_runs(BOARD, "F39-walk") == ["20260929T072135_250it_25pct"]
    assert positions.newest_family_result_runs(BOARD, "F40-other") == []
    assert positions.newest_family_result_runs(BOARD.replace("**A RESULT**", "**Not a result**"), "F39-walk") == []


def test_section_reads_a_heading_with_a_suffix():
    text = "## What is measured — what a run costs\n\n- line\n\n## What is open\n\n- other\n"
    assert "- line" in positions.section(text, "What is measured")
    assert "- other" not in positions.section(text, "What is measured")


def test_stale_stamp_and_missing_result_are_reported(tmp_path):
    fresh = _page(tmp_path, "fresh.md", 219, "- read on `20260929T072135_250it_25pct` (§9.219)")
    behind = _page(tmp_path, "behind.md", 177, "- read on `20260929T072135_250it_25pct` (§9.219)")
    unread = _page(tmp_path, "unread.md", 219, "- nothing new (§9.219)")
    rows = positions.stale_report([fresh, behind, unread], 220, "F39-walk", ["20260929T072135_250it_25pct"])
    assert rows == [
        ("behind.md", "STALE", "read through §9.177, 43 sections behind the record (cap %d)" % positions.STALE_SECTIONS),
        ("unread.md", "WARN", "What is measured names no result of F39-walk (20260929T072135_250it_25pct)"),
    ]


def test_second_homes_lists_every_restatement_with_its_line(tmp_path):
    page = tmp_path / "p.md"
    page.write_text("- the control `20260929T072135_250it_25pct` landed in 27.9 h\n- registry **600 fields**\n- 2 of 12 inside\n- 1600 other\n",
                    encoding="utf-8")
    rows = positions.second_homes(positions.board_figures(BOARD), [str(page)])
    labels = sorted(r[0] for r in rows)
    assert labels == ["N of 12", "registry fields", "result run", "wall hours"]
    assert all(r[2].endswith((":1", ":2", ":3")) for r in rows)
