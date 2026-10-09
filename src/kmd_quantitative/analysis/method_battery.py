"""Final common-protocol R0/R1 results; not historical R0 or new estimates."""
from .result_io import read_json, read_table


def freeze(*, root=None):
    """Saved authority, definitions, 78/64 populations and limits."""
    return read_json('final_freeze', root=root)


def battery_conditions(*, root=None):
    return read_json('battery_model', root=root)


def summary(*, raw=False, root=None):
    """Four saved T summaries, n=64 each; T unit is percentage points."""
    return read_table('method_summary', raw=raw, root=root)


def population(*, raw=False, root=None):
    """All 78 planned blocks; preserve the 14 non-acquisitions and blanks."""
    return read_table('matched_population', raw=raw, root=root)


def contrasts(*, raw=False, root=None):
    """256 saved rows: 64 common blocks x two Crr x two Battery comparisons.

    D = Classical effect - Quantum effect; T = D_R1 - D_R0.
    _pp fields contrast percent savings, _Wh fields contrast absolute savings.
    No absent Quantum route is imputed or classified as delivery infeasible.
    """
    return read_table('matched_contrasts', raw=raw, root=root)


def energies(*, raw=False, root=None):
    """384 saved rows: 64 x two Crr x B0/B1/B2. DC Wh in observed window.

    Direct energy differences use Quantum - Classical, unlike saving D.
    """
    return read_table('direct_energy', raw=raw, root=root)
