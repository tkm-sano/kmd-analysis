"""Explicit S2 berth sensitivity without altering frozen demand or common code."""
from dataclasses import dataclass, fields, replace
from kmd_toc.common.models import Problem
from .program import load_registered, digest, ROOT


@dataclass(frozen=True)
class BerthSensitivityProblem(Problem):
    baseline_berths: tuple = ()

    def _validate_frozen(self, conditions):
        # The ONLY variation is registered S2 berth count. All original frozen
        # checks run on the canonical four-berth reference; actual berth records
        # are still checked by Problem.validate and by both plan validators.
        if (self.experiment.scenario_id != 'S2' or len(self.baseline_berths)!=4 or
                len(self.berths) not in (2,8) or
                self.experiment.method_settings.get('A_rule_v1_berth_sensitivity') != len(self.berths)):
            raise ValueError('UNREGISTERED_BERTH_SENSITIVITY')
        Problem._validate_frozen(replace(self,berths=self.baseline_berths),conditions)


def load_input(config, scale, berths=None):
    registration = config['inputs']
    p = load_registered(ROOT/registration['input_root']/scale,registration['scenarios'][scale],scale)
    if berths is None or berths == len(p.berths):
        return p
    if scale!='S2' or berths not in (2,8):
        raise ValueError('UNREGISTERED_SENSITIVITY')
    original_hash = p.fingerprint
    actual = tuple(replace(p.berths[0],berth_id=f'B{i+1:03}') for i in range(berths))
    data = {f.name:getattr(p,f.name) for f in fields(Problem)}
    data.update(berths=actual,baseline_berths=p.berths,
                experiment=replace(p.experiment,method_settings={**p.experiment.method_settings,
                    'A_rule_v1_berth_sensitivity':berths,'canonical_problem_hash':original_hash}))
    return BerthSensitivityProblem(**data).validate()
