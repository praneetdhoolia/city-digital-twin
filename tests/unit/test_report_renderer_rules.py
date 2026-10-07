"""render_report.py: a model recommendation states what it predicts, and the
reference library's State table is written from the two JSON files (the
sixteenth report, 8 October 2026)."""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "render_report", REPO / ".claude" / "skills" / "project-report" / "scripts" / "render_report.py")
rr = importlib.util.module_from_spec(spec)
sys.modules["render_report"] = rr
spec.loader.exec_module(rr)


def test_a_model_recommendation_without_a_prediction_is_refused():
    recs = [{"category": "model", "what": "a change"},
            {"category": "model", "what": "b", "predicts": {"mode": "walk", "direction": "up", "size": ""}},
            {"category": "model", "what": "c", "predicts": {"mode": "walk", "direction": "up", "size": "2 pp"}},
            {"category": "code", "what": "d"}]
    bad = rr.check_predictions(recs)
    assert len(bad) == 2 and "recommendation 1" in bad[0] and "recommendation 2" in bad[1]


def test_the_library_state_table_comes_from_the_json_counts(tmp_path):
    (tmp_path / "field-survey.json").write_text(json.dumps({
        "projects": [{}] * 61, "platforms": [{}] * 12, "excluded": [{}] * 88, "not_reverified": [{}] * 47,
        "gaps": [{"status": None}] * 7 + [{"status": "CLOSED"}] * 25,
        "last_pass": {"rows_reused": 53, "rows_refreshed": 5, "rows_added": 3, "platforms_reused": 12,
                      "gaps_closed": 5, "gaps_added": 3, "searches_spent": 35, "budget": 40, "rounds": 4}}), encoding="utf-8")
    (tmp_path / "factors.json").write_text(json.dumps({
        "factors": [{}] * 108, "gaps": [{}] * 19, "counts": {"needs_research": 1},
        "last_pass": {"factors_added": 2, "added": ["E30", "E31"], "addenda_written": 16,
                      "gaps_closed": ["a", "b"], "gaps_added": ["c"] * 4, "searches_spent": 33, "budget": 40}}), encoding="utf-8")
    body = rr.library_state(tmp_path, "20261008T003329", "1b14e559abcdef", "2026-10-07", "sixteenth")
    assert "**61**" in body and "**32 (7 open)**" in body and "**108**" in body and "E30, E31" in body
    assert "the sixteenth report" in body and "`1b14e559`" in body
    readme = tmp_path / "README.md"
    readme.write_text("# L\n\n## State\n\n<!-- generated:library-state start -->\nold\n<!-- generated:library-state end -->\n\n## Next\n",
                      encoding="utf-8")
    assert rr.write_library_state(readme, body)
    text = readme.read_text(encoding="utf-8")
    assert "old" not in text and "**61**" in text and text.endswith("## Next\n")
    readme.write_text("no markers\n", encoding="utf-8")
    assert not rr.write_library_state(readme, body)
