"""A stopped arm's persons come from its own input plans.

MATSim writes output_persons only at controler end, so the readers that
required it could not measure F36's arm 0 (#86, #107, #145). The fallback
reads the same person attributes from the run's `plans.xml.gz` - and never a
plan's own attributes.
"""
import gzip

import iteration_reading as ir

PLANS = ('<?xml version="1.0" encoding="utf-8"?>\n'
         '<population><person id="7">\n'
         '\t\t<attributes>\n'
         '\t\t\t<attribute name="subpopulation" class="java.lang.String">person</attribute>\n'
         '\t\t\t<attribute name="carAvail" class="java.lang.String">always</attribute>\n'
         '\t\t</attributes>\n'
         '\t\t<plan selected="yes">\n'
         '\t\t\t<attributes>\n'
         '\t\t\t\t<attribute name="carAvail" class="java.lang.String">PLAN</attribute>\n'
         '\t\t\t</attributes>\n'
         '\t\t</plan>\n'
         '\t</person>\n'
         '\t<person id="8">\n'
         '\t\t<attributes>\n'
         '\t\t\t<attribute name="subpopulation" class="java.lang.String">freight</attribute>\n'
         '\t\t</attributes>\n'
         '\t</person>\n</population>\n')


def test_a_stopped_arm_reads_person_attributes_from_its_plans(tmp_path):
    with gzip.open(tmp_path / 'plans.xml.gz', 'wt', encoding='utf-8') as fh:
        fh.write(PLANS)
    got = ir.person_attributes(str(tmp_path), ('subpopulation', 'carAvail'))
    assert got == {'7': {'subpopulation': 'person', 'carAvail': 'always'},
                   '8': {'subpopulation': 'freight'}}
