"""The MATSim `subpopulation` vocabulary the demand writes, named once.

`build_matsim_plans.py` stamps every person with one of three labels and
`build_matsim_run_inputs.py` emits the two non-resident ones as
`incomeScoring.excludeSubpopulations`; each typed the names itself, so a
rename in the writer would have excluded nothing at run time and no check
would have said so (eighth project report, 11 September 2026, area 1). The
labels are the FRAMEWORK's - they name demand tiers, not a city - and every
writer and reader imports them from here.
"""

RESIDENT = 'person'      # a resident with a household, a budget and an income
EXTERNAL = 'external'    # the boundary tier: volumes entering from outside
FREIGHT = 'freight'      # the freight tier: trucks, no budget

# the tiers income scoring must not touch: volumes, not budgets, and they
# carry no income attribute either
NON_RESIDENT = (EXTERNAL, FREIGHT)


def label(tier, external):
    """The subpopulation a person is written with, from the demand's own tier."""
    if tier == 'freight':
        return FREIGHT
    return EXTERNAL if external else RESIDENT
