"""Tests for ML tools: GP, active learning, feature importance, symbolic regression."""

import numpy as np
import pytest
from backend.tools.ml_tools import (
    generate_candidate_dopants,
    gaussian_process_predict,
    suggest_next_experiment,
    feature_importance_analysis,
    symbolic_regression_eads,
    _generate_rationale,
)


def test_generate_candidate_dopants():
    result = generate_candidate_dopants()
    assert result["num_candidates"] == 12
    elements = [c["element"] for c in result["candidates"]]
    assert "Ti" in elements
    assert "Zr" in elements


def test_generate_candidate_dopants_exclude():
    result = generate_candidate_dopants(exclude=["Ti", "Zr"])
    assert result["num_candidates"] == 10
    elements = [c["element"] for c in result["candidates"]]
    assert "Ti" not in elements
    assert "Zr" not in elements


def test_gaussian_process_predict():
    X_train = np.array([[1.54, 0.605, 2, 4, 47.87],
                         [1.33, 0.72, 2, 4, 91.22]])
    y_train = np.array([-0.5871, -0.4683])
    X_cand = np.array([[1.63, 0.54, 3, 5, 50.94],
                        [2.36, 0.60, 4, 6, 183.84]])

    result = gaussian_process_predict(X_train, y_train, X_cand)
    assert len(result["predictions"]) == 2
    assert len(result["uncertainties"]) == 2
    assert all(u >= 0 for u in result["uncertainties"])


def test_suggest_next_experiment():
    X_train = np.array([[1.54, 0.605, 2, 4, 47.87],
                         [1.33, 0.72, 2, 4, 91.22]])
    y_train = np.array([-0.5871, -0.4683])
    candidates = generate_candidate_dopants(exclude=["Ti", "Zr"])

    result = suggest_next_experiment(X_train, y_train, candidates)
    assert "ranked_candidates" in result
    assert len(result["ranked_candidates"]) == 10
    assert result["most_informative"] is not None


def test_feature_importance_analysis():
    X = np.array([[1.0, 2.0, 3.0],
                   [2.0, 3.0, 4.0],
                   [3.0, 4.0, 5.0]])
    y = np.array([-0.5, -0.3, -0.1])
    names = ["feat_a", "feat_b", "feat_c"]

    result = feature_importance_analysis(X, y, names)
    assert "ranked_features" in result
    assert result["most_important"] is not None
    assert len(result["ranked_features"]) == 3


def test_symbolic_regression_fallback():
    X = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]])
    y = np.array([-0.5, -0.3, -0.1])
    names = ["omega", "eta"]

    result = symbolic_regression_eads(X, y, names, n_iterations=5)
    assert "equations" in result
    assert isinstance(result["equations"], list)
    assert "best_equation" in result
    assert isinstance(result["best_equation"], str)


def test_generate_rationale_isovalent():
    candidate = {"element": "Hf", "features": [], "properties": {
        "oxidation_state": 4, "ionic_radius_ang": 0.71, "d_electrons": 2,
    }}
    rationale = _generate_rationale(candidate)
    assert "isovalent" in rationale


def test_generate_rationale_aliovalent():
    candidate = {"element": "V", "features": [], "properties": {
        "oxidation_state": 5, "ionic_radius_ang": 0.54, "d_electrons": 3,
    }}
    rationale = _generate_rationale(candidate)
    assert "aliovalent" in rationale


def test_generate_rationale_d_electrons():
    candidate = {"element": "Mo", "features": [], "properties": {
        "oxidation_state": 6, "ionic_radius_ang": 0.65, "d_electrons": 5,
    }}
    rationale = _generate_rationale(candidate)
    assert "Kubas" in rationale
