"""Two shape rules from the sixteenth report (8 October 2026).

The board's hand paragraph said "F38 is open" under a ledger whose newest
family was F39, two reports running; the brief's header read "Commit: this
handoff's" where the template's <sha> goes. Each is now a rule.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_doc_shape", REPO / "tests" / "check_doc_shape.py")
cds = importlib.util.module_from_spec(spec)
sys.modules["check_doc_shape"] = cds
spec.loader.exec_module(cds)

BOARD_SPEC = {"path": "{city}/docs/STATUS.md", "max_hand_lines": 170, "open_family_claim": r"\bF(\d+) is open\b"}
BRIEF_SPEC = {"path": "{city}/docs/NEXT_AGENT_BRIEF.md", "max_lines": 180,
              "family_stamp": r"\*\*Open family:\*\*\s*`([^`]+)`",
              "commit_stamp": r"\*\*Commit:\*\*\s*`([0-9a-f]{7,40})`"}


def _city(tmp_path):
    (tmp_path / "docs").mkdir()
    return tmp_path


def test_a_hand_line_may_say_only_the_newest_family_is_open(tmp_path):
    city = _city(tmp_path)
    (city / "docs" / "STATUS.md").write_text(
        "# b\n<!-- generated:state start -->\nF38 is open here is generated and ignored\n<!-- generated:state end -->\n"
        "F38 is open at the rebuild.\nF39 is open at its rebuild.\n", encoding="utf-8")
    problems = cds.check_board(city, BOARD_SPEC, "F39-motorcycles-by-daily-use")
    assert len(problems) == 1 and "F38 is open" in problems[0] and ":5:" in problems[0]
    assert cds.check_board(city, BOARD_SPEC, "F38-destinations") == [
        p for p in cds.check_board(city, BOARD_SPEC, "F38-destinations") if "F39 is open" in p]


def test_the_brief_commit_stamp_must_be_a_sha(tmp_path):
    city = _city(tmp_path)
    brief = city / "docs" / "NEXT_AGENT_BRIEF.md"
    head = "# Brief\n\n**Written:** x · **Open family:** `F39-x` · **Commit:** %s\n\n## §0\n## §1\n## §2\n## §3\n"
    brief.write_text(head % "this handoff's", encoding="utf-8")
    assert any("commit stamp" in p for p in cds.check_brief(city, BRIEF_SPEC, "F39-x"))
    brief.write_text(head % "`e25deff2`", encoding="utf-8")
    assert not any("commit stamp" in p for p in cds.check_brief(city, BRIEF_SPEC, "F39-x"))


def test_position_caps_exclude_a_generated_block(tmp_path):
    city = _city(tmp_path)
    d = city / "docs" / "positions"
    d.mkdir()
    big = "| `F1-x` | 20260816T000000 | %s | §9.1 |\n" % ("x" * 500)
    (d / "sampling-and-families.md").write_text(
        "# S\n\n**Updated:** x · **Record read through:** §9.1 · **Written against family:** `F1-x`\n\n"
        "## What is built\n\n## What is measured\n\n## What is open\n\n"
        "<!-- generated:families start -->\n" + big * 40 + "<!-- generated:families end -->\n\n## History\n",
        encoding="utf-8")
    spec_ = {"dir": "{city}/docs/positions", "max_lines": 130, "max_bytes": 14000, "max_line_chars": 600,
             "required_headings": ["## What is built", "## What is measured", "## What is open", "## History"],
             "families_page": "sampling-and-families.md", "family_stamp": r"\*\*Written against family:\*\*\s*`(F[^`]+)`"}
    assert cds.check_positions(city, spec_, ["F1-x"]) == []
    assert any("F2-y" in p for p in cds.check_positions(city, spec_, ["F1-x", "F2-y"]))
