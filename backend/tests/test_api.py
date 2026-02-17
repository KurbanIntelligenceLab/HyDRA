"""Tests for FastAPI endpoints using TestClient."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_get_projects(client):
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    names = [p["name"] for p in data]
    assert "zr-tio2" in names


def test_get_descriptors(client):
    resp = client.get("/api/data/zr-tio2/descriptors")
    assert resp.status_code == 200
    data = resp.json()
    assert "columns" in data
    assert "data" in data
    assert len(data["data"]) == 6


def test_get_correlation(client):
    resp = client.get("/api/data/zr-tio2/correlation")
    assert resp.status_code == 200
    data = resp.json()
    assert "columns" in data
    assert "matrix" in data


def test_get_shifts(client):
    resp = client.get("/api/data/zr-tio2/shifts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pairs_found"] == 3


def test_list_structures(client):
    resp = client.get("/api/data/zr-tio2/structures")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6


def test_get_structure(client):
    resp = client.get("/api/data/zr-tio2/structure/pristine-TiO2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["num_atoms"] == 269


def test_get_charges(client):
    resp = client.get("/api/data/zr-tio2/charges/pristine-TiO2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_charges"] is True


def test_thermo_t50(client):
    resp = client.post("/api/thermo/zr-tio2/t50", json={})
    assert resp.status_code == 200


def test_feature_importance(client):
    resp = client.post("/api/ml/zr-tio2/feature-importance")
    assert resp.status_code == 200
    data = resp.json()
    assert "ranked_features" in data
    assert "most_important" in data
