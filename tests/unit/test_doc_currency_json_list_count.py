"""check_doc_currency.py `json_list_count`: a claim about a list's length (the
Mumbai catalogue, the sixteenth report C23)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_doc_currency", REPO / "tests" / "check_doc_currency.py")
cdc = importlib.util.module_from_spec(spec)
sys.modules["check_doc_currency"] = cdc
spec.loader.exec_module(cdc)


def test_json_list_count_counts_the_list_and_a_matched_subset(tmp_path):
    (tmp_path / "sources.json").write_text(json.dumps({"sources": [
        {"licence": "A"}, {"licence": "A"}, {"licence": "B"}, "not a dict"]}), encoding="utf-8")
    assert cdc.truth_json_list_count(tmp_path, {"file": "sources.json", "key": "sources"}) == 4
    assert cdc.truth_json_list_count(tmp_path, {"file": "sources.json", "key": "sources", "match": {"licence": "A"}}) == 2
    with pytest.raises(cdc.Skip):
        cdc.truth_json_list_count(tmp_path, {"file": "sources.json", "key": "missing"})
    assert "json_list_count" in cdc.RESOLVERS
