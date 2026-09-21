"""Give unscored daily plans access to every declared eligible transport mode."""
from collections import Counter
from copy import deepcopy
import hashlib
import xml.etree.ElementTree as ET


def selected_demand_hash(population):
    digest = hashlib.sha256()
    for person in population.findall('person'):
        selected = [p for p in person.findall('plan') if p.get('selected') == 'yes']
        if len(selected) != 1:
            raise ValueError('Exactly one selected input plan is required')
        attributes = person.find('attributes')
        for value in (person.get('id').encode(),
                      ET.tostring(attributes) if attributes is not None else b'', ET.tostring(selected[0])):
            digest.update(value)
            digest.update(b'\0')
    return digest.hexdigest()


def add_mode_alternatives(population, supported_modes):
    before = selected_demand_hash(population)
    modes_added, plan_counts = Counter(), Counter()
    persons_with_choices = 0
    for person in population.findall('person'):
        plans = person.findall('plan')
        if len(plans) != 1:
            raise ValueError('Alternative enumeration requires a fresh single-plan input')
        original = plans[0]
        permitted = person.findtext("attributes/attribute[@name='permittedModes']")
        legs = original.findall('leg')
        locked = person.findtext("attributes/attribute[@name='lockedMode']")
        if locked is not None:
            if any(leg.get('mode') != locked for leg in legs):
                raise ValueError('Fixed-mode demand conflicts with its locked mode')
            plan_counts[len(plans)] += 1
            continue
        if permitted is not None and legs:
            modes = set(permitted.split(','))
            if not modes or not modes <= set(supported_modes):
                raise ValueError('Unsupported eligibility modes: ' + str(sorted(modes)))
            if original.get('score') is not None or any(leg.find('route') is not None for leg in legs):
                raise ValueError('Enumerate fresh unscored, unrouted plans, not experienced journeys')
            initial = tuple(leg.get('mode') for leg in legs)
            if not set(initial) <= modes:
                raise ValueError('The selected input plan violates declared mode eligibility')
            for mode in sorted(modes):
                if all(value == mode for value in initial):
                    continue
                alternative = deepcopy(original)
                alternative.set('selected', 'no')
                for leg in alternative.findall('leg'):
                    leg.set('mode', mode)
                person.append(alternative)
                modes_added[mode] += 1
            persons_with_choices += int(len(person.findall('plan')) > 1)
        plan_counts[len(person.findall('plan'))] += 1
    after = selected_demand_hash(population)
    if before != after:
        raise ValueError('Enumeration changed selected demand or person attributes')
    return dict(persons_count=len(population.findall('person')),
                persons_with_mobile_choices_count=persons_with_choices,
                plans_added_by_mode=dict(modes_added), persons_by_plan_count=dict(sorted(plan_counts.items())),
                maximum_plans_per_person_count=max(plan_counts),
                before_selected_demand_sha256=before, after_selected_demand_sha256=after)
