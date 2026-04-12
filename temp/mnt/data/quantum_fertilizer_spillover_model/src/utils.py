from __future__ import annotations

from math import erf, sqrt
from pathlib import Path
from typing import Iterable


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def yen(x: float) -> str:
    return f"{x:,.0f} 円"


def number(x: float, digits: int = 2) -> str:
    return f"{x:,.{digits}f}"


def markdown_table(rows: list[list[str]], headers: list[str]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt(row: Iterable[str]) -> str:
        cells = [str(cell).ljust(widths[i]) for i, cell in enumerate(row)]
        return "| " + " | ".join(cells) + " |"

    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    lines = [fmt(headers), separator]
    lines.extend(fmt(row) for row in rows)
    return "\n".join(lines)
