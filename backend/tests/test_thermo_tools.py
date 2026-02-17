"""Tests for thermodynamic tools."""

import pytest
from backend.tools.thermo_tools import (
    langmuir_coverage,
    desorption_midpoint_T50,
    coverage_vs_pressure,
    coverage_vs_temperature,
    doe_window_check,
    compare_systems_thermo,
)


def test_langmuir_coverage_bounds():
    theta = langmuir_coverage(-0.5, 300, 1.0)
    assert 0 <= theta <= 1


def test_langmuir_coverage_temperature_dependence():
    # Higher T -> lower coverage for exothermic adsorption (negative E_ads)
    theta_low_T = langmuir_coverage(-0.5, 250, 1.0)
    theta_high_T = langmuir_coverage(-0.5, 500, 1.0)
    assert theta_low_T > theta_high_T


def test_langmuir_invalid_temperature():
    with pytest.raises(ValueError, match="Temperature"):
        langmuir_coverage(-0.5, 0, 1.0)


def test_langmuir_invalid_pressure():
    with pytest.raises(ValueError, match="Pressure"):
        langmuir_coverage(-0.5, 300, 0)


def test_desorption_midpoint_t50():
    t50 = desorption_midpoint_T50(-0.5, 1.0)
    assert t50 > 0


def test_t50_pressure_dependence():
    t50_low_p = desorption_midpoint_T50(-0.5, 0.1)
    t50_high_p = desorption_midpoint_T50(-0.5, 10.0)
    assert t50_high_p > t50_low_p


def test_coverage_vs_pressure():
    result = coverage_vs_pressure(-0.5, 300)
    assert "pressures_bar" in result
    assert "coverages" in result
    assert len(result["pressures_bar"]) == 100
    assert len(result["coverages"]) == 100


def test_coverage_vs_temperature():
    result = coverage_vs_temperature(-0.5, 1.0)
    assert "temperatures_K" in result
    assert "coverages" in result
    assert len(result["temperatures_K"]) == 100
    assert len(result["coverages"]) == 100


def test_doe_window_check_in_window():
    result = doe_window_check(300)  # ~27 C, within -40 to 85 C
    assert result["in_doe_window"] is True
    assert result["above_window"] is False
    assert result["below_window"] is False


def test_doe_window_check_above():
    result = doe_window_check(500)  # ~227 C, above 85 C
    assert result["in_doe_window"] is False
    assert result["above_window"] is True


def test_doe_window_check_below():
    result = doe_window_check(200)  # ~-73 C, below -40 C
    assert result["in_doe_window"] is False
    assert result["below_window"] is True


def test_compare_systems_thermo():
    systems = {
        "1Zr-TiO2-H2": -0.4683,
        "2Zr-TiO2-H2": -0.3412,
        "pristine-TiO2-H2": -0.5871,
    }
    result = compare_systems_thermo(systems, P_bar=1.0)
    assert len(result["systems"]) == 3
    assert result["best_deliverability"] is not None
    # Should be sorted by T50 ascending
    t50s = [s["T50_K"] for s in result["systems"]]
    assert t50s == sorted(t50s)
