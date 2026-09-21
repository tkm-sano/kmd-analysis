"""Exact artifact loader and raw-sample adapter; no repair or energy authority."""
from fractions import Fraction
import numpy as np
from .contract import *
from traffic_simulation.r24_vrptw_quantum_encoding_preflight.model import build,factorized,expanded,decode_candidate
from traffic_simulation.r24_vrptw.instance import number

class Adapter:
    def __init__(self,cid):
        self.cid=cid;self.condition=condition(cid);gate=check_condition_sources(cid)
        selected=read(ENC/'SELECTED_ENCODING_SPEC.json')
        require(selected['candidate']=='COMPILED_TEMPORAL_NOGOODS','encoding','ENCODING_MISMATCH')
        self.data=read(BENCH/'instances'/f'{cid}.json');self.model=build(self.data);m=self.model
        saved=read(ENC/'conditions'/cid/'QUBO.json');self.N=m['N'];self.order=m['names']
        coeff=dict(N=self.N,offset=m['offset'],linear=m['h'].tolist(),
            quadratic=[[int(i),int(j),float(m['J'][i,j])] for i,j in zip(*np.nonzero(m['J']))])
        require(digest(coeff)==gate['qubo_coefficients_sha256'],'rebuilt coefficients','QUBO_HASH_MISMATCH')
        require(digest(self.order)==gate['variable_order_sha256'],'names','VARIABLE_ORDER_MISMATCH')
        require(coeff=={k:saved[k] for k in coeff},'saved QUBO','QUBO_HASH_MISMATCH')
        compiler=read(ENC/'conditions'/cid/'TEMPORAL_COMPILER.json')
        require(digest(m['patterns'])==digest(compiler['patterns']) and digest(m['terms'])==digest(compiler['terms']),
            'temporal no-good compilation','ENCODING_MISMATCH')
        require(m['A']==saved['penalty_A'] and m['M']==saved['AND_M'],'penalty','ENCODING_MISMATCH')
        self.authority=read(FREEZE/'FEASIBLE_AUTHORITIES.json')[cid]
        self.feasible=set(self.authority['feasible_bitstrings']);self.optimal=set(self.authority['optimal_bitstrings'])
        exact=read(BENCH/'preflight'/cid/'EXACT.json');milp=read(BENCH/'preflight'/cid/'MILP.json')
        self.optimum=number(self.authority['objective'],'objective')
        require(self.optimum==number(exact['best_objective'],'objective') and abs(self.optimum-number(milp['objective'],'objective'))<=Fraction('0.0000001'),
            'classical optimum','CLASSICAL_REFERENCE_MISMATCH')
        if self.condition['TW_regime']=='WIDE':
            continuity=next(r for r in read(FREEZE/'WIDE_CVRP_CONTINUITY.json')['records'] if r['condition']==cid)
            require(sha(ROOT/continuity['source'])==continuity['source_sha256'],'CVRP artifact','QUBO_HASH_MISMATCH')
            prior=read(ROOT/continuity['source'])
            require(prior['h_s']==m['h'].tolist() and prior['J_upper_triangle_s']==m['J'].tolist() and prior['variable_order']==self.order,'WIDE CVRP','QUBO_HASH_MISMATCH')

    def bits(self,key):
        require(isinstance(key,str) and len(key)==self.N and set(key)<=set('01'),key,'INVALID_BITSTRING')
        return np.asarray([int(c) for c in key[::-1]],dtype=np.int64)

    def inspect(self,key,count=1):
        require(type(count) is int and count>0,'frequency','INVALID_SAMPLE_COUNT')
        bits=self.bits(key);obj,pen,e=factorized(self.model,bits[None,:]);ee=float(expanded(self.model,bits[None,:])[0])
        require(abs(ee-float(e[0]))<=1e-6,'energy decomposition','ARTIFACT_VALIDATION_FAILURE')
        p={k:int(v[0]) for k,v in pen.items()};decoded=decode_candidate(self.model,bits)
        replay=decoded.get('replay');routes=decoded['routes'];encoding_valid=not any(p.values())
        components=dict(visit=p['visit']==0,route=False,capacity=None,temporal=None,depot=None)
        if replay:
            components.update(visit=replay['visit_feasible'],route=all(p[k]==0 for k in ['slot','prefix','reach']) and replay['route_feasible'],
                capacity=replay['capacity_feasible'],temporal=replay['temporal_feasible'],depot=replay['depot_feasible'])
            require(components['visit']==(p['visit']==0),'visit replay','VALIDATOR_MISMATCH')
        feasible=encoding_valid and replay is not None and replay['overall_feasible']
        independent_objective=replay['routing_objective_seconds'] if replay else None
        optimal=bool(feasible and abs(number(independent_objective,'objective')-self.optimum)<=Fraction('0.0000001'))
        distance=min(((int(key,2)^int(f,2)).bit_count() for f in self.feasible),default=None)
        require(feasible==(key in self.feasible)==(distance==0),'complete feasible authority','VALIDATOR_MISMATCH')
        require(optimal==(key in self.optimal),'optimal authority','CLASSICAL_REFERENCE_MISMATCH')
        customers=replay['customers'] if replay else [];vehicles=replay['vehicles'] if replay else []
        if feasible and self.condition['waiting_required']=='True':
            require(sum(number(c['waiting_time'],'wait') for c in customers)>0,'waiting-required replay','VALIDATOR_MISMATCH')
        # No sampled time register exists: independent early-service/precedence metrics are null.
        labels=[]
        for family in ['visit','route','capacity','temporal','depot']:
            if components[family] is False:labels.append({'temporal':'time_window','depot':'depot_return'}.get(family,family))
        if p['capacity']:labels.append('capacity_encoding')
        if p['ancilla']:labels.append('ancilla')
        weighted={k:v*(self.model['M'] if k=='ancilla' else self.model['A']) for k,v in p.items()}
        temporal_evaluable=components['temporal'] is not None
        return dict(condition=self.cid,display_bitstring=key,variable_order_bits=bits.tolist(),count=count,
            coefficient_energy=ee,factorized_energy=float(e[0]),base_objective=float(obj[0]),
            penalty_residuals=p,penalty_contributions=weighted,encoding_feasible=encoding_valid,
            existing_CVRP_penalty=sum(weighted[k] for k in ['visit','slot','prefix','capacity','reach']),
            temporal_nogood_penalty=weighted['temporal']+weighted['depot'],quadratization_penalty=weighted['ancilla'],
            decode_status='EVALUABLE' if replay else 'NOT_EVALUABLE',
            decode_failure_reason=None if replay else 'non-one-hot slot or invalid depot padding; no repair',
            routes_or_null=routes,vehicle_assignment=routes,visit_order=routes,
            capacity_state=dict(physical_valid=components['capacity'],encoding_valid=p['capacity']==0),
            temporal_evaluability='EVALUABLE' if temporal_evaluable else 'NOT_EVALUABLE',
            validator_status=decoded['replay_status'],**components,overall_feasible=bool(feasible),
            component_observability={k:'NOT_EVALUABLE' if v is None else 'EVALUABLE' for k,v in components.items()},
            replay_customer_rows=customers,replay_vehicle_rows=vehicles,violation_labels=labels,
            independent_objective=independent_objective,optimal_or_null=optimal,nearest_feasible_distance_or_null=distance,
            early_service_sampled_violation=None,temporal_precedence_sampled_violation=None,
            replay_early_service_residual=0 if temporal_evaluable else None,
            replay_precedence_residual=0 if temporal_evaluable else None,
            early_arrival_customers=sum(number(c['early_amount'],'early')>0 for c in customers),
            late_customers=sum(number(c['late_amount'],'late')>0 for c in customers),
            waiting_seconds=str(sum((number(c['waiting_time'],'wait') for c in customers),Fraction(0))),
            total_late_seconds=str(sum((number(c['late_amount'],'late') for c in customers),Fraction(0))))
