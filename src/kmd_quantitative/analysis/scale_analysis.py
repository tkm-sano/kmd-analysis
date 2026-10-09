"""Six classical scales; descriptive saved data, never large-scale QAOA."""
from .result_io import read_json, read_table


def routes(*, raw=False, root=None):
    """Six rows; 468 logical bindings versus 460 distinct physical instances."""
    return read_table('scale_routes', raw=raw, root=root)


def methods(*, raw=False, root=None):
    return read_table('scale_methods', raw=raw, root=root)


def battery_summary(*, raw=False, root=None):
    """24 logical-distribution summaries, percent (not interaction pp)."""
    return read_table('scale_battery', raw=raw, root=root)


def conditions(*, raw=False, root=None):
    return read_table('scale_conditions', raw=raw, root=root)


def service_diagnostics(*, raw=False, root=None):
    """Six saved diagnostic rows, retaining late stops and late returns."""
    return read_table('service_diagnostics', raw=raw, root=root)


def interaction_summary(*, raw=False, root=None):
    """112 saved rows. Read summary_type/unit; estimands must not be pooled.

    Includes equal-parent mean contrasts (26 parents, percentage points) and
    logical/unique-physical/equal-parent reductions (percent).
    """
    return read_table('scale_interaction', raw=raw, root=root)


def trajectory_validation(*, root=None):
    """Saved diagnostics, not a new native VRPTW revalidation."""
    return read_json('trajectory_validation', root=root)
