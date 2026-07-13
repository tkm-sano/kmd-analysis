"""Build the Japanese-edited audit notebook as a separate artifact."""
from pathlib import Path

from src.revise_japanese_markdown import revise


ROOT = Path(__file__).resolve().parent
revise(
    ROOT / "quantum_transport_reproducibility_audit_revised.ipynb",
    ROOT / "quantum_transport_reproducibility_audit_japanese_revised.ipynb",
    ROOT / "outputs" / "tables" / "japanese_revision_log.csv",
)
