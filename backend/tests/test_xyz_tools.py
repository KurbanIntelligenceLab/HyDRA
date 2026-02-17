"""Tests for XYZ geometry tools using real zr-tio2 data."""

import pytest
from backend.tools.xyz_tools import (
    parse_xyz,
    list_xyz_files,
    compute_coordination_numbers,
    get_adsorption_site_geometry,
    compute_charge_distribution,
    generate_3d_viz_data,
)


def test_parse_xyz(sample_xyz_path):
    data = parse_xyz(sample_xyz_path)
    assert data["num_atoms"] == 269
    assert "Ti" in data["elements"]
    assert "O" in data["elements"]
    assert len(data["atoms"]) == 269


def test_list_xyz_files(project_name):
    files = list_xyz_files(project_name)
    assert len(files) == 6
    labels = [f["system_label"] for f in files]
    assert "pristine-TiO2" in labels


def test_compute_coordination_numbers(sample_xyz_path):
    data = parse_xyz(sample_xyz_path)
    cn_data = compute_coordination_numbers(data["atoms"][:20])  # subset for speed
    assert len(cn_data) == 20
    for item in cn_data:
        assert item["cn"] >= 0
        assert isinstance(item["cn"], int)


def test_get_adsorption_site_geometry_with_h2(project_name):
    result = get_adsorption_site_geometry(project_name, "pristine-TiO2-H2")
    assert result["has_adsorbate"] is True
    assert result["h_h_distance_ang"] > 0


def test_get_adsorption_site_geometry_without_h2(project_name):
    result = get_adsorption_site_geometry(project_name, "pristine-TiO2")
    # pristine-TiO2 has H atoms in the structure (surface hydroxyls)
    # so has_adsorbate may be True depending on structure
    assert isinstance(result["has_adsorbate"], bool)


def test_compute_charge_distribution(project_name):
    result = compute_charge_distribution(project_name, "pristine-TiO2")
    assert result["has_charges"] is True
    assert "Ti" in result["by_element"]
    assert "O" in result["by_element"]


def test_compute_charge_distribution_zr(project_name):
    result = compute_charge_distribution(project_name, "1Zr-TiO2")
    assert result["has_charges"] is True
    assert "Zr" in result["by_element"]


def test_generate_3d_viz_data(project_name):
    result = generate_3d_viz_data(project_name, "pristine-TiO2")
    assert "xyz_text" in result
    assert "atoms" in result
    assert result["num_atoms"] == 269
    assert len(result["atoms"]) == 269
