"""Reusable, presentation-quality rendering for research summary tables.

The CSV exporter deliberately does not apply presentation rounding.  Display
formatting, line wrapping, alignment, and emphasis are applied only while
rendering PNG or SVG files, so the CSV remains suitable for verification and
secondary analysis.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import suppress
from functools import lru_cache
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Literal, TypeAlias
import unicodedata
import warnings

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import font_manager, rc_context
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


DEFAULT_RESEARCH_NOTE = (
    "注: 本表はsynthetic customer configurationおよびroute proxyに基づく。"
    "東京都の実配送における観測失敗率を示すものではない。各数値は、車両性能、"
    "顧客需要、配送可能時間、充電条件、およびルート生成方法の仮定に依存する。"
)

Formatter: TypeAlias = Callable[[Any], str] | str

_JAPANESE_FONT_CANDIDATES = (
    "Noto Sans CJK JP",
    "Noto Sans JP",
    "Source Han Sans JP",
    "Source Han Sans",
    "Hiragino Sans",
    "Yu Gothic",
    "YuGothic",
    "Meiryo",
    "IPAexGothic",
    "IPAGothic",
    "TakaoGothic",
    "Arial Unicode MS",
)

_MISSING_DISPLAY = "Not evaluated"
_BREAK_AFTER = frozenset(" \t/-;,:、。，．：；・）)]}〉》」』】")
_ACRONYMS = {
    "ci": "CI",
    "csv": "CSV",
    "doi": "DOI",
    "ev": "EV",
    "evrp": "EVRP",
    "id": "ID",
    "kg": "kg",
    "km": "km",
    "kw": "kW",
    "kwh": "kWh",
    "qrl": "QRL",
    "soc": "SOC",
    "srl": "SRL",
    "svg": "SVG",
    "url": "URL",
}


def export_table_as_csv(
    table: pd.DataFrame,
    output_path: str | os.PathLike[str],
    *,
    index: bool = False,
    encoding: str = "utf-8-sig",
    na_rep: str = "",
) -> Path:
    """Write a table without presentation rounding, using an atomic replace.

    Parameters
    ----------
    table:
        Source table. Values and column names are passed directly to
        :meth:`pandas.DataFrame.to_csv`; in particular, no ``float_format`` is
        supplied and no display strings are substituted for missing values.
    output_path:
        Destination ending in ``.csv``. Parent directories are created when
        necessary.
    index:
        Whether to include the DataFrame index. Research summary tables
        normally use the default, ``False``.
    encoding:
        Text encoding. ``utf-8-sig`` is the default so Japanese text opens
        reliably in spreadsheet software while remaining UTF-8.
    na_rep:
        CSV representation of missing values. The default is an empty field;
        use an explicit research-status string in ``table`` when a status such
        as ``Not evaluated`` is part of the data rather than presentation.

    Returns
    -------
    pathlib.Path
        The resolved destination path (not necessarily an absolute path).

    Notes
    -----
    The temporary file is flushed and fsynced before :func:`os.replace`.
    Consequently, readers see either the previous complete file or the new
    complete file on filesystems that provide atomic same-directory rename.
    """

    _validate_table(table)
    destination = _prepare_destination(output_path, ".csv")
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.stem}.",
        suffix=".tmp.csv",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding=encoding, newline="") as handle:
            table.to_csv(
                handle,
                index=index,
                na_rep=na_rep,
                lineterminator="\n",
            )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        _fsync_directory(destination.parent)
    except BaseException:
        with suppress(FileNotFoundError):
            temporary_path.unlink()
        raise
    return destination


def render_table_as_png(
    table: pd.DataFrame,
    output_path: str | os.PathLike[str],
    *,
    title: str | None = None,
    note: str = DEFAULT_RESEARCH_NOTE,
    emphasized_columns: Iterable[str] | None = None,
    column_labels: Mapping[str, str] | Sequence[str] | None = None,
    formatters: Mapping[str, Formatter] | None = None,
    dpi: int = 300,
    font_size: float = 9.0,
    font_family: str | None = None,
    landscape: bool = True,
) -> Path:
    """Render a DataFrame as a high-resolution, presentation-ready PNG.

    Numeric columns are right-aligned and textual columns are left-aligned.
    Column widths and row heights are inferred from the displayed content,
    including Japanese full-width characters. Long cell text is wrapped and
    missing values are displayed as ``Not evaluated``. Raw values in ``table``
    are never modified.

    Parameters
    ----------
    table, output_path:
        Source DataFrame and a destination ending in ``.png``.
    title:
        Optional title placed above the table.
    note:
        Note placed below the table. It defaults to the scope warning required
        for the synthetic EVRP research tables.
    emphasized_columns:
        Column names to highlight with an accent header and tinted cells.
    column_labels:
        Optional mapping from source column name to display label, or one label
        per source column. Without it, snake-case names are humanized.
    formatters:
        Per-column callables or Python format specifications. For example,
        ``{"unmet_rate": ".1%", "distance_km": ",.1f"}``. Missing values
        retain the standard ``Not evaluated`` display.
    dpi:
        Raster resolution. The default, 300 dpi, is suitable for research
        slides and print.
    font_size, font_family:
        Base point size and optional installed font family. If the requested
        family is unavailable, an installed Japanese-capable family is chosen.
    landscape:
        Ensure the canvas is wider than it is tall, useful for wide tables.

    Returns
    -------
    pathlib.Path
        Path of the completed PNG.
    """

    if isinstance(dpi, bool) or not isinstance(dpi, int) or not 72 <= dpi <= 1200:
        raise ValueError("dpi must be an integer between 72 and 1200.")
    destination = _prepare_destination(output_path, ".png")
    figure = _build_table_figure(
        table,
        title=title,
        note=note,
        emphasized_columns=emphasized_columns,
        column_labels=column_labels,
        formatters=formatters,
        font_size=font_size,
        font_family=font_family,
        landscape=landscape,
        svg_text=False,
    )
    try:
        _atomic_save_figure(figure, destination, file_format="png", dpi=dpi)
    finally:
        plt.close(figure)
    return destination


def render_table_as_svg(
    table: pd.DataFrame,
    output_path: str | os.PathLike[str],
    *,
    title: str | None = None,
    note: str = DEFAULT_RESEARCH_NOTE,
    emphasized_columns: Iterable[str] | None = None,
    column_labels: Mapping[str, str] | Sequence[str] | None = None,
    formatters: Mapping[str, Formatter] | None = None,
    font_size: float = 9.0,
    font_family: str | None = None,
    landscape: bool = True,
) -> Path:
    """Render a DataFrame as an editable-text SVG research table.

    This function uses the same wrapping, formatting, alignment, automatic
    sizing, Japanese-font selection, emphasis, and note placement as
    :func:`render_table_as_png`. Matplotlib's ``svg.fonttype`` is set to
    ``"none"`` in a local rendering context, so text remains SVG ``<text>``
    elements instead of being converted to outlines.

    Parameters are identical to :func:`render_table_as_png` except that the
    resolution-independent SVG output has no DPI option.

    Returns
    -------
    pathlib.Path
        Path of the completed SVG.
    """

    destination = _prepare_destination(output_path, ".svg")
    figure = _build_table_figure(
        table,
        title=title,
        note=note,
        emphasized_columns=emphasized_columns,
        column_labels=column_labels,
        formatters=formatters,
        font_size=font_size,
        font_family=font_family,
        landscape=landscape,
        svg_text=True,
    )
    try:
        _atomic_save_figure(figure, destination, file_format="svg", dpi=96)
    finally:
        plt.close(figure)
    return destination


def _build_table_figure(
    table: pd.DataFrame,
    *,
    title: str | None,
    note: str,
    emphasized_columns: Iterable[str] | None,
    column_labels: Mapping[str, str] | Sequence[str] | None,
    formatters: Mapping[str, Formatter] | None,
    font_size: float,
    font_family: str | None,
    landscape: bool,
    svg_text: bool,
) -> Figure:
    """Build, but do not save, a table figure."""

    _validate_table(table)
    if isinstance(font_size, bool) or not isinstance(font_size, (int, float)):
        raise TypeError("font_size must be a positive number.")
    if not math.isfinite(float(font_size)) or not 5.0 <= float(font_size) <= 36.0:
        raise ValueError("font_size must be between 5 and 36 points.")
    if title is not None and not isinstance(title, str):
        raise TypeError("title must be a string or None.")
    if not isinstance(note, str):
        raise TypeError("note must be a string.")
    if font_family is not None and not isinstance(font_family, str):
        raise TypeError("font_family must be a string or None.")
    if not isinstance(landscape, bool):
        raise TypeError("landscape must be a boolean.")

    frame = table.copy(deep=False)
    source_columns = list(frame.columns)
    names = [str(column) for column in source_columns]
    if len(set(names)) != len(names):
        raise ValueError("Column names must remain unique when converted to strings.")
    frame.columns = names

    emphasized = _normalize_emphasized_columns(emphasized_columns, names)
    labels = _normalize_column_labels(column_labels, names)
    normalized_formatters = _normalize_formatters(formatters, names)
    numeric_columns = {name for name in names if _column_is_numeric(frame[name])}

    display_rows: list[list[str]] = []
    for row in frame.itertuples(index=False, name=None):
        display_rows.append(
            [
                _format_value(value, name, normalized_formatters.get(name))
                for name, value in zip(names, row, strict=True)
            ]
        )
    if not display_rows:
        # Matplotlib's table artist cannot construct a header-only table. Keep
        # the zero-row state visually explicit instead of raising an opaque
        # IndexError or making an empty result look like a failed export.
        display_rows = [["No records", *("" for _ in names[1:])]]

    width_units = _infer_column_widths(
        names,
        labels,
        display_rows,
        numeric_columns=numeric_columns,
    )
    wrapped_labels = [
        _wrap_text(label, max(5, int(width)))
        for label, width in zip(labels, width_units, strict=True)
    ]
    wrapped_rows = [
        [
            _wrap_text(value, max(5, int(width)))
            for value, width in zip(row, width_units, strict=True)
        ]
        for row in display_rows
    ]

    header_lines = max((_line_count(value) for value in wrapped_labels), default=1)
    row_lines = [
        max((_line_count(value) for value in row), default=1) for row in wrapped_rows
    ]
    row_height_inches = [
        _height_for_lines(header_lines, font_size, is_header=True),
        *[_height_for_lines(count, font_size) for count in row_lines],
    ]
    table_height = sum(row_height_inches)

    width_per_unit = max(0.061, float(font_size) * 0.0071)
    table_width = max(11.5, sum(width_units) * width_per_unit)
    table_width = min(table_width, 42.0)

    provisional_width = table_width + 0.60
    note_width_units = max(30, int((provisional_width - 0.70) / width_per_unit))
    wrapped_note = _wrap_text(note, note_width_units) if note else ""
    note_lines = _line_count(wrapped_note) if wrapped_note else 0
    note_height = (0.20 + note_lines * font_size * 1.35 / 72.0) if note_lines else 0.12
    title_height = 0.62 if title else 0.20
    figure_height = table_height + note_height + title_height + 0.30
    figure_width = provisional_width
    if landscape and figure_width <= figure_height:
        figure_width = min(42.0, figure_height * 1.15)

    # Keep a pathological long-text table renderable without silently dropping
    # rows. The SVG remains fully scalable; a large PNG is intentionally left
    # to the caller's requested DPI.
    figure_height = min(max(figure_height, 3.0), 36.0)
    figure_width = min(max(figure_width, 12.0), 42.0)

    selected_font = _select_japanese_font(font_family)
    rc_parameters: dict[str, Any] = {
        "font.family": [selected_font, "DejaVu Sans"],
        "axes.unicode_minus": False,
    }
    if svg_text:
        rc_parameters["svg.fonttype"] = "none"

    with rc_context(rc_parameters):
        figure = plt.figure(
            figsize=(figure_width, figure_height),
            facecolor="white",
            layout=None,
        )
        left_inches = 0.30
        right_inches = 0.30
        bottom_inches = note_height + 0.12
        top_inches = title_height + 0.08
        axes = figure.add_axes(
            (
                left_inches / figure_width,
                bottom_inches / figure_height,
                1.0 - (left_inches + right_inches) / figure_width,
                1.0 - (bottom_inches + top_inches) / figure_height,
            )
        )
        axes.axis("off")

        column_width_fractions = np.asarray(width_units, dtype=float)
        column_width_fractions /= column_width_fractions.sum()
        artist = axes.table(
            cellText=wrapped_rows,
            colLabels=wrapped_labels,
            colWidths=column_width_fractions.tolist(),
            cellLoc="left",
            bbox=Bbox.from_bounds(0.0, 0.0, 1.0, 1.0),
        )
        artist.auto_set_font_size(False)
        artist.set_fontsize(font_size)

        total_height = sum(row_height_inches)
        normalized_heights = [height / total_height for height in row_height_inches]
        header_color = "#17324D"
        accent_color = "#087E8B"
        emphasized_fill = "#E5F3F5"
        body_fills = ("#FFFFFF", "#F4F7F9")

        for (row_index, column_index), cell in artist.get_celld().items():
            cell.set_edgecolor("#CBD5DD")
            cell.set_linewidth(0.55)
            cell.PAD = 0.075
            cell.set_height(normalized_heights[row_index])
            text = cell.get_text()
            text.set_fontfamily(selected_font)
            text.set_verticalalignment("center")
            if row_index == 0:
                cell.set_facecolor(
                    accent_color if names[column_index] in emphasized else header_color
                )
                text.set_color("white")
                text.set_fontweight("bold")
                text.set_horizontalalignment("left")
            else:
                if names[column_index] in emphasized:
                    cell.set_facecolor(emphasized_fill)
                    text.set_fontweight("semibold")
                else:
                    cell.set_facecolor(body_fills[(row_index - 1) % 2])
                text.set_color("#14212B")
                text.set_horizontalalignment(
                    "right" if names[column_index] in numeric_columns else "left"
                )

        if title:
            figure.text(
                left_inches / figure_width,
                1.0 - 0.16 / figure_height,
                title,
                ha="left",
                va="top",
                fontsize=font_size * 1.35,
                fontweight="bold",
                color="#102A43",
                fontfamily=selected_font,
            )
        if wrapped_note:
            figure.text(
                left_inches / figure_width,
                0.10 / figure_height,
                wrapped_note,
                ha="left",
                va="bottom",
                fontsize=max(5.0, font_size * 0.78),
                color="#52616B",
                linespacing=1.25,
                fontfamily=selected_font,
            )

    return figure


def _validate_table(table: pd.DataFrame) -> None:
    if not isinstance(table, pd.DataFrame):
        raise TypeError("table must be a pandas DataFrame.")
    if table.columns.empty:
        raise ValueError("table must contain at least one column.")
    if table.columns.has_duplicates:
        duplicates = [str(value) for value in table.columns[table.columns.duplicated()]]
        raise ValueError(f"table contains duplicate columns: {duplicates}.")
    if isinstance(table.columns, pd.MultiIndex):
        raise ValueError("MultiIndex columns are not supported for table rendering.")


def _prepare_destination(
    output_path: str | os.PathLike[str], expected_suffix: str
) -> Path:
    try:
        destination = Path(output_path).expanduser()
    except TypeError as exc:
        raise TypeError("output_path must be a string or path-like object.") from exc
    if destination.suffix.lower() != expected_suffix:
        raise ValueError(f"output_path must end in {expected_suffix!r}: {destination}")
    if destination.exists() and destination.is_dir():
        raise IsADirectoryError(f"Output path is a directory: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _normalize_emphasized_columns(
    columns: Iterable[str] | None, available: Sequence[str]
) -> set[str]:
    if columns is None:
        return set()
    if isinstance(columns, str):
        normalized = {columns}
    else:
        try:
            normalized = {str(column) for column in columns}
        except TypeError as exc:
            raise TypeError(
                "emphasized_columns must be an iterable of column names."
            ) from exc
    missing = sorted(normalized - set(available))
    if missing:
        raise ValueError(f"emphasized_columns contains unknown columns: {missing}.")
    return normalized


def _normalize_column_labels(
    labels: Mapping[str, str] | Sequence[str] | None,
    columns: Sequence[str],
) -> list[str]:
    if labels is None:
        return [_humanize_label(column) for column in columns]
    if isinstance(labels, Mapping):
        unknown = sorted(str(key) for key in labels if str(key) not in columns)
        if unknown:
            raise ValueError(f"column_labels contains unknown columns: {unknown}.")
        normalized_mapping = {str(key): str(value) for key, value in labels.items()}
        return [
            normalized_mapping.get(column, _humanize_label(column))
            for column in columns
        ]
    if isinstance(labels, str):
        raise TypeError("column_labels must be a mapping or a sequence of labels.")
    normalized = [str(label) for label in labels]
    if len(normalized) != len(columns):
        raise ValueError(
            "column_labels must contain exactly one label per table column "
            f"({len(columns)} expected, {len(normalized)} received)."
        )
    return normalized


def _normalize_formatters(
    formatters: Mapping[str, Formatter] | None,
    columns: Sequence[str],
) -> dict[str, Formatter]:
    if formatters is None:
        return {}
    if not isinstance(formatters, Mapping):
        raise TypeError("formatters must be a mapping from column names to formatters.")
    normalized: dict[str, Formatter] = {}
    for key, formatter in formatters.items():
        name = str(key)
        if name not in columns:
            raise ValueError(f"formatters contains an unknown column: {name!r}.")
        if not callable(formatter) and not isinstance(formatter, str):
            raise TypeError(
                f"Formatter for {name!r} must be callable or a format string."
            )
        normalized[name] = formatter
    return normalized


def _humanize_label(column: str) -> str:
    tokens = [token for token in re.split(r"[_\s]+", column.strip()) if token]
    if not tokens:
        return column
    rendered = [_ACRONYMS.get(token.casefold(), token) for token in tokens]
    if rendered[0].casefold() not in _ACRONYMS:
        rendered[0] = rendered[0][:1].upper() + rendered[0][1:]
    return " ".join(rendered)


def _column_is_numeric(series: pd.Series) -> bool:
    if is_bool_dtype(series.dtype):
        return False
    if is_numeric_dtype(series.dtype):
        return True
    nonmissing = series[~series.map(_is_missing)]
    if nonmissing.empty:
        return False
    converted = pd.to_numeric(nonmissing, errors="coerce")
    return bool(converted.notna().mean() >= 0.95)


def _format_value(value: Any, column: str, formatter: Formatter | None) -> str:
    if _is_missing(value):
        return _MISSING_DISPLAY
    if formatter is not None:
        try:
            if callable(formatter):
                return str(formatter(value))
            if "{" in formatter:
                return str(formatter.format(value))
            return format(value, formatter)
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            raise ValueError(
                f"Could not apply the display formatter for column {column!r} "
                f"to value {value!r}."
            ) from exc
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if bool(value) else "No"
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, str) and _looks_like_interval(column):
        formatted_interval = _format_percentage_interval(value)
        if formatted_interval is not None:
            return formatted_interval
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isinf(number):
            return "∞" if number > 0 else "−∞"
        normalized_name = column.casefold()
        if _looks_like_rate(normalized_name):
            return f"{number:.1%}" if abs(number) <= 1.0 else f"{number:.1f}%"
        if _looks_like_count(normalized_name):
            return f"{number:,.0f}"
        if _looks_like_minutes(normalized_name):
            return f"{number:,.0f}"
        if _looks_like_distance(normalized_name):
            return f"{number:,.1f}"
        if number == 0:
            return "0"
        if abs(number) < 0.001 or abs(number) >= 1_000_000:
            return f"{number:.3g}"
        return f"{number:,.3f}".rstrip("0").rstrip(".")
    return str(value)


def _looks_like_rate(column: str) -> bool:
    # Match semantic tokens, not arbitrary substrings: ``duration`` contains
    # the letters ``ratio`` but is a time field, not a percentage.
    tokens = set(re.findall(r"[a-z0-9]+", column))
    return bool(
        tokens
        & {"rate", "ratio", "share", "percent", "percentage", "proportion", "pct"}
    ) or any(
        marker in column
        for marker in (
            "confidence_interval_lower",
            "confidence_interval_upper",
            "ci_lower",
            "ci_upper",
        )
    )


def _looks_like_count(column: str) -> bool:
    return any(
        marker in column
        for marker in ("count", "frequency", "sample_size", "seed_number")
    )


def _looks_like_minutes(column: str) -> bool:
    return (
        column.endswith("_min")
        or "minute" in column
        or "duration_min" in column
        or "time_min" in column
    )


def _looks_like_distance(column: str) -> bool:
    return column.endswith("_km") or "distance" in column


def _looks_like_interval(column: str) -> bool:
    return "confidence_interval" in column or bool(
        {"ci", "interval"} <= set(re.findall(r"[a-z0-9]+", column))
    )


def _format_percentage_interval(value: str) -> str | None:
    match = re.fullmatch(
        r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(%?)\s*[-–—]\s*"
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(%?)\s*",
        value,
    )
    if match is None:
        return None
    lower = float(match.group(1))
    upper = float(match.group(3))
    explicitly_percent = bool(match.group(2) or match.group(4))
    if not explicitly_percent and max(abs(lower), abs(upper)) <= 1.0:
        lower *= 100.0
        upper *= 100.0
    return f"{lower:.1f}–{upper:.1f}%"


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return isinstance(result, (bool, np.bool_)) and bool(result)


def _infer_column_widths(
    columns: Sequence[str],
    labels: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    numeric_columns: set[str],
) -> list[float]:
    widths: list[float] = []
    for index, (column, label) in enumerate(zip(columns, labels, strict=True)):
        measured = [_longest_line_width(label)]
        measured.extend(_longest_line_width(row[index]) for row in rows)
        if len(measured) > 2:
            representative = float(np.quantile(measured, 0.90, method="higher"))
        else:
            representative = float(max(measured, default=1))
        if column in numeric_columns:
            widths.append(min(18.0, max(8.0, representative + 1.5)))
        else:
            widths.append(min(36.0, max(11.0, representative + 1.5)))
    return widths


def _display_width(text: str) -> int:
    width = 0
    for character in text:
        if character == "\t":
            width += 4
        elif unicodedata.east_asian_width(character) in {"F", "W"}:
            width += 2
        elif unicodedata.combining(character):
            continue
        else:
            width += 1
    return width


def _longest_line_width(text: str) -> int:
    return max((_display_width(line) for line in str(text).splitlines()), default=0)


def _wrap_text(value: str, maximum_width: int) -> str:
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    if not text:
        return ""
    return "\n".join(
        line
        for paragraph in text.split("\n")
        for line in (_wrap_paragraph(paragraph, maximum_width) or [""])
    )


def _wrap_paragraph(paragraph: str, maximum_width: int) -> list[str]:
    remaining = paragraph.strip()
    if not remaining:
        return []
    lines: list[str] = []
    while _display_width(remaining) > maximum_width:
        consumed_width = 0
        hard_break = 0
        preferred_break = 0
        for index, character in enumerate(remaining, start=1):
            character_width = _display_width(character)
            if consumed_width + character_width > maximum_width:
                break
            consumed_width += character_width
            hard_break = index
            if character in _BREAK_AFTER:
                preferred_break = index
        minimum_preferred = max(1, int(hard_break * 0.55))
        cut = preferred_break if preferred_break >= minimum_preferred else hard_break
        if cut <= 0:  # A single unusual glyph wider than the requested width.
            cut = 1
        lines.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining or not lines:
        lines.append(remaining)
    return lines


def _line_count(text: str) -> int:
    return max(1, str(text).count("\n") + 1)


def _height_for_lines(
    lines: int, font_size: float, *, is_header: bool = False
) -> float:
    line_height = float(font_size) * (1.38 if is_header else 1.31) / 72.0
    padding = 0.18 if is_header else 0.14
    minimum = 0.42 if is_header else 0.32
    return max(minimum, lines * line_height + padding)


@lru_cache(maxsize=16)
def _select_japanese_font(preferred: str | None = None) -> str:
    installed = {
        entry.name.casefold(): entry.name for entry in font_manager.fontManager.ttflist
    }
    if preferred:
        matched = installed.get(preferred.casefold())
        if matched:
            return matched
    for candidate in _JAPANESE_FONT_CANDIDATES:
        matched = installed.get(candidate.casefold())
        if matched:
            return matched
    warnings.warn(
        "No known Japanese-capable font was found. Install Noto Sans CJK JP "
        "or IPAexGothic to guarantee Japanese glyph coverage.",
        RuntimeWarning,
        stacklevel=2,
    )
    return installed.get("dejavu sans", "DejaVu Sans")


def _atomic_save_figure(
    figure: Figure,
    destination: Path,
    *,
    file_format: Literal["png", "svg"],
    dpi: int,
) -> None:
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.stem}.",
        suffix=f".tmp.{file_format}",
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        # SVG serialization consults rcParams at save time, after the local
        # context used to construct the figure has exited. Re-apply this one
        # setting here so labels remain editable ``<text>`` elements.
        save_context = {"svg.fonttype": "none"} if file_format == "svg" else {}
        with rc_context(save_context):
            figure.savefig(
                temporary_path,
                format=file_format,
                dpi=dpi,
                facecolor="white",
                edgecolor="none",
                metadata={"Creator": "table_rendering_utils.py"},
            )
        with temporary_path.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        _fsync_directory(destination.parent)
    except BaseException:
        with suppress(FileNotFoundError):
            temporary_path.unlink()
        raise


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory fsync after an atomic replace."""

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


__all__ = [
    "DEFAULT_RESEARCH_NOTE",
    "export_table_as_csv",
    "render_table_as_png",
    "render_table_as_svg",
]
