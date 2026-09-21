import pytest

from analyse.baseline_behaviour import retained_plan_scores


def test_missing_and_nonfinite_scores_are_not_evaluated(tmp_path):
    path = tmp_path / 'plans.xml'
    path.write_text('''<population><person id="p"><plan selected="yes" score="10"/>
        <plan selected="no"/><plan selected="no" score="NaN"/>
        <plan selected="no" score="-Infinity"/><plan selected="no" score="-2"/>
        </person><person id="q"><plan selected="yes"/></person></population>''')
    report = retained_plan_scores(path, {'p': {'subpopulation': 'resident'},
                                        'q': {'subpopulation': 'freight'}})
    assert report['resident']['unscored_plans_count'] == 3
    assert report['resident']['selected_unscored_plans_count'] == 0
    assert report['resident']['finite_stored_scores'] == dict(count=2, minimum=-2, median=4, maximum=10)
    assert report['freight']['selected_unscored_plans_count'] == 1
    assert report['freight']['finite_stored_scores']['median'] is None


@pytest.mark.parametrize('xml', [
    '<population/>',
    '<population><person id="p"><plan selected="no"/></person></population>',
    '<population><person id="p"><plan selected="yes"/><plan selected="yes"/></person></population>',
    '<population><person id="other"><plan selected="yes"/></person></population>',
])
def test_inconsistent_population_or_selection_rejected(tmp_path, xml):
    path = tmp_path / 'plans.xml'
    path.write_text(xml)
    with pytest.raises(ValueError):
        retained_plan_scores(path, {'p': {}})
