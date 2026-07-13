"""Build the traceable circuit-width literature-survey artifacts.

The input is the existing local primary-source extraction table.  This module
does not perform a new systematic search and never upgrades the four slide-only
reference values to verified literature evidence.
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import pandas as pd


INCLUDED_STUDIES = {
    "vrptw-2023-leonidas",
    "hvrp-2024-fitzek",
    "cvrp-2025-onah-utility",
    "encoding-2022-glos",
    "vrp-2020-azad",
    "vrp-2025-azfar-arxiv",
    "cvrp-2023-xie",
    "cvrp-2023-palackal",
}

SLIDE_REFERENCES = [
    {
        "evidence_id": "CW-L-MIN-SLIDE",
        "survey_id": "SLIDE-LEONIDAS-MIN",
        "reported_value": 128,
        "value_type": "SLIDE_TRANSCRIBED",
        "unit": "qubits",
        "width_definition": "slide-described minimal formulation width",
        "logical_or_physical": "NOT_VERIFIED",
        "problem_family": "VRP",
        "problem_variant": "VRPTW",
        "formulation": "minimal encoding (slide label)",
        "algorithm": "NOT_VERIFIED",
        "source_title": "Qubit efficient quantum algorithms for the vehicle routing problem on NISQ processors",
        "authors": "Ioannis D. Leonidas; Alexander Dukakis; Benjamin Tan; Dimitris G. Angelakis",
        "year": 2023,
        "doi": "10.48550/arXiv.2306.08507",
        "url": "https://arxiv.org/abs/2306.08507",
        "table_or_figure": "research slide 7",
        "notes": "The paper reports a 128-route instance using 8 qubits; the origin of the slide value 128 as a width was not verified.",
    },
    {
        "evidence_id": "CW-L-FULL-SLIDE",
        "survey_id": "SLIDE-LEONIDAS-FULL",
        "reported_value": 256,
        "value_type": "SLIDE_TRANSCRIBED",
        "unit": "qubits",
        "width_definition": "slide-described full formulation width",
        "logical_or_physical": "NOT_VERIFIED",
        "problem_family": "VRP",
        "problem_variant": "VRPTW",
        "formulation": "full encoding (slide label)",
        "algorithm": "NOT_VERIFIED",
        "source_title": "Qubit efficient quantum algorithms for the vehicle routing problem on NISQ processors",
        "authors": "Ioannis D. Leonidas; Alexander Dukakis; Benjamin Tan; Dimitris G. Angelakis",
        "year": 2023,
        "doi": "10.48550/arXiv.2306.08507",
        "url": "https://arxiv.org/abs/2306.08507",
        "table_or_figure": "research slide 7",
        "notes": "No primary-source page, equation, table, or instance substitution yielding 256 was identified.",
    },
    {
        "evidence_id": "CW-O-HOBO-SLIDE",
        "survey_id": "SLIDE-ONAH-HOBO",
        "reported_value": 6080,
        "value_type": "SLIDE_TRANSCRIBED",
        "unit": "qubits",
        "width_definition": "slide-described higher-order encoding width",
        "logical_or_physical": "NOT_VERIFIED",
        "problem_family": "VRP",
        "problem_variant": "CVRP",
        "formulation": "HOBO/direct encoding (slide label)",
        "algorithm": "resource estimate",
        "source_title": "Requirements for Early Quantum Advantage and Quantum Utility in the Capacitated Vehicle Routing Problem",
        "authors": "Chinonso Onah; Kristel Michielsen",
        "year": 2025,
        "doi": "10.48550/arXiv.2509.11469",
        "url": "https://arxiv.org/abs/2509.11469",
        "table_or_figure": "research slide 7",
        "notes": "The primary paper's Golden_5 row reports 7,685 HOBO qubits; the instance yielding 6,080 was not verified.",
    },
    {
        "evidence_id": "CW-O-QUBO-SLIDE",
        "survey_id": "SLIDE-ONAH-QUBO",
        "reported_value": 14528,
        "value_type": "SLIDE_TRANSCRIBED",
        "unit": "qubits",
        "width_definition": "slide-described quadratic encoding width",
        "logical_or_physical": "NOT_VERIFIED",
        "problem_family": "VRP",
        "problem_variant": "CVRP",
        "formulation": "QUBO (slide label)",
        "algorithm": "resource estimate",
        "source_title": "Requirements for Early Quantum Advantage and Quantum Utility in the Capacitated Vehicle Routing Problem",
        "authors": "Chinonso Onah; Kristel Michielsen",
        "year": 2025,
        "doi": "10.48550/arXiv.2509.11469",
        "url": "https://arxiv.org/abs/2509.11469",
        "table_or_figure": "research slide 7",
        "notes": "The primary paper's Golden_5 row reports 202,505 QUBO qubits; the instance yielding 14,528 was not verified.",
    },
]


CONSTRAINT_STATUS = {
    "vrptw-2023-leonidas": {"time window": "Reported", "multiple vehicles": "Insufficient information"},
    "hvrp-2024-fitzek": {"capacity": "Reported", "multiple vehicles": "Reported", "heterogeneous fleet": "Reported"},
    "cvrp-2025-onah-utility": {"capacity": "Reported"},
    "encoding-2022-glos": {"capacity": "Not applicable", "multiple vehicles": "Not applicable"},
    "vrp-2020-azad": {"multiple vehicles": "Reported", "subtour elimination": "Reported"},
    "vrp-2025-azfar-arxiv": {"multiple vehicles": "Reported", "subtour elimination": "Reported"},
    "cvrp-2023-xie": {"capacity": "Reported", "multiple vehicles": "Reported"},
    "cvrp-2023-palackal": {"capacity": "Reported"},
}

CONSTRAINTS = [
    "capacity",
    "time window",
    "multiple vehicles",
    "multiple depots",
    "range",
    "charging",
    "SOC",
    "heterogeneous fleet",
    "precedence",
    "subtour elimination",
]


def _number(text: object, pattern: str) -> float:
    match = re.search(pattern, str(text), flags=re.I)
    return float(match.group(1)) if match else np.nan


def _reported_width(text: object) -> float:
    match = re.match(r"\s*([0-9][0-9,]*)\s+qubits?\s*$", str(text), flags=re.I)
    return float(match.group(1).replace(",", "")) if match else np.nan


def _instance_fields(paper_id: str, description: str) -> tuple[float, str, float, float, float]:
    text = str(description)
    instance_value = node_count = customer_count = vehicle_count = np.nan
    unit = "NOT_REPORTED"
    if paper_id == "vrptw-2023-leonidas":
        instance_value = _number(text, r"([0-9]+)[- ]route")
        unit = "routes"
    elif paper_id == "hvrp-2024-fitzek":
        customer_count = _number(text, r"([0-9]+) cities")
        vehicle_count = _number(text, r"([0-9]+) trucks?")
        instance_value, unit = customer_count, "customers"
    elif paper_id == "cvrp-2025-onah-utility":
        node_count = _number(text, r"n=([0-9]+)")
        vehicle_count = _number(text, r"vehicles=([0-9]+)")
        instance_value, unit = node_count, "nodes"
    elif paper_id == "vrp-2020-azad":
        node_count = _number(text, r"\(([0-9]+),")
        vehicle_count = _number(text, r",([0-9]+)\)")
        instance_value, unit = node_count, "locations"
    elif paper_id == "vrp-2025-azfar-arxiv":
        node_count = _number(text, r"([0-9]+)-node")
        vehicle_count = _number(text, r"([0-9]+)-vehicle")
        instance_value, unit = node_count, "nodes"
    elif paper_id == "cvrp-2023-palackal":
        node_count = _number(text, r"([0-9]+)-node")
        instance_value, unit = node_count, "nodes"
    return instance_value, unit, customer_count, node_count, vehicle_count


def _problem_variant(paper_id: str, problem: str) -> str:
    if "VRPTW" in problem:
        return "VRPTW"
    if "HVRP" in problem:
        return "HVRP"
    if "CVRP" in problem and "TSP" in problem:
        return "CVRP/TSP decomposition"
    if "CVRP" in problem:
        return "CVRP"
    if "TSP" in problem:
        return "TSP"
    return "VRP"


def _source_parts(location: str) -> tuple[str, str, str]:
    table_or_figure = "; ".join(re.findall(r"(?:Table|Fig\.?|Figs\.?|Eq\.?)\s*[^;,.]*", location, flags=re.I))
    page_or_section = location if location else "MISSING"
    equation = "; ".join(re.findall(r"Eq\.?\s*[^;,.]*", location, flags=re.I))
    return page_or_section, table_or_figure or "NOT_REPORTED", equation or "NOT_REPORTED"


def _derivation_check(
    paper_id: str,
    formulation: str,
    instance_size: float,
    customer_count: float,
    node_count: float,
    decision_variables: object,
    reported_width: float,
) -> tuple[str, str, float, object, str, str]:
    formula = substitution = rounding = "NOT_APPLICABLE"
    recalculated = np.nan
    status = "NOT_RECALCULATED"
    if pd.isna(reported_width):
        return formula, substitution, recalculated, np.nan, rounding, "FORMULA_ONLY_NO_INSTANCE_SUBSTITUTION"
    if paper_id == "vrptw-2023-leonidas" and pd.notna(instance_size):
        if "minimal" in str(formulation).lower():
            formula = "W = 1 + ceil(log2(n_c))"
            recalculated = 1 + np.ceil(np.log2(instance_size))
            substitution = f"1 + ceil(log2({instance_size:g})) = {recalculated:g}"
            rounding = "ceiling to the next integer address width"
        else:
            formula = "W = n_c"
            recalculated = instance_size
            substitution = f"W = {instance_size:g}"
            rounding = "none"
    elif paper_id == "hvrp-2024-fitzek":
        routing = _number(decision_variables, r"routing\s+([0-9]+)")
        capacity = _number(decision_variables, r"capacity\s+([0-9]+)")
        if pd.notna(routing) and pd.notna(capacity):
            formula = "W = W_routing + W_capacity"
            recalculated = routing + capacity
            substitution = f"{routing:g} + {capacity:g} = {recalculated:g}"
            rounding = "none"
    elif paper_id == "vrp-2020-azad" and pd.notna(node_count):
        formula = "W = n(n-1)"
        recalculated = node_count * (node_count - 1)
        substitution = f"{node_count:g} × ({node_count:g}-1) = {recalculated:g}"
        rounding = "none"
    elif paper_id == "cvrp-2023-palackal" and pd.notna(node_count):
        formula = "W = (n-1)^2 for the extracted TSP subproblem encoding"
        recalculated = (node_count - 1) ** 2
        substitution = f"({node_count:g}-1)^2 = {recalculated:g}"
        rounding = "none"
    matched = bool(np.isclose(recalculated, reported_width)) if pd.notna(recalculated) else np.nan
    if pd.notna(recalculated):
        status = "RECALCULATED_MATCH" if matched else "RECALCULATED_MISMATCH"
    return formula, substitution, recalculated, matched, rounding, status


def make_full_survey(resources: pd.DataFrame, papers: pd.DataFrame) -> pd.DataFrame:
    metadata = papers.set_index("id").to_dict(orient="index")
    rows: list[dict] = []
    selected = resources[resources.paper_id.isin(INCLUDED_STUDIES)].copy()
    for ordinal, (_, source) in enumerate(selected.iterrows(), start=1):
        paper = metadata[source.paper_id]
        width = _reported_width(source.circuit_width_qubits)
        value_type = "NUMERIC_VALUE" if pd.notna(width) else "FORMULA_ONLY"
        page, table_figure, equation = _source_parts(str(source.source_location))
        instance_context = f"{source.instance_or_scope}; {source.binary_variables_or_problem_size}"
        size, size_unit, customers, nodes, vehicles = _instance_fields(source.paper_id, instance_context)
        variant = _problem_variant(source.paper_id, source.problem)
        # Explicit study-level coding avoids mistaking "IBM Qiskit simulation"
        # for hardware execution. Palackal reports selected VQE hardware runs;
        # the row notes retain that the width record is a decomposed TSP study.
        is_hardware = source.paper_id in {
            "vrptw-2023-leonidas",
            "vrp-2025-azfar-arxiv",
            "cvrp-2023-palackal",
        }
        definition = "logical qubits or circuit wires used by the reported formulation"
        if source.paper_id == "cvrp-2025-onah-utility":
            definition = "logical/resource-estimate qubit count; not a physical error-corrected qubit estimate"
        formula, substitution, recalculated, formula_match, rounding, derivation_status = _derivation_check(
            source.paper_id,
            source.formulation_or_encoding,
            size,
            customers,
            nodes,
            source.binary_variables_or_problem_size,
            width,
        )
        rows.append(
            {
                "survey_id": f"SURV-{ordinal:03d}",
                "record_scope": "STRUCTURED_SURVEY",
                "paper_id": source.paper_id,
                "authors": paper["authors"],
                "year": int(paper["year"]),
                "title": paper["title"],
                "venue": paper["venue_or_source"],
                "doi": paper["doi"],
                "url": paper["url"].replace("/pdf/", "/abs/") if "arxiv.org/pdf/" in paper["url"] else paper["url"],
                "problem_family": "transportation/routing optimization",
                "problem_variant": variant,
                "application_domain": "transportation and logistics",
                "algorithm": paper["method"],
                "hardware_or_simulator": source.hardware_or_backend,
                "formulation": source.formulation_or_encoding,
                "encoding": paper["encoding_or_formulation"],
                "objective_function": "See primary source; not normalized across studies",
                "constraints_included": "; ".join(k for k, v in CONSTRAINT_STATUS.get(source.paper_id, {}).items() if v == "Reported") or "Not reported",
                "constraints_omitted": "Not inferred from silence; see constraint-coverage table",
                "customer_count": customers,
                "node_count": nodes,
                "vehicle_count": vehicles,
                "depot_count": np.nan,
                "instance_size_value": size,
                "instance_size_unit": size_unit,
                "problem_instance_description": source.instance_or_scope,
                "decision_variable_count": source.binary_variables_or_problem_size,
                "auxiliary_variable_count": "NOT_REPORTED",
                "ancilla_count": "NOT_REPORTED",
                "reported_width": width,
                "width_unit": "qubits" if pd.notna(width) else "formula",
                "width_definition": definition,
                "logical_or_physical": "logical/resource-level; physical mapping not evaluated",
                "width_formula": source.circuit_width_qubits if pd.isna(width) else formula,
                "formula_page": page if pd.isna(width) or formula != "NOT_APPLICABLE" else "NOT_APPLICABLE",
                "formula_substitution": substitution,
                "recalculated_width": recalculated,
                "formula_matches_reported": formula_match,
                "rounding_rule": rounding,
                "derivation_status": derivation_status,
                "reported_value_page": page if pd.notna(width) else "NOT_APPLICABLE",
                "table_or_figure": table_figure,
                "depth_reported": source.circuit_depth if pd.notna(source.circuit_depth) else "Not reported",
                "gate_count_reported": source.gate_or_volume_metric if pd.notna(source.gate_or_volume_metric) else "Not reported",
                "runtime_reported": "Not reported in width extraction table",
                "solution_quality_reported": "Not extracted for this width record",
                "hardware_executed": bool(is_hardware),
                "maximum_executed_width": width if is_hardware and pd.notna(width) else np.nan,
                "maximum_estimated_width": width if source.paper_id == "cvrp-2025-onah-utility" and pd.notna(width) else np.nan,
                "evidence_type": "DIRECTLY_REPORTED_VALUE" if pd.notna(width) else "DIRECTLY_REPORTED_FORMULA",
                "value_type": value_type,
                "extraction_method": "local primary-source PDF/text extraction followed by structured normalization",
                "extractor": "Existing project extraction; normalized with a generative-AI coding assistant",
                "reviewer": "NOT_DOCUMENTED",
                "verification_status": "DIRECTLY_REPORTED",
                "evidence_quality": "A" if pd.notna(width) and table_figure != "NOT_REPORTED" else "B",
                "notes": source.notes,
            }
        )
    return pd.DataFrame(rows)


def make_evidence_registry(full: pd.DataFrame) -> pd.DataFrame:
    numeric = full[full.reported_width.notna()].copy()
    rows = []
    for i, row in numeric.iterrows():
        rows.append(
            {
                "evidence_id": f"CW-VERIFIED-{len(rows)+1:03d}",
                "survey_id": row.survey_id,
                "reported_value": row.reported_width,
                "value_type": row.value_type,
                "unit": row.width_unit,
                "width_definition": row.width_definition,
                "logical_or_physical": row.logical_or_physical,
                "problem_family": row.problem_family,
                "problem_variant": row.problem_variant,
                "instance_size": row.problem_instance_description,
                "customer_count": row.customer_count,
                "vehicle_count": row.vehicle_count,
                "constraints_included": row.constraints_included,
                "formulation": row.formulation,
                "encoding": row.encoding,
                "algorithm": row.algorithm,
                "source_title": row.title,
                "authors": row.authors,
                "year": row.year,
                "doi": row.doi,
                "url": row.url,
                "page": row.reported_value_page,
                "equation": row.width_formula,
                "table_or_figure": row.table_or_figure,
                "extraction_method": row.extraction_method,
                "verification_status": row.verification_status,
                "evidence_quality": row.evidence_quality,
                "notes": row.notes,
            }
        )
    for ref in SLIDE_REFERENCES:
        base = {column: "NOT_VERIFIED" for column in rows[0].keys()}
        base.update(ref)
        base.update(
            {
                "instance_size": "not verified",
                "customer_count": np.nan,
                "vehicle_count": np.nan,
                "constraints_included": "NOT_VERIFIED",
                "encoding": "NOT_VERIFIED",
                "page": "MISSING",
                "equation": "MISSING",
                "extraction_method": "slide transcription plus unsuccessful primary-source value match",
                "verification_status": "SOURCE_NOT_VERIFIED",
                "evidence_quality": "D",
            }
        )
        rows.append(base)
    registry = pd.DataFrame(rows)
    # Compatibility aliases used by earlier notebook code and external readers.
    registry["metric_definition"] = registry["width_definition"]
    registry["problem_type"] = registry["problem_variant"]
    registry["DOI_or_URL"] = registry["doi"].fillna(registry["url"])
    registry["status"] = registry["verification_status"]
    return registry


def make_constraint_coverage(full: pd.DataFrame) -> pd.DataFrame:
    studies = full[["paper_id", "title", "problem_variant"]].drop_duplicates()
    rows = []
    for study in studies.itertuples(index=False):
        configured = CONSTRAINT_STATUS.get(study.paper_id, {})
        for constraint in CONSTRAINTS:
            status = configured.get(constraint, "Not reported")
            rows.append(
                {
                    "paper_id": study.paper_id,
                    "title": study.title,
                    "problem_variant": study.problem_variant,
                    "constraint": constraint,
                    "status": status,
                    "interpretation_rule": "Not reported is not treated as Not implemented",
                }
            )
    return pd.DataFrame(rows)


def make_exclusions(papers: pd.DataFrame) -> pd.DataFrame:
    excluded = papers[~papers.id.isin(INCLUDED_STUDIES)].copy()
    excluded["exclusion_reason"] = np.where(
        excluded.problem.str.contains("benchmark|resource|NISQ|variational|utility", case=False, na=False),
        "Methodological/foundational source without a transport-instance width record",
        "No eligible transport-instance width evidence in the current local extraction",
    )
    excluded["decision_status"] = "EXCLUDED_FROM_WIDTH_VALUE_SYNTHESIS"
    excluded["reviewer"] = "Generative-AI-assisted normalization; human verification NOT_DOCUMENTED"
    return excluded[["id", "title", "year", "problem", "url", "doi", "exclusion_reason", "decision_status", "reviewer"]]


def make_summaries(full: pd.DataFrame, registry: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    numeric = full[full.reported_width.notna()].copy()
    summary_rows = []
    for variant, group in full.groupby("problem_variant", sort=True):
        numbers = numeric[numeric.problem_variant.eq(variant)]
        sizes = group.dropna(subset=["instance_size_value"])
        size_text = "Not consistently reported"
        if len(sizes):
            by_unit = []
            for unit, values in sizes.groupby("instance_size_unit").instance_size_value:
                by_unit.append(f"{values.min():g}-{values.max():g} {unit}")
            size_text = "; ".join(by_unit)
        width_text = "Formula only"
        if len(numbers):
            width_text = f"{numbers.reported_width.min():g}-{numbers.reported_width.max():g} qubits"
        summary_rows.append(
            {
                "problem_variant": variant,
                "studies": group.paper_id.nunique(),
                "instance_size_range": size_text,
                "width_range": width_text,
                "typical_formulation": "; ".join(sorted(group.formulation.dropna().astype(str).unique())[:3]),
                "main_constraints_represented": "; ".join(sorted(set("; ".join(group.constraints_included).split("; ")))),
                "evidence_quality": "; ".join(sorted(group.evidence_quality.unique())),
            }
        )
    verification = (
        registry.groupby("verification_status", dropna=False)
        .size()
        .rename("number_of_values")
        .reset_index()
    )
    meanings = {
        "DIRECTLY_REPORTED": "Primary-source value or formula with a traceable section/table/figure locator",
        "FORMULA_DERIVED": "Recalculated from a source formula and recorded substitutions",
        "SLIDE_TRANSCRIBED": "Transcribed from a research slide only",
        "SOURCE_NOT_VERIFIED": "No matching primary-source value/location verified",
    }
    complete = pd.DataFrame({"verification_status": list(meanings)})
    verification = complete.merge(verification, how="left", on="verification_status").fillna({"number_of_values": 0})
    verification["number_of_values"] = verification.number_of_values.astype(int)
    verification["meaning"] = verification.verification_status.map(meanings)
    return pd.DataFrame(summary_rows), verification


def make_flow(papers: pd.DataFrame, full: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("Local literature records identified", len(papers), "Current local papers.csv; historical search universe NOT_DOCUMENTED"),
            ("Duplicate IDs removed", int(papers.id.duplicated().sum()), "Current registry ID check; not a historical PRISMA count"),
            ("Records screened against scope", len(papers), "Title/problem/method metadata screening"),
            ("Studies containing eligible width evidence", full.paper_id.nunique(), "Transportation/routing primary-source extraction rows"),
            ("Structured width/formula records", len(full), "One row per extracted instance/formula record"),
            ("Numeric values directly traceable", int((registry.verification_status == "DIRECTLY_REPORTED").sum()), "Primary-source locator retained"),
            ("Slide values retained as source-not-verified", int((registry.verification_status == "SOURCE_NOT_VERIFIED").sum()), "Not counted as verified survey results"),
        ],
        columns=["stage", "count", "count_scope_and_caveat"],
    )


def make_search_protocol() -> pd.DataFrame:
    """Record only the search/verification actions that are actually documented."""
    rows = [
        ("survey_type", "exploratory structured literature survey", "DOCUMENTED", "Not a systematic review or exhaustive scoping review"),
        ("search_date", "2026-07-13", "DOCUMENTED", "Date of the targeted primary-source verification for this revision"),
        ("starting_population", "Research slides, local papers.csv, local primary-source PDFs, and circuit_resources.csv", "DOCUMENTED", "Earlier discovery process is NOT_DOCUMENTED"),
        ("search_sources", "Local primary-source PDF corpus; arXiv abstract records; Nature publisher article page", "DOCUMENTED", "No subscription database search was performed in this revision"),
        ("search_terms", "Exact paper titles, author names, arXiv IDs 2306.08507/2308.08785/2509.11469, DOI 10.1038/s41598-024-76967-w, and within-document terms qubit/width/route/Table 3", "DOCUMENTED", "The illustrative Boolean query in the specification was not represented as an executed historic query"),
        ("publication_period", "No ex-ante period restriction documented", "NOT_DOCUMENTED", "Current eligible local records span 2020-2025; this is an observed range, not a planned filter"),
        ("language_restriction", "English-language local primary sources", "DEFINED_DURING_ANALYSIS", "A prior language restriction is NOT_DOCUMENTED"),
        ("document_type", "Primary research articles, conference papers, and arXiv manuscripts containing a width value or formula", "DEFINED_DURING_ANALYSIS", "Reviews are retained as background but excluded from value synthesis"),
        ("backward_citation_search", "Not performed for this revision", "NOT_PERFORMED", "No exhaustive ancestry search claimed"),
        ("forward_citation_search", "Not performed for this revision", "NOT_PERFORMED", "No exhaustive citation-index search claimed"),
        ("duplicate_removal", "Current registry deduplicated by paper ID/DOI", "DOCUMENTED", "Historical duplicate-removal counts are NOT_DOCUMENTED"),
        ("reviewer", "Generative-AI-assisted extraction normalization; independent human literature reviewer NOT_DOCUMENTED", "DOCUMENTED", "Primary-source locators and validation results remain available for human review"),
        ("preregistration", "No preregistered survey protocol identified", "NOT_DOCUMENTED", "Criteria and visualizations added in the current revision are DEFINED_DURING_ANALYSIS"),
        ("missing_information_policy", "Use Not reported, Not implemented, Not applicable, Insufficient information, MISSING, and NOT_DOCUMENTED distinctly", "DOCUMENTED", "Silence in a paper is never coded as Not implemented"),
    ]
    return pd.DataFrame(rows, columns=["field", "current_setting", "status", "interpretation_note"])


def plot_width_vs_size(full: pd.DataFrame, figures: Path) -> bool:
    plot = full.dropna(subset=["reported_width", "instance_size_value"]).copy()
    if plot.empty:
        return False
    units = list(dict.fromkeys(plot.instance_size_unit))
    fig, axes = plt.subplots(1, len(units), figsize=(6 * len(units), 4.8), squeeze=False)
    markers = ["o", "s", "^", "D", "P", "X", "v", "<"]
    variants = sorted(plot.problem_variant.unique())
    marker_map = {variant: markers[i % len(markers)] for i, variant in enumerate(variants)}
    short_labels = {
        "vrptw-2023-leonidas": "Leonidas 2023",
        "hvrp-2024-fitzek": "Fitzek 2024",
        "cvrp-2025-onah-utility": "Onah 2025",
        "vrp-2020-azad": "Azad 2020",
        "vrp-2025-azfar-arxiv": "Azfar 2025",
        "cvrp-2023-palackal": "Palackal 2023",
    }
    offsets = [(4, 4), (4, -11), (4, 12), (-54, 4), (-54, -11), (4, 20)]
    for ax, unit in zip(axes[0], units):
        subset = plot[plot.instance_size_unit.eq(unit)]
        for point_index, row in enumerate(subset.itertuples(index=False)):
            ax.scatter(row.instance_size_value, row.reported_width, marker=marker_map[row.problem_variant], facecolors="white", edgecolors="black", s=65)
            ax.annotate(short_labels.get(row.paper_id, row.paper_id), (row.instance_size_value, row.reported_width), xytext=offsets[point_index % len(offsets)], textcoords="offset points", fontsize=7)
        ax.set_yscale("log")
        if subset.instance_size_value.max() / subset.instance_size_value.min() > 20:
            ax.set_xscale("log")
        ax.set_xlabel(f"Instance size ({unit})")
        ax.set_ylabel("Reported logical/resource-level width (qubits, log scale)")
        ax.set_title(f"Comparable only within size unit: {unit}")
        ax.grid(alpha=0.25)
    fig.suptitle("Circuit width versus reported instance size — no cross-unit regression")
    fig.tight_layout()
    fig.savefig(figures / "circuit_width_vs_instance_size.png", dpi=300, bbox_inches="tight")
    fig.savefig(figures / "circuit_width_vs_instance_size.svg", bbox_inches="tight")
    plt.close(fig)
    return True


def plot_constraint_coverage(coverage: pd.DataFrame, figures: Path) -> bool:
    if coverage.empty:
        return False
    order = ["Insufficient information", "Not applicable", "Not reported", "Reported"]
    code = {value: i for i, value in enumerate(order)}
    matrix = coverage.pivot(index="paper_id", columns="constraint", values="status").reindex(columns=CONSTRAINTS)
    values = matrix.replace(code).astype(float).to_numpy()
    cmap = ListedColormap(["#4d4d4d", "#d9d9d9", "#f7f7f7", "#2166ac"])
    norm = BoundaryNorm(np.arange(-0.5, 4.5, 1), cmap.N)
    fig, ax = plt.subplots(figsize=(12, 5.8))
    image = ax.imshow(values, aspect="auto", cmap=cmap, norm=norm)
    ax.set_xticks(range(len(matrix.columns)), matrix.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_title("Constraint reporting status by study (absence of reporting is not non-implementation)")
    colorbar = fig.colorbar(image, ax=ax, ticks=range(4), fraction=0.03, pad=0.02)
    colorbar.ax.set_yticklabels(order)
    fig.tight_layout()
    fig.savefig(figures / "circuit_width_constraint_coverage.png", dpi=300, bbox_inches="tight")
    fig.savefig(figures / "circuit_width_constraint_coverage.svg", bbox_inches="tight")
    plt.close(fig)
    return True


def plot_components(full: pd.DataFrame, figures: Path) -> bool:
    subset = full[full.paper_id.eq("hvrp-2024-fitzek") & full.reported_width.notna()].copy()
    if subset.empty:
        return False
    subset["routing_qubits"] = subset.decision_variable_count.map(lambda x: _number(x, r"routing\s+([0-9]+)"))
    subset["capacity_qubits"] = subset.decision_variable_count.map(lambda x: _number(x, r"capacity\s+([0-9]+)"))
    subset = subset.dropna(subset=["routing_qubits", "capacity_qubits"])
    if subset.empty:
        return False
    labels = subset.problem_instance_description.astype(str)
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(labels, subset.routing_qubits, label="routing qubits", color="white", edgecolor="black", hatch="//")
    ax.bar(labels, subset.capacity_qubits, bottom=subset.routing_qubits, label="capacity qubits", color="#bdbdbd", edgecolor="black")
    ax.set_ylabel("Reported qubits")
    ax.set_title("Verified width components where the primary extraction reports a decomposition")
    ax.legend()
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(figures / "circuit_width_components.png", dpi=300, bbox_inches="tight")
    fig.savefig(figures / "circuit_width_components.svg", bbox_inches="tight")
    plt.close(fig)
    return True


def validate(full: pd.DataFrame, registry: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    tests = []
    add = lambda test_id, description, passed, observed: tests.append(
        {"test_id": test_id, "description": description, "status": "PASS" if passed else "FAIL", "observed": str(observed)}
    )
    add("CW01", "survey_id is unique", full.survey_id.is_unique, int(full.survey_id.duplicated().sum()))
    add("CW02", "each registry value has survey_id", registry.survey_id.notna().all(), int(registry.survey_id.isna().sum()))
    add("CW03", "each registry value has verification_status", registry.verification_status.notna().all(), int(registry.verification_status.isna().sum()))
    add("CW04", "all numeric reported widths are positive", registry.reported_value.gt(0).all(), registry.reported_value.min())
    add("CW05", "all numeric values have units", registry.unit.notna().all(), int(registry.unit.isna().sum()))
    direct = registry.verification_status.eq("DIRECTLY_REPORTED")
    add("CW06", "direct reports have a page/section/table/figure locator", registry.loc[direct, ["page", "table_or_figure"]].ne("MISSING").any(axis=1).all(), int((~registry.loc[direct, ["page", "table_or_figure"]].ne("MISSING").any(axis=1)).sum()))
    derived = registry.verification_status.eq("FORMULA_DERIVED")
    add("CW07", "formula-derived values have equation records", (~derived | registry.equation.ne("MISSING")).all(), int((derived & registry.equation.eq("MISSING")).sum()))
    add("CW08", "unverified slide values are not counted as directly reported", not ((registry.verification_status.eq("SOURCE_NOT_VERIFIED")) & registry.evidence_id.str.startswith("CW-VERIFIED")).any(), int(registry.verification_status.eq("SOURCE_NOT_VERIFIED").sum()))
    add("CW09", "logical/physical semantics are recorded", registry.logical_or_physical.notna().all(), int(registry.logical_or_physical.isna().sum()))
    add("CW10", "summary is generated from full survey variants", set(summary.problem_variant) == set(full.problem_variant), len(summary))
    checked = full.derivation_status.str.startswith("RECALCULATED", na=False)
    add("CW11", "all performed formula/component recalculations match reported widths", full.loc[checked, "formula_matches_reported"].fillna(False).all(), int((~full.loc[checked, "formula_matches_reported"].fillna(False)).sum()))
    return pd.DataFrame(tests)


def build_survey_outputs(resources_path: Path, papers_path: Path, tables: Path, figures: Path) -> dict[str, object]:
    resources = pd.read_csv(resources_path)
    papers = pd.read_csv(papers_path)
    full = make_full_survey(resources, papers)
    registry = make_evidence_registry(full)
    coverage = make_constraint_coverage(full)
    excluded = make_exclusions(papers)
    summary, verification = make_summaries(full, registry)
    flow = make_flow(papers, full, registry)
    search_protocol = make_search_protocol()
    validation = validate(full, registry, summary)

    full.to_csv(tables / "circuit_width_survey_full.csv", index=False)
    registry.to_csv(tables / "circuit_width_evidence.csv", index=False)
    summary.to_csv(tables / "circuit_width_survey_summary.csv", index=False)
    verification.to_csv(tables / "circuit_width_verification_summary.csv", index=False)
    coverage.to_csv(tables / "circuit_width_constraint_coverage.csv", index=False)
    excluded.to_csv(tables / "circuit_width_excluded_studies.csv", index=False)
    flow.to_csv(tables / "circuit_width_survey_flow.csv", index=False)
    search_protocol.to_csv(tables / "circuit_width_search_protocol.csv", index=False)
    validation.to_csv(tables / "circuit_width_survey_validation.csv", index=False)

    figure_status = {
        "width_vs_instance_size": plot_width_vs_size(full, figures),
        "constraint_coverage": plot_constraint_coverage(coverage, figures),
        "width_components": plot_components(full, figures),
    }
    return {
        "full": full,
        "registry": registry,
        "summary": summary,
        "verification": verification,
        "coverage": coverage,
        "excluded": excluded,
        "flow": flow,
        "search_protocol": search_protocol,
        "validation": validation,
        "figure_status": figure_status,
    }
