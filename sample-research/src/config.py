from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_TABLES = BASE_DIR / "outputs" / "tables"
OUTPUT_FIGURES = BASE_DIR / "outputs" / "figures"
DOCS_DIR = BASE_DIR / "docs"
