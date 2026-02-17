"""ML tools: symbolic regression (PySR), Gaussian Process, active learning, feature importance."""

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.preprocessing import StandardScaler

# Candidate dopant properties for screening
# Format: {element: {property: value}} based on periodic table properties
CANDIDATE_DOPANTS = {
    "Ti": {"atomic_number": 22, "electronegativity": 1.54, "ionic_radius_ang": 0.605,
            "d_electrons": 2, "oxidation_state": 4, "atomic_mass": 47.87},
    "Zr": {"atomic_number": 40, "electronegativity": 1.33, "ionic_radius_ang": 0.72,
            "d_electrons": 2, "oxidation_state": 4, "atomic_mass": 91.22},
    "Hf": {"atomic_number": 72, "electronegativity": 1.30, "ionic_radius_ang": 0.71,
            "d_electrons": 2, "oxidation_state": 4, "atomic_mass": 178.49},
    "V":  {"atomic_number": 23, "electronegativity": 1.63, "ionic_radius_ang": 0.54,
            "d_electrons": 3, "oxidation_state": 5, "atomic_mass": 50.94},
    "Nb": {"atomic_number": 41, "electronegativity": 1.60, "ionic_radius_ang": 0.64,
            "d_electrons": 4, "oxidation_state": 5, "atomic_mass": 92.91},
    "Mo": {"atomic_number": 42, "electronegativity": 2.16, "ionic_radius_ang": 0.65,
            "d_electrons": 5, "oxidation_state": 6, "atomic_mass": 95.95},
    "W":  {"atomic_number": 74, "electronegativity": 2.36, "ionic_radius_ang": 0.60,
            "d_electrons": 4, "oxidation_state": 6, "atomic_mass": 183.84},
    "Ce": {"atomic_number": 58, "electronegativity": 1.12, "ionic_radius_ang": 0.87,
            "d_electrons": 1, "oxidation_state": 4, "atomic_mass": 140.12},
    "La": {"atomic_number": 57, "electronegativity": 1.10, "ionic_radius_ang": 1.032,
            "d_electrons": 1, "oxidation_state": 3, "atomic_mass": 138.91},
    "Sn": {"atomic_number": 50, "electronegativity": 1.96, "ionic_radius_ang": 0.69,
            "d_electrons": 0, "oxidation_state": 4, "atomic_mass": 118.71},
    "Al": {"atomic_number": 13, "electronegativity": 1.61, "ionic_radius_ang": 0.535,
            "d_electrons": 0, "oxidation_state": 3, "atomic_mass": 26.98},
    "Fe": {"atomic_number": 26, "electronegativity": 1.83, "ionic_radius_ang": 0.645,
            "d_electrons": 6, "oxidation_state": 3, "atomic_mass": 55.85},
}


def generate_candidate_dopants(exclude: list[str] | None = None) -> dict:
    """Generate feature vectors for candidate dopants not yet tested.

    Args:
        exclude: list of elements to exclude (already tested)

    Returns dict with 'candidates' list and 'feature_names'.
    """
    exclude = set(exclude or [])
    feature_names = ["electronegativity", "ionic_radius_ang", "d_electrons",
                     "oxidation_state", "atomic_mass"]
    candidates = []
    for el, props in CANDIDATE_DOPANTS.items():
        if el in exclude:
            continue
        features = [props[f] for f in feature_names]
        candidates.append({
            "element": el,
            "features": features,
            "properties": props,
        })
    return {
        "feature_names": feature_names,
        "candidates": candidates,
        "num_candidates": len(candidates),
    }


def gaussian_process_predict(X_train: np.ndarray, y_train: np.ndarray,
                              X_candidates: np.ndarray,
                              candidate_labels: list[str] | None = None) -> dict:
    """Train GP on descriptor → E_ads data, predict for candidate systems.

    Args:
        X_train: (n_train, n_features) training features
        y_train: (n_train,) training targets (E_ads)
        X_candidates: (n_cand, n_features) candidate features
        candidate_labels: optional labels for candidates

    Returns dict with predictions, uncertainties, and model info.
    """
    X_train = np.array(X_train, dtype=float)
    y_train = np.array(y_train, dtype=float)
    X_candidates = np.array(X_candidates, dtype=float)

    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_cand_scaled = scaler.transform(X_candidates)

    # GP with RBF kernel + noise
    kernel = ConstantKernel(1.0) * RBF(length_scale=1.0) + WhiteKernel(noise_level=0.001)
    gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, alpha=1e-6)
    gp.fit(X_train_scaled, y_train)

    # Predict
    y_pred, y_std = gp.predict(X_cand_scaled, return_std=True)

    # Also predict training set for validation
    y_train_pred, y_train_std = gp.predict(X_train_scaled, return_std=True)

    results = {
        "predictions": y_pred.tolist(),
        "uncertainties": y_std.tolist(),
        "train_predictions": y_train_pred.tolist(),
        "train_uncertainties": y_train_std.tolist(),
        "train_targets": y_train.tolist(),
        "kernel_params": str(gp.kernel_),
        "log_marginal_likelihood": float(gp.log_marginal_likelihood_value_),
    }

    if candidate_labels:
        results["candidate_labels"] = candidate_labels

    return results


def suggest_next_experiment(X_train: np.ndarray, y_train: np.ndarray,
                            candidates: dict) -> dict:
    """Use active learning (max uncertainty) to rank candidate dopants.

    Args:
        X_train: training features
        y_train: training targets
        candidates: output from generate_candidate_dopants()

    Returns ranked list of candidates by expected information gain.
    """
    X_cand = np.array([c["features"] for c in candidates["candidates"]])
    labels = [c["element"] for c in candidates["candidates"]]

    gp_results = gaussian_process_predict(X_train, y_train, X_cand, labels)

    # Rank by uncertainty (descending = most informative first)
    rankings = []
    for i, cand in enumerate(candidates["candidates"]):
        rankings.append({
            "element": cand["element"],
            "predicted_E_ads_eV": round(gp_results["predictions"][i], 4),
            "uncertainty_eV": round(gp_results["uncertainties"][i], 4),
            "properties": cand["properties"],
            "rationale": _generate_rationale(cand),
        })

    rankings.sort(key=lambda x: -x["uncertainty_eV"])

    return {
        "ranked_candidates": rankings,
        "most_informative": rankings[0]["element"] if rankings else None,
        "selection_criterion": "Maximum GP uncertainty (most informative for model improvement)",
    }


def _generate_rationale(candidate: dict) -> str:
    """Generate a scientific rationale for why a candidate is interesting."""
    el = candidate["element"]
    props = candidate["properties"]
    notes = []
    if props["oxidation_state"] == 4:
        notes.append("isovalent with Ti(IV), minimal charge compensation needed")
    elif props["oxidation_state"] > 4:
        notes.append(f"aliovalent ({el}({props['oxidation_state']}+)), may create electron-rich sites")
    elif props["oxidation_state"] < 4:
        notes.append(f"aliovalent ({el}({props['oxidation_state']}+)), may create oxygen vacancies")
    if props["ionic_radius_ang"] > 0.7:
        notes.append("larger ionic radius may expand adsorption pocket")
    if props["d_electrons"] > 3:
        notes.append(f"d{props['d_electrons']} configuration may enable Kubas-type binding")
    return "; ".join(notes) if notes else "standard dopant candidate"


def feature_importance_analysis(X: np.ndarray, y: np.ndarray,
                                 feature_names: list[str]) -> dict:
    """Compute feature importance via leave-one-out and perturbation analysis.
    Suitable for very small datasets (n <= 10)."""
    X = np.array(X, dtype=float)
    y = np.array(y, dtype=float)
    n_samples, n_features = X.shape

    # Leave-one-out sensitivity
    loo_errors = []
    for i in range(n_samples):
        X_loo = np.delete(X, i, axis=0)
        y_loo = np.delete(y, i)
        if len(y_loo) < 2:
            continue
        # Simple linear prediction for LOO
        mean_pred = y_loo.mean()
        loo_errors.append({
            "left_out_index": i,
            "actual": float(y[i]),
            "predicted_mean": float(mean_pred),
            "error": float(abs(y[i] - mean_pred)),
        })

    # Feature perturbation sensitivity
    perturbation_sensitivity = {}
    for j, fname in enumerate(feature_names):
        # Compute how much E_ads changes per unit change in this feature
        if n_samples >= 2:
            feat_range = X[:, j].max() - X[:, j].min()
            y_range = y.max() - y.min()
            if feat_range > 0:
                sensitivity = abs(y_range / feat_range)
            else:
                sensitivity = 0.0
            # Correlation
            if np.std(X[:, j]) > 0 and np.std(y) > 0:
                corr = float(np.corrcoef(X[:, j], y)[0, 1])
            else:
                corr = 0.0
        else:
            sensitivity = 0.0
            corr = 0.0

        perturbation_sensitivity[fname] = {
            "sensitivity": round(sensitivity, 6),
            "correlation_with_target": round(corr, 4),
            "feature_range": round(float(X[:, j].max() - X[:, j].min()), 6),
            "feature_mean": round(float(X[:, j].mean()), 6),
        }

    # Rank by absolute correlation
    ranked = sorted(perturbation_sensitivity.items(),
                    key=lambda x: abs(x[1]["correlation_with_target"]), reverse=True)

    return {
        "leave_one_out": loo_errors,
        "feature_sensitivity": perturbation_sensitivity,
        "ranked_features": [{"feature": k, **v} for k, v in ranked],
        "most_important": ranked[0][0] if ranked else None,
    }


def symbolic_regression_eads(X: np.ndarray, y: np.ndarray,
                              feature_names: list[str],
                              max_complexity: int = 10,
                              n_iterations: int = 40) -> dict:
    """Run PySR symbolic regression to discover interpretable formulas.

    Returns discovered equations ranked by Pareto optimality (accuracy vs complexity).
    Falls back to simple analytical fits if PySR is not available.
    """
    X = np.array(X, dtype=float)
    y = np.array(y, dtype=float)

    try:
        from pysr import PySRRegressor

        model = PySRRegressor(
            niterations=n_iterations,
            binary_operators=["+", "-", "*", "/"],
            unary_operators=["square", "neg"],
            maxsize=max_complexity,
            populations=15,
            procs=1,
            multithreading=False,
            temp_equation_file=True,
            progress=False,
        )
        model.fit(X, y, variable_names=feature_names)

        equations = []
        for i in range(len(model.equations_)):
            eq = model.equations_.iloc[i]
            equations.append({
                "equation": str(eq["equation"]),
                "complexity": int(eq["complexity"]),
                "loss": float(eq["loss"]),
                "score": float(eq.get("score", 0)),
            })

        best = model.get_best()
        return {
            "method": "PySR symbolic regression",
            "equations": equations,
            "best_equation": str(best["equation"]) if isinstance(best, dict) else str(best),
            "feature_names": feature_names,
            "n_datapoints": len(y),
        }

    except ImportError:
        # Fallback: simple analytical relationships
        return _analytical_fallback(X, y, feature_names)


def _analytical_fallback(X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> dict:
    """Simple analytical fits when PySR is not available."""
    n_samples, n_features = X.shape
    equations = []

    # Linear fits for each single feature
    for j, fname in enumerate(feature_names):
        if np.std(X[:, j]) > 0:
            # Simple linear regression
            slope = np.cov(X[:, j], y)[0, 1] / np.var(X[:, j])
            intercept = y.mean() - slope * X[:, j].mean()
            y_pred = slope * X[:, j] + intercept
            mse = float(np.mean((y - y_pred) ** 2))
            r2 = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - y.mean()) ** 2) if np.var(y) > 0 else 0

            sign = "+" if intercept >= 0 else "-"
            equations.append({
                "equation": f"E_ads = {slope:.4f} * {fname} {sign} {abs(intercept):.4f}",
                "complexity": 3,
                "loss": mse,
                "r_squared": float(r2),
                "feature": fname,
            })

    # Rank by R² (descending)
    equations.sort(key=lambda x: -x.get("r_squared", 0))

    return {
        "method": "analytical_fallback (PySR not installed)",
        "equations": equations,
        "best_equation": equations[0]["equation"] if equations else "No fit found",
        "feature_names": feature_names,
        "n_datapoints": len(y),
        "note": "Install PySR for more sophisticated symbolic regression: pip install pysr",
    }
