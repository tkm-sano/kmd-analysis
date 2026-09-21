"""Identical Standard aggregation arithmetic with Structured identity resolution."""
import types
from .contract import run_plan,run_identity
from traffic_simulation.r24_vrptw_qaoa_worker import results as standard
save=standard.save
summarize=standard.summarize
_g=dict(standard.__dict__)
_g.update(plan=lambda spec,rid:run_plan(rid)[0],identity=lambda spec,r:run_identity(r['run_id']))
aggregate_batch=types.FunctionType(standard.aggregate_batch.__code__,_g,'aggregate_batch',standard.aggregate_batch.__defaults__)
