from .validation import require_valid


def evaluate(p,plan):
    report=require_valid(p,plan)
    return {**report,'primary_D_definition':'all_shared_OD_depot_customer_customer_depot_distance',
            'break_added_to_W':False,'W_adjusted_posthoc':False,
            'total_break_min':sum(b.end_s-b.start_s for b in plan.breaks)/60}
