"""Tools for loading and analyzing electronic descriptor data from CSV."""

import pandas as pd
import numpy as np
from functools import lru_cache
from .project_manager import get_project_csv_path


# Cache for descriptor data to avoid reloading CSV files
_descriptor_cache = {}


def load_descriptor_data(project: str) -> pd.DataFrame:
    """Load the descriptor CSV for a project into a DataFrame with caching."""
    # Check cache first
    if project in _descriptor_cache:
        return _descriptor_cache[project].copy()

    # Load from file
    csv_path = get_project_csv_path(project)
    df = pd.read_csv(csv_path)

    # Strip whitespace from column names and string values
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Cache it
    _descriptor_cache[project] = df

    return df.copy()


def get_system_properties(project: str, system_label: str) -> dict:
    """Get all properties for a specific system as a dict."""
    df = load_descriptor_data(project)
    row = df[df["system_label"] == system_label]
    if row.empty:
        raise ValueError(f"System '{system_label}' not found. Available: {df['system_label'].tolist()}")
    return row.iloc[0].to_dict()


def get_numeric_columns(project: str) -> list[str]:
    """Get list of numeric descriptor column names."""
    df = load_descriptor_data(project)
    return df.select_dtypes(include="number").columns.tolist()


def compute_correlation_matrix(project: str) -> dict:
    """Compute correlation matrix of all numeric descriptors.
    Returns dict with 'columns' and 'matrix' (2D list)."""
    df = load_descriptor_data(project)
    numeric = df.select_dtypes(include="number").dropna(axis=1, how="all")
    corr = numeric.corr()
    return {
        "columns": corr.columns.tolist(),
        "matrix": corr.values.tolist(),
    }


def compute_descriptor_shifts(project: str) -> dict:
    """Compute descriptor shifts upon adsorption.
    Auto-detects paired systems (e.g., 'X' and 'X-H2').
    Returns dict mapping base_system -> {descriptor: shift_value}."""
    df = load_descriptor_data(project)
    labels = df["system_label"].tolist()

    # Find pairs: look for systems where one is a suffix of another
    suffixes = ["-H2", "_H2", "-ads", "_ads", "-adsorbed"]
    pairs = []
    for label in labels:
        for suffix in suffixes:
            if label.endswith(suffix):
                base = label[: -len(suffix)]
                if base in labels:
                    pairs.append((base, label))
                    break

    if not pairs:
        return {"pairs_found": 0, "shifts": {}, "note": "No adsorption pairs detected"}

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    shifts = {}
    for base, adsorbed in pairs:
        base_row = df[df["system_label"] == base].iloc[0]
        ads_row = df[df["system_label"] == adsorbed].iloc[0]
        shift = {}
        for col in numeric_cols:
            bv = base_row[col]
            av = ads_row[col]
            if pd.notna(bv) and pd.notna(av):
                shift[col] = float(av - bv)
        shifts[base] = shift

    return {
        "pairs_found": len(pairs),
        "pairs": [(b, a) for b, a in pairs],
        "shifts": shifts,
        "descriptors": numeric_cols,
    }


def get_adsorption_energies(project: str) -> dict:
    """Extract systems that have adsorption energy data.
    Returns dict mapping system_label -> E_ads value."""
    df = load_descriptor_data(project)
    # Try common column names for adsorption energy
    eads_col = None
    for candidate in ["E_ads_eV", "E_ads", "Eads_eV", "Eads", "adsorption_energy"]:
        if candidate in df.columns:
            eads_col = candidate
            break

    if eads_col is None:
        return {"found": False, "note": "No adsorption energy column detected"}

    subset = df[df[eads_col].notna()][["system_label", eads_col]]
    return {
        "found": True,
        "column": eads_col,
        "data": {row["system_label"]: float(row[eads_col]) for _, row in subset.iterrows()},
    }


def get_energy_decomposition(project: str) -> dict:
    """Load energy decomposition data and compute shifts vs pristine reference.
    Returns dict with raw terms and shifts for each system."""
    from .project_manager import get_project_data_path

    path = get_project_data_path(project) / "energy_decomposition.csv"
    if not path.exists():
        return {"found": False, "note": "No energy_decomposition.csv in project"}

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Find pristine reference row
    ref_row = df[df["system"].str.contains("pristine", case=False)]
    if ref_row.empty:
        return {"found": False, "note": "No pristine reference system found"}

    energy_cols = ["E_elec_eV", "E_rep_eV", "E_disp_eV", "E_total_eV"]
    ref = ref_row.iloc[0]

    systems = []
    for _, row in df.iterrows():
        entry = {"system": row["system"]}
        for col in energy_cols:
            entry[col] = float(row[col])
            entry[f"d{col}"] = float(row[col] - ref[col])
        systems.append(entry)

    return {
        "found": True,
        "reference": ref["system"],
        "energy_columns": energy_cols,
        "systems": systems,
    }


def summarize_data(project: str) -> dict:
    """Generate a summary of the dataset: number of systems, descriptors, ranges."""
    df = load_descriptor_data(project)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    summary = {
        "num_systems": len(df),
        "system_labels": df["system_label"].tolist(),
        "num_descriptors": len(numeric_cols),
        "descriptors": numeric_cols,
        "descriptor_stats": {},
    }
    for col in numeric_cols:
        vals = df[col].dropna()
        if len(vals) > 0:
            summary["descriptor_stats"][col] = {
                "min": float(vals.min()),
                "max": float(vals.max()),
                "mean": float(vals.mean()),
                "range": float(vals.max() - vals.min()),
            }
    return summary
