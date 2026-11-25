from dataclasses import dataclass, replace, asdict, field
from functools import cached_property
from pathlib import Path
import json

from kmd_toc.common.config import fingerprint, read_json
from kmd_toc.common.models import Plan, Trip, Visit
from .policy import VERSION, load_policy, policy_hash


@dataclass(frozen=True)
class RestOptions:
    allow_assumed_locations: bool = False
    allow_post_final_depot_break: bool = True
    # Immutable (location ID, provenance evidence) caller-supplied confirmations.
    confirmed_locations: tuple = ()

    def payload(self):
        if type(self.allow_assumed_locations) is not bool or type(self.allow_post_final_depot_break) is not bool:
            raise ValueError('EXPLICIT_REST_OPTIONS_REQUIRED')
        if not self.allow_post_final_depot_break:
            raise ValueError('USER_APPROVED_EARLY_RETURN_RULE_CANNOT_BE_DISABLED')
        pairs = self.confirmed_locations
        if (not isinstance(pairs,tuple) or any(not isinstance(x,tuple) or len(x)!=2 or
                any(not isinstance(t,str) or not t.strip() for t in x) for x in pairs) or
                len({x[0] for x in pairs})!=len(pairs)):
            raise ValueError('REST_LOCATION_EVIDENCE_SCHEMA')
        return {'allow_assumed_locations':self.allow_assumed_locations,
                'allow_post_final_depot_break':self.allow_post_final_depot_break,
                'confirmed_locations':[list(x) for x in sorted(pairs)]}

    def eligible(self, location):
        self.payload()
        return self.allow_assumed_locations or location in dict(self.confirmed_locations)

    def evidence(self, location):
        proof = dict(self.confirmed_locations).get(location)
        return ('caller_confirmed',proof) if proof else ('assumed_unverified',None)


@dataclass(frozen=True)
class DutyProblem:
    base: object
    rest_options: RestOptions
    activated_policy_sha256: str = field(default_factory=policy_hash,init=False)

    def __getattr__(self, name):
        return getattr(self.base,name)

    @cached_property
    def vehicles(self):
        deadline=load_policy()['vehicle_return_deadline_s']
        return tuple(replace(v,return_deadline_s=deadline) for v in self.base.vehicles)

    @cached_property
    def fingerprint(self):
        return fingerprint({'base_problem_hash':self.base.fingerprint,'duty_policy_sha256':self.activated_policy_sha256,
                            'rest_options':self.rest_options.payload()})

    def validate(self):
        raise ValueError('DUTY_INPUT_REQUIRES_VERSIONED_VALIDATOR_NO_LEGACY_FALLBACK')

    def validate_duty(self):
        self.base.validate();c=load_policy();self.rest_options.payload()
        if policy_hash()!=self.activated_policy_sha256:raise ValueError('DUTY_POLICY_CHANGED_DURING_INPUT_LIFETIME')
        if any(v.first_ready_s<c['shift_start_s'] for v in self.vehicles):
            raise ValueError('FIRST_READY_BEFORE_SHIFT')
        if any(b.opening_s!=c['berth_opening_s'] or b.closing_s!=c['berth_closing_s'] for b in self.berths):
            raise ValueError('BERTH_HOURS_MUST_REMAIN_0800_2000')
        if any(v.return_deadline_s!=c['vehicle_return_deadline_s'] for v in self.vehicles):
            raise ValueError('DUTY_VEHICLE_RETURN_DEADLINE')
        known={s.stop_id for s in self.stops}|{self.depot.depot_id}
        if any(loc not in known for loc,_ in self.rest_options.confirmed_locations):
            raise ValueError('BREAK_DETOUR_REQUIRES_NEW_OD_NODE_AND_APPROVAL')
        return self


def activate(base, *, version, rest_options=None):
    if version!=VERSION:
        raise ValueError('EXPLICIT_DUTY_VERSION_REQUIRED')
    if isinstance(base,DutyProblem):
        raise ValueError('NO_DOUBLE_DUTY_OVERLAY')
    return DutyProblem(base,rest_options or RestOptions()).validate_duty()


@dataclass(frozen=True)
class Break:
    vehicle_id: str
    trip_no: int | None
    location_id: str
    start_s: int
    end_s: int
    placement: str
    location_status: str
    evidence: str | None


@dataclass(frozen=True)
class DutyPlan(Plan):
    breaks: tuple = ()


def save_plan(plan,path):
    with Path(path).open('x') as f:
        json.dump(asdict(plan),f,indent=2,ensure_ascii=False,allow_nan=False)


def load_plan(path):
    data=read_json(path)
    if data.get('schema_version')!='duty-break-plan-v1':
        raise ValueError('DO_NOT_MIX_LEGACY_AND_DUTY_PLANS')
    try:
        trips=[]
        for raw in data.pop('trips'):
            raw['visits']=tuple(Visit(**v) for v in raw['visits']);trips.append(Trip(**raw))
        breaks=tuple(Break(**b) for b in data.pop('breaks'))
        return DutyPlan(**data,trips=tuple(trips),breaks=breaks)
    except (TypeError,KeyError) as error:
        raise ValueError('DUTY_PLAN_FIELDS') from error
