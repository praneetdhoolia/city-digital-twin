import xml.etree.ElementTree as ET

import pytest

from build.enumerate_mode_plans import add_mode_alternatives


def population(modes='walk,pt', selected='walk', route=''):
    return ET.fromstring(f'''<population><person id="traveller"><attributes>
        <attribute name="permittedModes">{modes}</attribute><attribute name="income">100</attribute></attributes>
        <plan selected="yes"><activity type="home" x="1" y="2" end_time="100"/>
        <leg mode="{selected}">{route}</leg><activity type="education" x="3" y="4" max_dur="200"/>
        <leg mode="walk"/><activity type="home" x="1" y="2"/></plan></person>
        <person id="stay"><attributes><attribute name="permittedModes">walk,pt</attribute></attributes>
        <plan selected="yes"><activity type="home"/></plan></person>
        <person id="goods"><attributes><attribute name="permittedModes">truck</attribute>
        <attribute name="lockedMode">truck</attribute></attributes><plan selected="yes"><activity type="depot"/><leg mode="truck"/>
        <activity type="delivery"/></plan></person></population>''')


def test_all_eligible_alternatives_preserve_people_selected_plans_and_fixed_freight():
    root = population()
    before = [ET.tostring(p.find('plan')) for p in root.findall('person')]
    report = add_mode_alternatives(root, ['walk', 'pt'])
    assert [ET.tostring(p.find('plan')) for p in root.findall('person')] == before
    plans = root.find('person').findall('plan')
    assert len(plans) == 2
    assert [leg.get('mode') for leg in plans[1].findall('leg')] == ['pt', 'pt']
    assert plans[1].get('score') is None and plans[1].get('selected') == 'no'
    assert report['before_selected_demand_sha256'] == report['after_selected_demand_sha256']
    assert report['persons_by_plan_count'] == {1: 2, 2: 1}


@pytest.mark.parametrize('kwargs', [dict(modes='walk,unknown'), dict(selected='car'), dict(route='<route/>')])
def test_bad_or_experienced_eligibility_is_refused(kwargs):
    with pytest.raises(ValueError):
        add_mode_alternatives(population(**kwargs), ['walk', 'pt'])


def test_mixed_original_is_retained_beside_both_pure_mode_alternatives():
    root = population(selected='pt')
    report = add_mode_alternatives(root, ['walk', 'pt'])
    assert report['maximum_plans_per_person_count'] == 3
    assert [tuple(leg.get('mode') for leg in p.findall('leg')) for p in root.find('person').findall('plan')] == [
        ('pt', 'walk'), ('pt', 'pt'), ('walk', 'walk')]
