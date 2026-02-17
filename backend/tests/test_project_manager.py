"""Tests for project manager."""

import pytest
import shutil
from pathlib import Path
from backend.tools.project_manager import (
    list_projects,
    create_project,
    validate_csv,
    validate_xyz,
    get_project_csv_path,
    PROJECTS_DIR,
)


def test_list_projects():
    projects = list_projects()
    names = [p["name"] for p in projects]
    assert "zr-tio2" in names
    zr = next(p for p in projects if p["name"] == "zr-tio2")
    assert zr["builtin"] is True
    assert zr["has_csv"] is True
    assert zr["num_xyz"] == 6


def test_create_project(tmp_path, monkeypatch):
    # Use a temporary projects dir to avoid polluting real data
    monkeypatch.setattr("backend.tools.project_manager.PROJECTS_DIR", tmp_path)
    result = create_project("test-project")
    assert result["name"] == "test-project"
    assert Path(result["path"]).exists()
    assert (Path(result["path"]) / "geo").exists()


def test_create_duplicate_project(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.tools.project_manager.PROJECTS_DIR", tmp_path)
    create_project("dup-project")
    with pytest.raises(ValueError, match="already exists"):
        create_project("dup-project")


def test_validate_csv_valid():
    csv_content = b"system_label,E_ads_eV,omega\nA,-0.5,3.2\nB,-0.3,2.8\n"
    result = validate_csv(csv_content)
    assert result["valid"] is True
    assert result["num_systems"] == 2
    assert result["has_adsorption_energy"] is True


def test_validate_csv_missing_column():
    csv_content = b"name,value\nA,1.0\n"
    result = validate_csv(csv_content)
    assert result["valid"] is False
    assert "system_label" in result["error"]


def test_validate_xyz_valid():
    xyz_content = b"2\ntest comment\nH 0.0 0.0 0.0 0.1\nO 1.0 0.0 0.0 -0.2\n"
    result = validate_xyz(xyz_content)
    assert result["valid"] is True
    assert result["num_atoms"] == 2
    assert result["has_charges"] is True


def test_validate_xyz_invalid():
    xyz_content = b"not a valid xyz file\n"
    result = validate_xyz(xyz_content)
    assert result["valid"] is False


def test_get_project_csv_path():
    path = get_project_csv_path("zr-tio2")
    assert path.exists()
    assert path.suffix == ".csv"
