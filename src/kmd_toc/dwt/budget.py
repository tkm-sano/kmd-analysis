"""An end-to-end deadline; budget is never substituted for measured wall time."""
import time
import math


class BudgetExceeded(TimeoutError):
    pass


class Budget:
    def __init__(self, seconds, reserve_fraction=0.08, clock=time.perf_counter, capture_sink=None,
                 adaptive_validation=False, verification_passes=2, jitter_fraction=0.02):
        if (type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0
                or not math.isfinite(reserve_fraction) or not 0 <= reserve_fraction < 1):
            raise ValueError('BUDGET_RANGE')
        self.clock = clock
        self.start = clock()
        self.seconds = seconds
        self.deadline = self.start + seconds
        self.reserve = seconds * reserve_fraction
        self.events = [{'name': 'input_load_start', 'elapsed_s': 0.0}]
        self.evidence = {}
        self.capture_sink = capture_sink
        self.adaptive_validation = adaptive_validation
        self.verification_passes = verification_passes
        self.jitter_fraction = jitter_fraction
        self.max_validation_s = 0.
        self.incumbent = None

    def observe_validation(self, elapsed):
        self.max_validation_s = max(self.max_validation_s, elapsed)
        if self.adaptive_validation:
            self.reserve = max(self.reserve, self.verification_passes * self.max_validation_s
                               + self.seconds * self.jitter_fraction)

    def capture(self, name, value):
        self.evidence[name] = value
        if self.capture_sink is not None:
            self.capture_sink(name, value)

    def mark(self, name):
        self.events.append({'name': name, 'elapsed_s': self.clock() - self.start})

    def left(self, cap=None, *, validation=False):
        remaining = self.deadline - self.clock() - (0 if validation else self.reserve)
        if remaining <= 0:
            raise BudgetExceeded('END_TO_END_BUDGET_EXHAUSTED')
        return remaining if cap is None else min(remaining, cap)

    @property
    def elapsed(self):
        return self.clock() - self.start
