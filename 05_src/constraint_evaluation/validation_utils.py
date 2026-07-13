"""Validation and integrity helpers for the synthetic Tokyo EVRP pipeline.

The helpers in this module deliberately distinguish an allowed empty result
(a CSV with a valid header and zero data rows) from an incomplete or invalid
artifact.  All functions are standalone: importing this file does not depend
on the notebook, repository package layout, or process working directory.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import tempfile
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, TypeAlias

import pandas as pd


PathLike: TypeAlias = str | os.PathLike[str]

MANIFEST_COLUMNS: Final[tuple[str, ...]] = (
    "path",
    "relative_path",
    "file_type",
    "size_bytes",
    "modified_at_utc",
    "sha256",
    "row_count",
    "column_count",
    "status",
    "generated_at_utc",
)
_HASH_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-fA-F]{64}$")
_COMMON_DELIMITERS: Final[tuple[str, ...]] = (",", "\t", ";", "|")


class ValidationError(ValueError):
    """Base class for data and artifact validation failures."""


class CSVValidationError(ValidationError):
    """Base class for failures involving a CSV artifact."""


class EmptyCSVFileError(CSVValidationError):
    """Raised when a CSV is zero bytes or contains no parseable header."""


class HeaderOnlyCSVError(CSVValidationError):
    """Raised when a header-only CSV is used where data rows are required."""


class CSVSchemaError(CSVValidationError):
    """Raised when a CSV or DataFrame does not have the required schema."""


class CSVEncodingError(CSVValidationError):
    """Raised when CSV bytes cannot be decoded with the requested encoding."""


class CSVDelimiterError(CSVValidationError):
    """Raised when a CSV delimiter or record structure cannot be parsed."""


class CSVTypeError(CSVValidationError):
    """Raised when a column contains values incompatible with its type."""


class DuplicateKeyError(CSVValidationError):
    """Raised when a supposedly unique key contains duplicate records."""


class ManifestValidationError(ValidationError):
    """Raised when an output manifest is invalid or no longer matches files."""


def find_repository_root(start: PathLike | None = None) -> Path:
    """Find the nearest ancestor containing a ``.git`` marker.

    Parameters
    ----------
    start:
        A file or directory from which to search.  If omitted, the current
        working directory is used.  A non-existent path is treated as a path
        location, so its existing ancestors can still be searched.

    Returns
    -------
    pathlib.Path
        The absolute repository-root path.

    Raises
    ------
    RuntimeError
        If no ``.git`` file or directory exists at or above ``start``.
    """

    raw_start = Path.cwd() if start is None else Path(start).expanduser()
    resolved = raw_start.resolve(strict=False)
    search_from = resolved.parent if resolved.is_file() else resolved

    for candidate in (search_from, *search_from.parents):
        if (candidate / ".git").exists():
            return candidate

    raise RuntimeError(
        f"Repository root could not be found from {resolved}. "
        "No .git marker exists in that path or any parent."
    )


def _source_label(source: PathLike | None) -> str:
    """Return a concise source label for validation messages."""

    return str(Path(source).expanduser()) if source is not None else "DataFrame"


def _normalise_columns(columns: Sequence[str] | str, *, argument: str) -> list[str]:
    """Normalise a single column or sequence and reject ambiguous requests."""

    if isinstance(columns, str):
        result = [columns]
    else:
        result = list(columns)
    if not result:
        raise ValueError(f"{argument} must contain at least one column name.")
    if any(not isinstance(column, str) or not column for column in result):
        raise TypeError(f"{argument} must contain non-empty string column names.")
    duplicates = sorted({column for column in result if result.count(column) > 1})
    if duplicates:
        raise ValueError(f"{argument} contains duplicate names: {duplicates}.")
    return result


def validate_required_columns(
    frame: pd.DataFrame,
    required_columns: Sequence[str] | str,
    source: PathLike | None = None,
) -> pd.DataFrame:
    """Validate that a DataFrame contains every required column exactly once.

    Extra columns are permitted.  The original DataFrame is returned to allow
    validation calls to be composed; it is never modified.

    Raises
    ------
    CSVSchemaError
        If required columns are missing or the DataFrame has duplicate labels.
    """

    if not isinstance(frame, pd.DataFrame):
        raise TypeError(
            f"frame must be a pandas DataFrame, got {type(frame).__name__}."
        )
    required = _normalise_columns(required_columns, argument="required_columns")
    label = _source_label(source)

    duplicate_labels = list(frame.columns[frame.columns.duplicated()].unique())
    if duplicate_labels:
        raise CSVSchemaError(
            f"CSV schema validation failed for {label}: duplicate column labels "
            f"{duplicate_labels}."
        )

    missing = [column for column in required if column not in frame.columns]
    if missing:
        available = [str(column) for column in frame.columns]
        raise CSVSchemaError(
            f"CSV schema validation failed for {label}: missing required columns "
            f"{missing}. Available columns: {available}."
        )
    return frame


def validate_nonempty_when_required(
    frame: pd.DataFrame,
    required: bool = True,
    source: PathLike | None = None,
) -> pd.DataFrame:
    """Reject a zero-row DataFrame only when non-empty data is required.

    A zero-row DataFrame with columns is a header-only CSV representation and
    can be a valid empty analysis result when ``required`` is ``False``.  A
    DataFrame with neither rows nor columns is invalid regardless of the flag,
    because it has no schema that downstream code can validate.

    Raises
    ------
    EmptyCSVFileError
        If the DataFrame has neither a header nor rows.
    HeaderOnlyCSVError
        If it has a header but no rows and ``required`` is true.
    """

    if not isinstance(frame, pd.DataFrame):
        raise TypeError(
            f"frame must be a pandas DataFrame, got {type(frame).__name__}."
        )
    label = _source_label(source)
    if frame.shape == (0, 0):
        raise EmptyCSVFileError(
            f"CSV validation failed for {label}: no header or data rows were found."
        )
    if required and frame.empty:
        raise HeaderOnlyCSVError(
            f"CSV is header-only for {label}: 0 data rows were found, but non-empty "
            f"data is required. Columns: {[str(column) for column in frame.columns]}."
        )
    return frame


def validate_numeric_columns(
    frame: pd.DataFrame,
    numeric_columns: Sequence[str] | str,
    source: PathLike | None = None,
    *,
    allow_missing: bool = True,
    allow_infinite: bool = False,
) -> pd.DataFrame:
    """Validate that selected columns contain numeric or missing values.

    Numeric strings such as ``"12.5"`` are accepted, but the DataFrame is not
    coerced or modified.  Booleans are rejected because they usually indicate
    a schema error in quantitative EVRP outputs.

    Parameters
    ----------
    allow_missing:
        Whether null values are permitted.
    allow_infinite:
        Whether positive or negative infinity is permitted.

    Raises
    ------
    CSVSchemaError
        If a selected column is absent.
    CSVTypeError
        If a present value is non-numeric, disallowed missing, or infinite.
    """

    columns = _normalise_columns(numeric_columns, argument="numeric_columns")
    validate_required_columns(frame, columns, source)
    label = _source_label(source)

    failures: list[str] = []
    for column in columns:
        series = frame[column]
        bool_mask = series.map(lambda value: isinstance(value, bool)) & series.notna()
        converted = pd.to_numeric(series.mask(bool_mask), errors="coerce")
        real_compatible = converted.map(_is_real_number_or_missing)
        finite = converted.map(_is_finite_real_number_or_missing)
        invalid_mask = series.notna() & (
            converted.isna() | bool_mask | ~real_compatible
        )
        missing_mask = series.isna()
        infinite_mask = converted.notna() & real_compatible & ~finite

        problems = invalid_mask.copy()
        if not allow_missing:
            problems |= missing_mask
        if not allow_infinite:
            problems |= infinite_mask
        if problems.any():
            positions = [
                str(position) for position in frame.index[problems][:5].tolist()
            ]
            values = [repr(value) for value in series[problems].head(5).tolist()]
            reasons: list[str] = []
            if invalid_mask.any():
                reasons.append("non-numeric values")
            if not allow_missing and missing_mask.any():
                reasons.append("missing values")
            if not allow_infinite and infinite_mask.any():
                reasons.append("infinite values")
            failures.append(
                f"{column!r} ({', '.join(reasons)} at indices {positions}; "
                f"sample values {values})"
            )

    if failures:
        raise CSVTypeError(
            f"CSV numeric type validation failed for {label}: "
            + "; ".join(failures)
            + "."
        )
    return frame


def _is_real_number_or_missing(value: Any) -> bool:
    """Return whether a converted scalar is missing or representable as real."""

    if pd.isna(value):
        return True
    try:
        float(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return True


def _is_finite_real_number_or_missing(value: Any) -> bool:
    """Return whether a converted scalar is missing or a finite real number."""

    if pd.isna(value):
        return True
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def validate_unique_keys(
    frame: pd.DataFrame,
    key_columns: Sequence[str] | str,
    source: PathLike | None = None,
    *,
    allow_missing: bool = False,
) -> pd.DataFrame:
    """Validate uniqueness and completeness of a single or composite key.

    Parameters
    ----------
    key_columns:
        One column name or the ordered columns forming a composite key.
    allow_missing:
        If false (the default), a null in any key component is invalid.

    Raises
    ------
    CSVSchemaError
        If a key column is absent.
    CSVTypeError
        If a key has missing components and missing keys are disallowed.
    DuplicateKeyError
        If two or more rows share the same key.
    """

    keys = _normalise_columns(key_columns, argument="key_columns")
    validate_required_columns(frame, keys, source)
    label = _source_label(source)

    missing_mask = frame[keys].isna().any(axis=1)
    if not allow_missing and missing_mask.any():
        positions = [
            str(position) for position in frame.index[missing_mask][:5].tolist()
        ]
        raise CSVTypeError(
            f"CSV key validation failed for {label}: key columns {keys} contain "
            f"missing values in {int(missing_mask.sum())} row(s); sample indices {positions}."
        )

    candidate = frame.loc[~missing_mask] if allow_missing else frame
    duplicated = candidate.duplicated(subset=keys, keep=False)
    if duplicated.any():
        duplicate_rows = (
            candidate.loc[duplicated, keys].head(5).to_dict(orient="records")
        )
        duplicate_key_count = int(
            candidate.loc[duplicated, keys].drop_duplicates().shape[0]
        )
        raise DuplicateKeyError(
            f"CSV key validation failed for {label}: {duplicate_key_count} duplicate "
            f"key value(s) across {int(duplicated.sum())} row(s) for columns {keys}. "
            f"Sample duplicate keys: {duplicate_rows}."
        )
    return frame


def _probable_delimiter(
    path: Path,
    *,
    encoding: str,
    requested_delimiter: str | None,
) -> str | None:
    """Infer a likely common delimiter without masking a schema error."""

    try:
        with path.open("r", encoding=encoding, newline="") as stream:
            first_line = stream.readline()
    except (OSError, UnicodeError):
        return None
    if not first_line:
        return None

    best_delimiter: str | None = None
    best_width = 1
    for delimiter in _COMMON_DELIMITERS:
        if delimiter == requested_delimiter:
            continue
        try:
            width = len(next(csv.reader([first_line], delimiter=delimiter)))
        except (csv.Error, StopIteration):
            continue
        if width > best_width:
            best_delimiter = delimiter
            best_width = width
    return best_delimiter


def read_csv_checked(
    path: PathLike,
    required_columns: Sequence[str] | str | None = None,
    *,
    require_nonempty: bool = False,
    allow_empty: bool | None = None,
    numeric_columns: Sequence[str] | str | None = None,
    unique_keys: Sequence[str] | str | None = None,
    allow_missing_numeric: bool = True,
    allow_infinite_numeric: bool = False,
    allow_missing_keys: bool = False,
    encoding: str = "utf-8",
    delimiter: str | None = ",",
    **read_csv_kwargs: Any,
) -> pd.DataFrame:
    """Read a CSV and validate its physical state, schema, and selected types.

    The function distinguishes the following cases with explicit exceptions:

    * missing path: :class:`FileNotFoundError`;
    * zero-byte or headerless file: :class:`EmptyCSVFileError`;
    * valid header with no rows when rows are required:
      :class:`HeaderOnlyCSVError`;
    * missing/duplicate columns: :class:`CSVSchemaError`;
    * decoding failure: :class:`CSVEncodingError`;
    * wrong delimiter or malformed records: :class:`CSVDelimiterError`;
    * incompatible ``dtype`` or numeric values: :class:`CSVTypeError`.

    A header-only CSV is returned normally when ``require_nonempty`` is false;
    its ``DataFrame.attrs['csv_state']`` value is ``"header_only"``.  This is
    how a legitimate empty analysis result remains distinct from a failed
    zero-byte output.

    ``allow_empty`` is a compatibility inverse of ``require_nonempty``.  It is
    useful for callers whose APIs already use that spelling; specifying
    contradictory values is rejected.
    """

    csv_path = Path(path).expanduser()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file is missing: {csv_path}.")
    if not csv_path.is_file():
        raise CSVValidationError(f"CSV path is not a regular file: {csv_path}.")
    if csv_path.stat().st_size == 0:
        raise EmptyCSVFileError(f"CSV file is zero bytes: {csv_path}.")

    if allow_empty is not None:
        inverse = not allow_empty
        if require_nonempty and not inverse:
            raise ValueError(
                "Contradictory empty-data options: require_nonempty=True and "
                "allow_empty=True."
            )
        require_nonempty = inverse

    kwargs = dict(read_csv_kwargs)
    if "encoding" in kwargs:
        raise TypeError(
            "Pass encoding via the encoding parameter, not read_csv_kwargs."
        )
    kwargs["encoding"] = encoding
    if "delimiter" in kwargs:
        raise TypeError(
            "Pass delimiter via the delimiter parameter, not read_csv_kwargs."
        )
    if "sep" not in kwargs and delimiter is not None:
        kwargs["sep"] = delimiter
    requested_delimiter = kwargs.get("sep", delimiter)

    try:
        frame = pd.read_csv(csv_path, **kwargs)
    except UnicodeDecodeError as exc:
        raise CSVEncodingError(
            f"CSV encoding error for {csv_path} using encoding={encoding!r}: {exc}."
        ) from exc
    except pd.errors.EmptyDataError as exc:
        raise EmptyCSVFileError(
            f"CSV contains no parseable header or data rows: {csv_path}. "
            "The file is non-zero in size but empty or whitespace-only."
        ) from exc
    except pd.errors.ParserError as exc:
        raise CSVDelimiterError(
            f"CSV delimiter/record parsing error for {csv_path} using "
            f"delimiter={requested_delimiter!r}: {exc}."
        ) from exc
    except UnicodeError as exc:
        raise CSVEncodingError(
            f"CSV encoding error for {csv_path} using encoding={encoding!r}: {exc}."
        ) from exc
    except (TypeError, ValueError) as exc:
        if "dtype" in kwargs or "converters" in kwargs:
            raise CSVTypeError(
                f"CSV type conversion failed for {csv_path}: {exc}."
            ) from exc
        raise CSVValidationError(
            f"CSV could not be read from {csv_path}: {exc}."
        ) from exc

    # Pandas normally mangles duplicate CSV headers (for example ``id`` and
    # ``id.1``).  Parse the physical header too so malformed schemas are not
    # silently accepted as distinct columns.
    header_setting = kwargs.get("header", "infer")
    uses_physical_first_line_header = (
        (header_setting == "infer" or header_setting == 0)
        and not kwargs.get("names")
        and not kwargs.get("skiprows")
        and not kwargs.get("comment")
    )
    if uses_physical_first_line_header:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as stream:
                header_line = stream.readline()
            if isinstance(requested_delimiter, str) and len(requested_delimiter) == 1:
                physical_header = next(
                    csv.reader([header_line], delimiter=requested_delimiter), []
                )
                if physical_header:
                    physical_header[0] = physical_header[0].lstrip("\ufeff")
                duplicate_headers = sorted(
                    {
                        name
                        for name in physical_header
                        if physical_header.count(name) > 1
                    }
                )
                if duplicate_headers:
                    raise CSVSchemaError(
                        f"CSV schema validation failed for {csv_path}: duplicate header "
                        f"names {duplicate_headers}."
                    )
        except UnicodeDecodeError as exc:
            raise CSVEncodingError(
                f"CSV encoding error for {csv_path} using encoding={encoding!r}: {exc}."
            ) from exc

    if required_columns is not None:
        try:
            validate_required_columns(frame, required_columns, csv_path)
        except CSVSchemaError as exc:
            probable = _probable_delimiter(
                csv_path,
                encoding=encoding,
                requested_delimiter=(
                    requested_delimiter
                    if isinstance(requested_delimiter, str)
                    and len(requested_delimiter) == 1
                    else None
                ),
            )
            if probable is not None and len(frame.columns) <= 1:
                raise CSVDelimiterError(
                    f"CSV delimiter appears incorrect for {csv_path}: requested "
                    f"{requested_delimiter!r}, but the header is consistent with "
                    f"{probable!r}."
                ) from exc
            raise

    if numeric_columns is not None:
        validate_numeric_columns(
            frame,
            numeric_columns,
            csv_path,
            allow_missing=allow_missing_numeric,
            allow_infinite=allow_infinite_numeric,
        )
    if unique_keys is not None:
        validate_unique_keys(
            frame,
            unique_keys,
            csv_path,
            allow_missing=allow_missing_keys,
        )
    validate_nonempty_when_required(frame, require_nonempty, csv_path)

    frame.attrs["csv_state"] = "header_only" if frame.empty else "data"
    frame.attrs["source_path"] = str(csv_path.resolve())
    return frame


def write_csv_atomic(
    frame: pd.DataFrame,
    path: PathLike,
    *,
    index: bool = False,
    encoding: str = "utf-8",
    create_parent: bool = True,
    **to_csv_kwargs: Any,
) -> Path:
    """Write a DataFrame to CSV atomically using a same-directory temp file.

    The destination is replaced only after ``DataFrame.to_csv`` completes and
    the temporary file is flushed to disk.  If writing fails, any existing
    destination is left untouched and the temporary file is removed.

    Returns
    -------
    pathlib.Path
        The destination path as supplied (with ``~`` expanded).
    """

    if not isinstance(frame, pd.DataFrame):
        raise TypeError(
            f"frame must be a pandas DataFrame, got {type(frame).__name__}."
        )
    destination = Path(path).expanduser()
    parent = destination.parent
    if create_parent:
        parent.mkdir(parents=True, exist_ok=True)
    elif not parent.is_dir():
        raise FileNotFoundError(f"CSV output directory does not exist: {parent}.")
    if destination.exists() and destination.is_dir():
        raise IsADirectoryError(f"CSV destination is a directory: {destination}.")

    suffix = "".join(destination.suffixes) or ".tmp"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=parent,
        prefix=f".{destination.name}.",
        suffix=suffix,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        frame.to_csv(
            temporary,
            index=index,
            encoding=encoding,
            **to_csv_kwargs,
        )
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        try:
            directory_descriptor = os.open(parent, os.O_RDONLY)
        except OSError:
            directory_descriptor = None
        if directory_descriptor is not None:
            try:
                try:
                    os.fsync(directory_descriptor)
                except OSError:
                    # The replacement is already complete.  Some filesystems
                    # do not support fsync on directories, so this durability
                    # enhancement must remain best-effort.
                    pass
            finally:
                os.close(directory_descriptor)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def atomic_write_csv(
    frame: pd.DataFrame,
    path: PathLike,
    *,
    index: bool = False,
    encoding: str = "utf-8",
    create_parent: bool = True,
    **to_csv_kwargs: Any,
) -> Path:
    """Compatibility alias for :func:`write_csv_atomic`."""

    return write_csv_atomic(
        frame,
        path,
        index=index,
        encoding=encoding,
        create_parent=create_parent,
        **to_csv_kwargs,
    )


def file_sha256(path: PathLike, *, chunk_size: int = 1024 * 1024) -> str:
    """Return the lowercase SHA-256 digest of a regular file.

    The file is streamed in chunks so large figures and data outputs do not
    need to be loaded into memory.
    """

    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}.")
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"File is missing and cannot be hashed: {file_path}.")
    if not file_path.is_file():
        raise IsADirectoryError(f"SHA-256 input is not a regular file: {file_path}.")

    digest = hashlib.sha256()
    with file_path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_file(path: PathLike, *, chunk_size: int = 1024 * 1024) -> str:
    """Compatibility alias for :func:`file_sha256`."""

    return file_sha256(path, chunk_size=chunk_size)


def _expand_paths(
    paths: Iterable[PathLike] | PathLike, *, recursive: bool
) -> list[Path]:
    """Expand file/directory inputs into a deterministic, unique file list."""

    if isinstance(paths, (str, os.PathLike)):
        requested = [Path(paths).expanduser()]
    else:
        requested = [Path(path).expanduser() for path in paths]
    if not requested:
        raise ValueError("At least one output path is required to generate a manifest.")

    files: list[Path] = []
    for requested_path in requested:
        if not requested_path.exists():
            raise FileNotFoundError(f"Output path is missing: {requested_path}.")
        if requested_path.is_dir():
            iterator = (
                requested_path.rglob("*") if recursive else requested_path.glob("*")
            )
            files.extend(path for path in iterator if path.is_file())
        elif requested_path.is_file():
            files.append(requested_path)
        else:
            raise ValidationError(
                f"Output path is not a regular file or directory: {requested_path}."
            )

    return sorted(
        {path.resolve() for path in files}, key=lambda value: value.as_posix()
    )


def _default_manifest_root(files: Sequence[Path], requested: object) -> Path:
    """Choose a stable root when a caller does not explicitly provide one."""

    if isinstance(requested, (str, os.PathLike)):
        requested_path = Path(requested).expanduser().resolve(strict=False)
        if requested_path.is_dir():
            try:
                return find_repository_root(requested_path)
            except RuntimeError:
                return requested_path
    if not files:
        return Path.cwd().resolve()
    try:
        return find_repository_root(files[0])
    except RuntimeError:
        common = Path(os.path.commonpath([str(path.parent) for path in files]))
        return common.resolve()


def _path_within(path: Path, parent: Path) -> bool:
    """Return whether a resolved path is equal to or contained by a parent."""

    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _normalise_deprecated_paths(
    deprecated_paths: Iterable[PathLike],
    *,
    root: Path,
) -> list[Path]:
    """Resolve deprecated file or directory markers against a manifest root."""

    resolved: list[Path] = []
    for value in deprecated_paths:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = root / path
        resolved.append(path.resolve(strict=False))
    return resolved


def generate_output_manifest(
    paths: Iterable[PathLike] | PathLike,
    manifest_path: PathLike | None = None,
    *,
    root: PathLike | None = None,
    recursive: bool = True,
    deprecated_paths: Iterable[PathLike] = (),
    include_csv_shape: bool = True,
) -> pd.DataFrame:
    """Generate a deterministic integrity manifest for output artifacts.

    Parameters
    ----------
    paths:
        A file, directory, or iterable of either.  Directories are expanded
        recursively by default.
    manifest_path:
        Optional CSV destination.  The manifest never lists itself because its
        digest would otherwise be self-referential.
    root:
        Root against which manifest paths are stored.  Every output must be
        contained by it.  If omitted, the repository root is used when found;
        otherwise a stable common/input directory is selected.
    deprecated_paths:
        Files or directories to mark ``deprecated``.  Deprecated artifacts are
        retained for provenance but are ignored by current-output validation by
        default.
    include_csv_shape:
        If true, parse CSV outputs and record exact row and column counts.

    Returns
    -------
    pandas.DataFrame
        One row per artifact with path, size, UTC modification time, SHA-256,
        optional CSV dimensions, and active/deprecated status.
    """

    files = _expand_paths(paths, recursive=recursive)
    manifest_destination = (
        Path(manifest_path).expanduser().resolve(strict=False)
        if manifest_path is not None
        else None
    )
    if manifest_destination is not None:
        files = [path for path in files if path != manifest_destination]
    if not files:
        raise ManifestValidationError(
            "No output files remain to include in the manifest after exclusions."
        )

    manifest_root = (
        Path(root).expanduser().resolve(strict=False)
        if root is not None
        else _default_manifest_root(files, paths)
    )
    outside = [path for path in files if not _path_within(path, manifest_root)]
    if outside:
        raise ManifestValidationError(
            f"Output files must be inside manifest root {manifest_root}; outside paths: "
            f"{[str(path) for path in outside[:5]]}."
        )

    deprecated = _normalise_deprecated_paths(deprecated_paths, root=manifest_root)
    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for output_path in files:
        stat = output_path.stat()
        relative = output_path.relative_to(manifest_root).as_posix()
        is_deprecated = any(_path_within(output_path, marker) for marker in deprecated)
        row_count: object = pd.NA
        column_count: object = pd.NA
        if include_csv_shape and output_path.suffix.lower() == ".csv":
            csv_frame = read_csv_checked(output_path, require_nonempty=False)
            row_count = int(csv_frame.shape[0])
            column_count = int(csv_frame.shape[1])
        rows.append(
            {
                "path": relative,
                "relative_path": relative,
                "file_type": output_path.suffix.lower().lstrip(".") or "no_extension",
                "size_bytes": int(stat.st_size),
                "modified_at_utc": pd.Timestamp(
                    stat.st_mtime_ns, unit="ns", tz="UTC"
                ).isoformat(),
                "sha256": file_sha256(output_path),
                "row_count": row_count,
                "column_count": column_count,
                "status": "deprecated" if is_deprecated else "active",
                "generated_at_utc": generated_at,
            }
        )

    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    manifest["row_count"] = manifest["row_count"].astype("Int64")
    manifest["column_count"] = manifest["column_count"].astype("Int64")
    validate_unique_keys(manifest, "path", "generated output manifest")
    manifest.attrs["manifest_root"] = str(manifest_root)
    if manifest_destination is not None:
        write_csv_atomic(manifest, manifest_destination, index=False)
    return manifest


def _read_manifest(
    manifest: pd.DataFrame | PathLike,
) -> tuple[pd.DataFrame, Path | None]:
    """Load a manifest while preserving path and digest strings exactly."""

    if isinstance(manifest, pd.DataFrame):
        return manifest.copy(), None
    manifest_path = Path(manifest).expanduser()
    frame = read_csv_checked(
        manifest_path,
        require_nonempty=True,
        dtype={
            "path": "string",
            "relative_path": "string",
            "sha256": "string",
            "status": "string",
        },
    )
    return frame, manifest_path.resolve()


def _manifest_root(manifest_path: Path | None, explicit_root: PathLike | None) -> Path:
    """Resolve the root used to interpret relative paths in a manifest."""

    if explicit_root is not None:
        return Path(explicit_root).expanduser().resolve(strict=False)
    if manifest_path is not None:
        try:
            return find_repository_root(manifest_path)
        except RuntimeError:
            return manifest_path.parent
    return Path.cwd().resolve()


def _resolve_manifest_entry(raw_path: object, *, root: Path) -> Path:
    """Resolve one manifest entry and prevent root traversal."""

    if pd.isna(raw_path) or not str(raw_path).strip():
        raise ManifestValidationError("Output manifest contains a blank path value.")
    path = Path(str(raw_path)).expanduser()
    resolved = (
        path.resolve(strict=False)
        if path.is_absolute()
        else (root / path).resolve(strict=False)
    )
    if not _path_within(resolved, root):
        raise ManifestValidationError(
            f"Manifest path escapes root {root}: {raw_path!r} resolves to {resolved}."
        )
    return resolved


def _normalise_required_manifest_path(path: PathLike, *, root: Path) -> str:
    """Convert a required path to the relative spelling used by a manifest."""

    value = Path(path).expanduser()
    resolved = (
        value.resolve(strict=False)
        if value.is_absolute()
        else (root / value).resolve(strict=False)
    )
    if not _path_within(resolved, root):
        raise ManifestValidationError(
            f"Required output path is outside manifest root {root}: {resolved}."
        )
    return resolved.relative_to(root).as_posix()


def validate_output_manifest(
    manifest: pd.DataFrame | PathLike,
    *,
    root: PathLike | None = None,
    required_paths: Iterable[PathLike] = (),
    verify_hashes: bool = True,
    verify_size: bool = True,
    verify_modified_time: bool = True,
    verify_csv_shape: bool = True,
    include_deprecated: bool = False,
) -> pd.DataFrame:
    """Validate an output manifest against the files currently on disk.

    Active rows are checked for existence and, by default, exact size, SHA-256,
    modification time, and recorded CSV dimensions.  Rows whose status is
    ``deprecated`` are retained in the returned DataFrame but are excluded from
    success criteria unless ``include_deprecated`` is true.

    Parameters
    ----------
    manifest:
        A manifest DataFrame or manifest CSV path.
    root:
        Root for relative artifact paths.  If omitted for a CSV inside a Git
        repository, the repository root is discovered automatically; outside a
        repository the manifest's parent is used.
    required_paths:
        Outputs that must have an active manifest row.

    Returns
    -------
    pandas.DataFrame
        A validated copy of the manifest.  ``attrs`` records the resolved root,
        active/deprecated counts, and ``validation_status='valid'``.

    Raises
    ------
    ManifestValidationError
        If the manifest schema is invalid, a required active row is absent, or
        any checked file metadata differs from the manifest.
    """

    frame, manifest_path = _read_manifest(manifest)
    path_column = "path" if "path" in frame.columns else "relative_path"
    required_columns = [path_column, "size_bytes", "sha256"]
    try:
        validate_required_columns(
            frame, required_columns, manifest_path or "manifest DataFrame"
        )
        validate_unique_keys(frame, path_column, manifest_path or "manifest DataFrame")
        validate_numeric_columns(
            frame,
            "size_bytes",
            manifest_path or "manifest DataFrame",
            allow_missing=False,
            allow_infinite=False,
        )
    except CSVValidationError as exc:
        raise ManifestValidationError(
            f"Output manifest schema is invalid: {exc}"
        ) from exc

    if "status" not in frame.columns:
        frame["status"] = "active"
    statuses = frame["status"].fillna("").astype(str).str.strip().str.lower()
    invalid_statuses = sorted(set(statuses) - {"active", "deprecated"})
    if invalid_statuses:
        raise ManifestValidationError(
            f"Output manifest contains unsupported status values {invalid_statuses}; "
            "expected 'active' or 'deprecated'."
        )

    root_hint: PathLike | None = root
    if root_hint is None and manifest_path is None:
        stored_root = frame.attrs.get("manifest_root")
        if isinstance(stored_root, (str, os.PathLike)):
            root_hint = stored_root
    manifest_root = _manifest_root(manifest_path, root_hint)
    active_paths: set[str] = set()
    failures: list[str] = []
    for position, (_, row) in enumerate(frame.iterrows(), start=2):
        status = str(row["status"]).strip().lower()
        raw_path = row[path_column]
        try:
            output_path = _resolve_manifest_entry(raw_path, root=manifest_root)
        except ManifestValidationError as exc:
            failures.append(f"row {position}: {exc}")
            continue
        relative = output_path.relative_to(manifest_root).as_posix()
        if status == "active":
            active_paths.add(relative)
        if status == "deprecated" and not include_deprecated:
            continue
        if manifest_path is not None and output_path == manifest_path:
            failures.append(
                f"row {position} ({relative}): a manifest cannot validate its own digest."
            )
            continue
        if not output_path.exists():
            failures.append(f"row {position} ({relative}): file is missing.")
            continue
        if not output_path.is_file():
            failures.append(f"row {position} ({relative}): path is not a regular file.")
            continue

        stat = output_path.stat()
        if verify_size:
            try:
                size_value = float(row["size_bytes"])
            except (TypeError, ValueError, OverflowError):
                failures.append(
                    f"row {position} ({relative}): invalid size_bytes={row['size_bytes']!r}."
                )
            else:
                if (
                    isinstance(row["size_bytes"], bool)
                    or not math.isfinite(size_value)
                    or not size_value.is_integer()
                ):
                    failures.append(
                        f"row {position} ({relative}): size_bytes must be an integer."
                    )
                elif size_value < 0:
                    failures.append(
                        f"row {position} ({relative}): size_bytes cannot be negative."
                    )
                elif stat.st_size != int(size_value):
                    failures.append(
                        f"row {position} ({relative}): size mismatch; manifest "
                        f"{int(size_value)}, current {stat.st_size}."
                    )

        expected_hash = str(row["sha256"]).strip().lower()
        if not _HASH_PATTERN.fullmatch(expected_hash):
            failures.append(
                f"row {position} ({relative}): sha256 must contain 64 hexadecimal characters."
            )
        elif verify_hashes:
            current_hash = file_sha256(output_path)
            if current_hash != expected_hash:
                failures.append(
                    f"row {position} ({relative}): SHA-256 mismatch; manifest "
                    f"{expected_hash}, current {current_hash}."
                )

        if verify_modified_time and "modified_at_utc" in frame.columns:
            expected_time = row["modified_at_utc"]
            if pd.isna(expected_time):
                failures.append(
                    f"row {position} ({relative}): modified_at_utc is missing."
                )
            else:
                try:
                    parsed_time = pd.Timestamp(expected_time)
                    if parsed_time.tzinfo is None:
                        parsed_time = parsed_time.tz_localize("UTC")
                    else:
                        parsed_time = parsed_time.tz_convert("UTC")
                    current_time = pd.Timestamp(stat.st_mtime_ns, unit="ns", tz="UTC")
                    parsed_ns = parsed_time.value
                    current_ns = current_time.value
                    if parsed_ns != current_ns:
                        failures.append(
                            f"row {position} ({relative}): modification-time mismatch; "
                            f"manifest {expected_time}, current {current_time.isoformat()}."
                        )
                except (TypeError, ValueError, OverflowError) as exc:
                    failures.append(
                        f"row {position} ({relative}): invalid modified_at_utc "
                        f"{expected_time!r} ({exc})."
                    )

        if verify_csv_shape and output_path.suffix.lower() == ".csv":
            try:
                csv_frame = read_csv_checked(output_path, require_nonempty=False)
            except (FileNotFoundError, CSVValidationError) as exc:
                failures.append(f"row {position} ({relative}): invalid CSV ({exc}).")
            else:
                for field, current_value in (
                    ("row_count", csv_frame.shape[0]),
                    ("column_count", csv_frame.shape[1]),
                ):
                    if field not in frame.columns or pd.isna(row[field]):
                        continue
                    try:
                        numeric_value = float(row[field])
                    except (TypeError, ValueError, OverflowError):
                        failures.append(
                            f"row {position} ({relative}): invalid {field}={row[field]!r}."
                        )
                    else:
                        if (
                            isinstance(row[field], bool)
                            or not math.isfinite(numeric_value)
                            or not numeric_value.is_integer()
                            or numeric_value < 0
                        ):
                            failures.append(
                                f"row {position} ({relative}): {field} must be a "
                                "non-negative integer."
                            )
                        elif int(numeric_value) != current_value:
                            failures.append(
                                f"row {position} ({relative}): {field} mismatch; "
                                f"manifest {int(numeric_value)}, current {current_value}."
                            )

    required_relative = {
        _normalise_required_manifest_path(path, root=manifest_root)
        for path in required_paths
    }
    missing_required = sorted(required_relative - active_paths)
    if missing_required:
        failures.append(
            f"required active output(s) absent from manifest: {missing_required}."
        )

    if failures:
        preview = "\n- ".join(failures[:20])
        remainder = len(failures) - min(len(failures), 20)
        suffix = f"\n- ... and {remainder} more failure(s)." if remainder else ""
        raise ManifestValidationError(
            f"Output manifest validation failed with {len(failures)} issue(s):\n- "
            f"{preview}{suffix}"
        )

    frame.attrs.update(
        {
            "manifest_root": str(manifest_root),
            "validation_status": "valid",
            "active_output_count": int((statuses == "active").sum()),
            "deprecated_output_count": int((statuses == "deprecated").sum()),
            "validated_output_count": int(
                (statuses == "active").sum()
                + (int((statuses == "deprecated").sum()) if include_deprecated else 0)
            ),
        }
    )
    return frame


__all__ = [
    "CSVDelimiterError",
    "CSVEncodingError",
    "CSVSchemaError",
    "CSVTypeError",
    "CSVValidationError",
    "DuplicateKeyError",
    "EmptyCSVFileError",
    "HeaderOnlyCSVError",
    "MANIFEST_COLUMNS",
    "ManifestValidationError",
    "ValidationError",
    "atomic_write_csv",
    "file_sha256",
    "find_repository_root",
    "generate_output_manifest",
    "read_csv_checked",
    "sha256_file",
    "validate_nonempty_when_required",
    "validate_numeric_columns",
    "validate_output_manifest",
    "validate_required_columns",
    "validate_unique_keys",
    "write_csv_atomic",
]
