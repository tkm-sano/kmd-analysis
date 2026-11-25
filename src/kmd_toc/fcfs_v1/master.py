"""Keep historical D-only pricing, replace its non-FCFS W integer selection."""
from kmd_toc.termination_v1.master import FiniteMaster


class FCFSIntegerCompletion(FiniteMaster):
    def __init__(self,p,day,columns,pool,seed_plan,config,ledger):
        super().__init__(day,columns,config,ledger)
        self.problem=p;self.route_pool=pool;self.seed_plan=seed_plan

    def lp(self,indices,primary='D',limit=None):
        if primary!='D' or limit is not None:
            raise ValueError('FCFS_CALENDAR_LP_IS_DISTANCE_PRICING_ONLY_NOT_W')
        result=super().lp(indices,primary,limit)
        result['scope']='historical_fixed_calendar_distance_pricing_surrogate_not_FCFS_W_or_global_bound'
        return result

    def ip(self,indices,primary='D',limit=None,seconds=None):
        if primary!='D' or limit is not None or seconds is not None:
            raise ValueError('FCFS_INTEGER_OBJECTIVE_OR_BUDGET_OVERRIDE_FORBIDDEN')
        from .cp import solve_completion,FCFSNoSolution
        try:
            plan=solve_completion(self.problem,self.route_pool,self.seed_plan.method_id,
                self.config,self.ledger,self.seed_plan.method_settings['fcfs_solver_seed'])
        except FCFSNoSolution as error:
            return {'success':False,'reason':str(error),'selected':[],'operating_policy':'FCFS_v1'}
        return {'success':True,'selected':[],'operating_policy':'FCFS_v1',
                'objective':sum(t.distance_m for t in plan.trips)/1000,
                'reason':'global_FCFS_W_is_not_additive_over_fixed_calendar_columns',
                'scope':'same_supplied_route_pool_D_first_W_second_FCFS_CP',
                'fcfs_assignments':[{'vehicle_id':t.vehicle_id,'trip_no':t.trip_no,
                                     'route':[v.stop_id for v in t.visits]} for t in plan.trips],
                'fcfs_settings':plan.method_settings}
