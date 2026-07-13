"""Create the stage-constraint revised notebook as a separate artifact."""
from pathlib import Path

from src.stage_constraint_revision import revise


ROOT = Path(__file__).resolve().parent
revise(
    ROOT / "quantum_transport_reproducibility_audit_revised.ipynb",
    ROOT / "quantum_transport_reproducibility_audit_stage_constraint_revised.ipynb",
)
