"""Shared fixtures for backend tests."""

import pytest
from pathlib import Path


PROJECTS_DIR = Path(__file__).parent.parent / "projects"


@pytest.fixture
def project_name():
    return "zr-tio2"


@pytest.fixture
def sample_xyz_path():
    return PROJECTS_DIR / "zr-tio2" / "geo" / "pristine-TiO2.xyz"


@pytest.fixture
def sample_h2_xyz_path():
    return PROJECTS_DIR / "zr-tio2" / "geo" / "pristine-TiO2-H2.xyz"
