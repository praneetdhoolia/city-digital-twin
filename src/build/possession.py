"""Household vehicle possession from a vehicle stock: the identities, once.

A registration count says how many vehicles a place holds, not how many of its
households hold one - a household with two motorcycles is one owning household.
The identity that turns a stock per household into a share of households
owning at least one is the Poisson at-least-one identity (DECISIONS.md 9.209
first used it to project a census share; 9.214 uses it forwards):

    lambda = vehicles / households,   P(at least one) = 1 - exp(-lambda)

and back, lambda = -ln(1 - P). `one_per_household` is the other bound the
identity sits under: every vehicle in a different household, P = min(1, lambda).
Which one a city uses is declared (B.motorbike.possession_identity); this
module holds the arithmetic so no builder types it again.

City-agnostic and free of any value: the caller supplies the stock and the
households.
"""
import math


def at_least_one(lam):
    """P(N >= 1) for N ~ Poisson(lam): 1 - exp(-lam). lam <= 0 gives 0."""
    if lam <= 0.0:
        return 0.0
    return 1.0 - math.exp(-lam)


def one_per_household(lam):
    """The upper bound: every vehicle held by a different household."""
    return min(1.0, max(0.0, lam))


def rate_of_share(share):
    """The Poisson rate implied by a share of households owning at least one."""
    if not 0.0 <= share < 1.0:
        raise ValueError('a share owning at least one must lie in [0, 1): %r' % share)
    return -math.log(1.0 - share)


IDENTITIES = {'poisson_at_least_one': at_least_one,
              'one_per_household': one_per_household}


def share_owning(vehicles, households, identity):
    """The share of households owning at least one vehicle, by the named
    identity, or None where there are no households to hold the stock."""
    if households <= 0:
        return None
    try:
        rule = IDENTITIES[identity]
    except KeyError:
        raise ValueError('unknown possession identity %r (have %s)'
                         % (identity, ', '.join(sorted(IDENTITIES))))
    return rule(float(vehicles) / float(households))
