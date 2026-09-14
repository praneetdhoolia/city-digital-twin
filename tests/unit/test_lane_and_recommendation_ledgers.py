"""The lane ledger and the recommendation ledger (DECISIONS.md 9.171).

The lane is the one home of what is next: a malformed ledger renders nothing,
an answered decision is never listed as open, and the rendered block carries
the recommended task first. The recommendation ledger notices a report row it
does not hold.
"""
import json

import lane
import report_recs


def _doc():
    return {
        "description": "test", "updated": "2026-09-14", "family": "F35",
        "tasks": [
            {"id": "b", "title": "second", "kind": "arm", "status": "open", "recommended": False,
             "cost": "1 h", "blocked_on": "nothing", "opens_family": False, "answers_issues": [],
             "evidence": "§9.1"},
            {"id": "a", "title": "first", "kind": "arm", "status": "open", "recommended": True,
             "cost": "2 h", "blocked_on": "D1", "opens_family": True, "answers_issues": [7],
             "evidence": "§9.2"},
        ],
        "decisions": [
            {"id": "D1", "question": "which?", "options": [{"label": "x", "detail": ""}, {"label": "y", "detail": ""}],
             "recommended": 0, "issues": [7], "evidence": "§9.2", "asked": "2026-09-14",
             "answer": None, "answered": None},
            {"id": "D2", "question": "send?", "options": [{"label": "yes", "detail": ""}, {"label": "no", "detail": ""}],
             "recommended": 0, "issues": [], "evidence": "§9.3", "asked": "2026-09-13",
             "answer": "yes", "answered": "2026-09-14"},
        ],
    }


def test_well_formed_ledger_has_no_problems():
    assert lane.problems(_doc()) == []


def test_two_recommended_open_tasks_is_a_problem():
    d = _doc()
    d["tasks"][0]["recommended"] = True
    assert any("more than one" in p for p in lane.problems(d))


def test_done_without_a_record_reference_is_a_problem():
    d = _doc()
    d["tasks"][0]["status"] = "done"
    assert any("done_ref" in p for p in lane.problems(d))


def test_answer_outside_the_options_is_a_problem():
    d = _doc()
    d["decisions"][0]["answer"] = "z"
    d["decisions"][0]["answered"] = "2026-09-14"
    assert any("not one of its options" in p for p in lane.problems(d))


def test_only_unanswered_decisions_are_open():
    assert [d["id"] for d in lane.open_decisions(_doc())] == ["D1"]


def test_render_puts_the_recommended_task_first_and_lists_open_decisions():
    out = lane.render(_doc())
    lines = out.splitlines()
    assert lines[0].startswith("1. **first**")
    assert "(recommended)" in lines[0]
    assert "#7" in lines[0]
    assert any(l.startswith("- **D1.**") for l in lines)
    assert not any(l.startswith("- **D2.**") for l in lines)
    assert "Decided: D2 = yes (2026-09-14)" in out


def test_answer_is_recorded_and_not_asked_again(tmp_path, monkeypatch):
    p = tmp_path / "lane.json"
    p.write_text(json.dumps(_doc()), encoding="utf-8")
    monkeypatch.setattr(lane, "PATH", str(p))
    assert lane.main(["--answer", "D1", "y"]) == 0
    doc = json.loads(p.read_text(encoding="utf-8"))
    assert doc["decisions"][0]["answer"] == "y"
    assert doc["decisions"][0]["answered"]
    assert lane.open_decisions(doc) == []
    assert lane.main(["--answer", "D1", "nonsense"]) == 1


def test_done_marks_the_task_with_its_section(tmp_path, monkeypatch):
    p = tmp_path / "lane.json"
    p.write_text(json.dumps(_doc()), encoding="utf-8")
    monkeypatch.setattr(lane, "PATH", str(p))
    assert lane.main(["--done", "a"]) == 1          # no --ref
    assert lane.main(["--done", "a", "--ref", "9.172"]) == 0
    doc = json.loads(p.read_text(encoding="utf-8"))
    a = [t for t in doc["tasks"] if t["id"] == "a"][0]
    assert a["status"] == "done" and a["done_ref"] == "9.172" and not a["recommended"]


def test_recommendation_ledger_notices_a_missing_row(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    html = ('<html><script type="application/json" id="report-data">'
            + json.dumps({"recommendations": [{"what": "one"}, {"what": "two", "repeat_of": "ninth #1"}]})
            + '</script></html>')
    (reports / "20260914T152907_project_report.html").write_text(html, encoding="utf-8")
    monkeypatch.setattr(report_recs, "REPORTS", str(reports))
    monkeypatch.setattr(report_recs, "PATH", str(reports / "recommendations.json"))
    doc = {"description": "", "rows": [{"id": "20260914T152907:1", "report": "20260914T152907", "rank": 1,
                                        "what": "one", "repeat_of": None, "opens_family": False,
                                        "status": "taken", "evidence": "9.170", "updated": "2026-09-14"}]}
    gap = report_recs.missing(doc)
    assert [r["id"] for r in gap] == ["20260914T152907:2"]
    assert gap[0]["repeat_of"] == "ninth #1" and gap[0]["status"] == "open"
    assert report_recs.main(["--check"]) == 1          # the ledger file is absent, so the row is unsynced
