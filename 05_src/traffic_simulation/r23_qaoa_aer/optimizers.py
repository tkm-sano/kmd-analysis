"""Small, explicit optimizer adapter for the governed R23 execution path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from scipy.optimize import minimize


SUPPORTED_OPTIMIZERS = ("COBYLA", "NELDER_MEAD")


class ObjectiveEvaluationCapReached(RuntimeError):
    """Raised before an objective call would exceed the common research cap."""

    reason_code = "OBJECTIVE_EVALUATION_CAP_REACHED"


@dataclass(frozen=True)
class NormalizedOptimizerResult:
    """Common result view while retaining the native SciPy result separately."""

    optimizer_name: str
    optimizer_method: str
    final_parameters: list[float]
    final_objective: float | None
    nfev: int | None
    nit: int | None
    optimizer_success: bool | None
    optimizer_status: int | None
    optimizer_message: str | None
    native_result: Any


def optimizer_method(name: str) -> str:
    normalized = name.upper().replace("-", "_")
    if normalized == "COBYLA":
        return "COBYLA"
    if normalized in {"NELDER_MEAD", "NELDERMEAD"}:
        return "Nelder-Mead"
    raise ValueError(f"unsupported R23 optimizer: {name}")


def minimize_objective(
    *,
    optimizer_name: str,
    fun: Callable[[Sequence[float]], float],
    x0: Sequence[float],
    maxiter: int,
    objective_cap: int,
    options: dict[str, Any] | None = None,
) -> NormalizedOptimizerResult:
    """Run exactly one selected SciPy method with a common callback budget.

    The objective callback remains responsible for enforcing the common R23
    cap.  ``maxiter`` is passed as a method-specific option and is not treated
    as equivalent work across methods.
    """
    method = optimizer_method(optimizer_name)
    method_options = dict(options or {})
    method_options.setdefault("maxiter", maxiter)
    if method == "Nelder-Mead":
        method_options.setdefault("maxfev", objective_cap)
    evaluation_count = 0

    def budgeted_fun(values):
        nonlocal evaluation_count
        if evaluation_count >= objective_cap:
            raise ObjectiveEvaluationCapReached("objective evaluation cap reached")
        evaluation_count += 1
        return fun(values)

    native = minimize(fun=budgeted_fun, x0=list(x0), method=method, options=method_options)
    final_parameters = [float(v) for v in native.x]
    raw_nfev = getattr(native, "nfev", None)
    raw_nit = getattr(native, "nit", None)
    raw_success = getattr(native, "success", None)
    raw_status = getattr(native, "status", None)
    return NormalizedOptimizerResult(
        optimizer_name=optimizer_name,
        optimizer_method=method,
        final_parameters=final_parameters,
        final_objective=float(native.fun) if getattr(native, "fun", None) is not None else None,
        nfev=None if raw_nfev is None else int(raw_nfev),
        nit=None if raw_nit is None else int(raw_nit),
        optimizer_success=None if raw_success is None else bool(raw_success),
        optimizer_status=None if raw_status is None else int(raw_status),
        optimizer_message=None if getattr(native, "message", None) is None else str(native.message),
        native_result=native,
    )
