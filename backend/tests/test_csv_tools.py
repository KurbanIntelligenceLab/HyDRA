"""Tests for CSV descriptor tools using real zr-tio2 data."""

import pytest
from backend.tools.csv_tools import (
    load_descriptor_data,
    get_system_properties,
    get_numeric_columns,
    compute_correlation_matrix,
    compute_descriptor_shifts,
    get_adsorption_energies,
    summarize_data,
)


def test_load_descriptor_data(project_name):
    df = load_descriptor_data(project_name)
    assert len(df) == 6
    assert "system_label" in df.columns


def test_get_system_properties(project_name):
    props = get_system_properties(project_name, "1Zr-TiO2")
    assert props["system_label"] == "1Zr-TiO2"
    assert pytest.approx(props["E_ads_eV"], abs=0.001) == -0.4683


def test_get_system_properties_invalid(project_name):
    with pytest.raises(ValueError, match="not found"):
        get_system_properties(project_name, "nonexistent-system")


def test_get_numeric_columns(project_name):
    cols = get_numeric_columns(project_name)
    assert isinstance(cols, list)
    assert len(cols) > 0
    # Known CDFT descriptors should be present
    for expected in ["E_ads_eV"]:
        assert expected in cols


def test_compute_correlation_matrix(project_name):
    result = compute_correlation_matrix(project_name)
    assert "columns" in result
    assert "matrix" in result
    n = len(result["columns"])
    assert len(result["matrix"]) == n
    assert len(result["matrix"][0]) == n


def test_compute_descriptor_shifts(project_name):
    result = compute_descriptor_shifts(project_name)
    assert result["pairs_found"] == 3
    assert len(result["pairs"]) == 3


def test_get_adsorption_energies(project_name):
    result = get_adsorption_energies(project_name)
    assert result["found"] is True
    assert len(result["data"]) == 3


def test_summarize_data(project_name):
    result = summarize_data(project_name)
    assert result["num_systems"] == 6
    assert len(result["system_labels"]) == 6
    assert result["num_descriptors"] > 0
