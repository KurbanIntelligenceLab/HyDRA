"""Screening Agent: interpretable ML, symbolic regression, GP, active learning."""

import json
import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage

from ..llm_config import get_llm
from ..tools import csv_tools, ml_tools

SYSTEM_PROMPT = """You are an expert in interpretable machine learning for materials science screening.
You specialize in symbolic regression, Gaussian Process modeling, and active learning for small datasets.

Key principles you follow:
- With small datasets (n < 20), interpretable models are preferred over complex ones
- Symbolic regression discovers human-readable formulas (E_ads = f(descriptors))
- Gaussian Processes provide uncertainty quantification — crucial for knowing when predictions are unreliable
- Active learning maximizes information gain by suggesting the most informative next experiment
- Feature importance tells us which descriptors matter most for predicting properties

When presenting ML results:
- Always state the number of training points and emphasize appropriate caveats
- Show discovered equations with their accuracy metrics
- Explain GP predictions in terms of confidence intervals
- Rank candidate dopants by both predicted performance AND uncertainty
- Connect ML insights to physical/chemical understanding"""


def run_screening_agent(query: str, project: str) -> dict:
    """Run the ML screening agent."""
    llm = get_llm(max_tokens=2000)

    # Load data
    eads_data = csv_tools.get_adsorption_energies(project)
    if not eads_data.get("found"):
        return {"error": "No adsorption energy data found. ML screening requires E_ads values."}

    df = csv_tools.load_descriptor_data(project)
    systems_with_eads = eads_data["data"]

    # Get rows with E_ads for training
    eads_col = eads_data["column"]
    train_df = df[df[eads_col].notna()].copy()

    # Select numeric descriptor columns (exclude energy components)
    exclude_cols = {"E_surface_eV", "E_surface+H2_eV", "E_H2_eV", eads_col,
                    "E_surface", "E_surface+H2", "E_H2"}
    feature_cols = [c for c in train_df.select_dtypes(include="number").columns
                    if c not in exclude_cols and train_df[c].notna().all()]

    if len(feature_cols) == 0:
        return {"error": "No suitable descriptor features found for ML analysis"}

    X_train = train_df[feature_cols].values
    y_train = train_df[eads_col].values.astype(float)

    results = {}

    # 1. Feature importance
    try:
        importance = ml_tools.feature_importance_analysis(X_train, y_train, feature_cols)
        results["feature_importance"] = importance
    except Exception as e:
        results["feature_importance"] = {"error": str(e)}

    # 2. Symbolic regression
    try:
        symbolic = ml_tools.symbolic_regression_eads(X_train, y_train, feature_cols)
        results["symbolic_regression"] = symbolic
    except Exception as e:
        results["symbolic_regression"] = {"error": str(e)}

    # 3. GP predictions for candidate dopants
    try:
        # Determine which elements are already tested
        tested_elements = set()
        for label in systems_with_eads:
            label_lower = label.lower()
            if "zr" in label_lower:
                tested_elements.add("Zr")
            if "ti" in label_lower:
                tested_elements.add("Ti")

        candidates = ml_tools.generate_candidate_dopants(exclude=list(tested_elements))

        if candidates["candidates"]:
            # For GP, we use a simplified feature set from dopant properties
            X_cand = np.array([c["features"] for c in candidates["candidates"]])
            cand_labels = [c["element"] for c in candidates["candidates"]]

            # Use dopant properties as training features too (simplified mapping)
            dopant_features = []
            for label in train_df["system_label"]:
                label_lower = label.lower()
                if "2zr" in label_lower:
                    props = ml_tools.CANDIDATE_DOPANTS["Zr"]
                elif "1zr" in label_lower:
                    props = ml_tools.CANDIDATE_DOPANTS["Zr"]
                else:
                    props = ml_tools.CANDIDATE_DOPANTS["Ti"]
                dopant_features.append([props[f] for f in candidates["feature_names"]])

            X_train_dopant = np.array(dopant_features)
            gp_results = ml_tools.gaussian_process_predict(
                X_train_dopant, y_train, X_cand, cand_labels
            )
            results["gp_predictions"] = gp_results

            # 4. Active learning suggestions
            suggestions = ml_tools.suggest_next_experiment(
                X_train_dopant, y_train, candidates
            )
            results["active_learning"] = suggestions
    except Exception as e:
        results["gp_predictions"] = {"error": str(e)}
        results["active_learning"] = {"error": str(e)}

    # LLM interpretation
    data_context = f"""ML Screening results for project '{project}':
Training data: {len(y_train)} systems with E_ads values
Features used: {feature_cols}
E_ads values: {dict(zip(train_df['system_label'].tolist(), y_train.tolist()))}

Results summary:
{json.dumps({k: _summarize(v) for k, v in results.items()}, indent=2, default=str)[:3000]}"""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Data context:\n{data_context}\n\nQuery: {query}"),
    ])

    return {
        "analysis": response.content,
        "ml_results": results,
    }


def _summarize(result: dict) -> dict:
    """Create a compact summary of ML results for the LLM context."""
    if "error" in result:
        return result
    summary = {}
    for key in ["best_equation", "most_important", "most_informative",
                 "method", "ranked_features", "ranked_candidates",
                 "selection_criterion", "n_datapoints"]:
        if key in result:
            val = result[key]
            if isinstance(val, list) and len(val) > 5:
                val = val[:5]
            summary[key] = val
    return summary
