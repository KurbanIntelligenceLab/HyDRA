"""Thermodynamic tools: Langmuir isotherm, van't Hoff, T_50, coverage predictions."""

import numpy as np

# Constants
KB_EV = 8.617333e-5  # Boltzmann constant in eV/K
R_JMK = 8.314  # Gas constant in J/(mol·K)
S0_H2 = 130.68  # Standard molar entropy of H2 in J/(mol·K)
EV_TO_KJMOL = 96.485  # eV to kJ/mol


def langmuir_coverage(E_ads_eV: float, T_K: float, P_bar: float) -> float:
    """Compute equilibrium H2 surface coverage using Langmuir isotherm.

    θ = K·P_red / (1 + K·P_red)
    where K = exp(-E_ads/(kB·T)) * exp(S0_H2/R)  (van't Hoff)
    and P_red = P / P0 with P0 = 1 bar.
    """
    if T_K <= 0:
        raise ValueError("Temperature must be positive")
    if P_bar <= 0:
        raise ValueError("Pressure must be positive")

    # E_ads is negative for exothermic adsorption
    # ΔH_ads ≈ E_ads (in eV), convert to J/mol for van't Hoff
    delta_H = E_ads_eV * EV_TO_KJMOL * 1000  # J/mol
    delta_S = -S0_H2  # Entropy loss upon adsorption (J/(mol·K))

    # Equilibrium constant K = exp(-ΔG/(R·T)) = exp(-(ΔH - T·ΔS)/(R·T))
    K = np.exp(-(delta_H - T_K * delta_S) / (R_JMK * T_K))

    P_red = P_bar  # P/P0 where P0 = 1 bar
    theta = K * P_red / (1 + K * P_red)
    return float(theta)


def desorption_midpoint_T50(E_ads_eV: float, P_bar: float) -> float:
    """Compute desorption midpoint temperature T_50 where θ = 0.5.

    At θ = 0.5: K·P_red = 1, so T_50 = ΔH / (ΔS + R·ln(P_red))
    For P_red = P/P0: T_50 = ΔH / (ΔS + R·ln(P))
    """
    if P_bar <= 0:
        raise ValueError("Pressure must be positive")

    delta_H = E_ads_eV * EV_TO_KJMOL * 1000  # J/mol
    delta_S = -S0_H2  # J/(mol·K)

    # T_50 = ΔH / (ΔS + R·ln(P))
    denominator = delta_S + R_JMK * np.log(P_bar)
    if denominator == 0:
        return float("inf")

    T50 = delta_H / denominator
    return float(T50)


def coverage_vs_pressure(E_ads_eV: float, T_K: float,
                         P_min: float = 0.01, P_max: float = 100.0,
                         n_points: int = 100) -> dict:
    """Compute coverage θ as a function of pressure at fixed T.
    Returns dict with 'pressures' and 'coverages' arrays."""
    pressures = np.logspace(np.log10(P_min), np.log10(P_max), n_points)
    coverages = [langmuir_coverage(E_ads_eV, T_K, p) for p in pressures]
    return {
        "pressures_bar": pressures.tolist(),
        "coverages": coverages,
        "T_K": T_K,
        "E_ads_eV": E_ads_eV,
    }


def coverage_vs_temperature(E_ads_eV: float, P_bar: float,
                            T_min: float = 200.0, T_max: float = 1000.0,
                            n_points: int = 100) -> dict:
    """Compute coverage θ as a function of temperature at fixed P.
    Returns dict with 'temperatures' and 'coverages' arrays."""
    temperatures = np.linspace(T_min, T_max, n_points)
    coverages = [langmuir_coverage(E_ads_eV, t, P_bar) for t in temperatures]
    return {
        "temperatures_K": temperatures.tolist(),
        "coverages": coverages,
        "P_bar": P_bar,
        "E_ads_eV": E_ads_eV,
    }


def t50_vs_pressure(E_ads_eV: float,
                    P_min: float = 0.01, P_max: float = 100.0,
                    n_points: int = 100) -> dict:
    """Compute T_50 as a function of pressure.
    Returns dict with 'pressures' and 't50s' arrays."""
    pressures = np.logspace(np.log10(P_min), np.log10(P_max), n_points)
    t50s = [desorption_midpoint_T50(E_ads_eV, p) for p in pressures]
    return {
        "pressures_bar": pressures.tolist(),
        "t50_K": t50s,
        "E_ads_eV": E_ads_eV,
    }


def doe_window_check(T50_K: float) -> dict:
    """Check if T_50 falls within DOE practical operating window (-40 to 85°C)."""
    doe_min_K = 273.15 - 40  # 233.15 K
    doe_max_K = 273.15 + 85  # 358.15 K
    return {
        "T50_K": T50_K,
        "T50_C": T50_K - 273.15,
        "doe_min_C": -40,
        "doe_max_C": 85,
        "in_doe_window": doe_min_K <= T50_K <= doe_max_K,
        "above_window": T50_K > doe_max_K,
        "below_window": T50_K < doe_min_K,
    }


def compare_systems_thermo(systems: dict[str, float], P_bar: float = 1.0) -> dict:
    """Compare multiple systems thermodynamically.

    Args:
        systems: dict mapping system_label -> E_ads_eV
        P_bar: pressure for T_50 calculation
    """
    results = []
    for label, eads in systems.items():
        t50 = desorption_midpoint_T50(eads, P_bar)
        theta_298 = langmuir_coverage(eads, 298.15, P_bar)
        doe = doe_window_check(t50)
        results.append({
            "system": label,
            "E_ads_eV": eads,
            "E_ads_kJmol": eads * EV_TO_KJMOL,
            "T50_K": t50,
            "T50_C": t50 - 273.15,
            "theta_298K": theta_298,
            "in_doe_window": doe["in_doe_window"],
        })
    # Sort by T50 (lower = better deliverability)
    results.sort(key=lambda x: x["T50_K"])
    return {
        "P_bar": P_bar,
        "systems": results,
        "best_deliverability": results[0]["system"] if results else None,
    }
