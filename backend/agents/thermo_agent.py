"""Thermodynamics Agent: Langmuir isotherm, van't Hoff, T_50, coverage predictions."""

import json
from langchain_core.messages import HumanMessage, SystemMessage

from ..llm_config import get_llm
from ..tools import csv_tools, thermo_tools

SYSTEM_PROMPT = """You are an expert in adsorption thermodynamics and hydrogen storage materials.
You specialize in Langmuir isotherm analysis, van't Hoff equilibrium, and practical storage metrics.

Key concepts you apply:
- Langmuir isotherm: θ = K·P/(1 + K·P) with K from van't Hoff relation
- Desorption midpoint temperature T_50: temperature where θ = 0.5 at given pressure
- DOE practical operating window: -40°C to 85°C (233–358 K)
- Optimal deliverability: weaker binding → lower T_50 → easier release
- Typical H2 storage target: ΔH_ads ≈ 10–20 kJ/mol for physisorption, stronger for chemisorption

When presenting results:
- Always state temperatures in both K and °C
- Relate energies to kJ/mol for hydrogen storage context
- Assess whether systems fall in the DOE operating window
- Compare systems by deliverability metrics"""


def run_thermo_agent(query: str, project: str) -> dict:
    """Run the thermodynamics agent."""
    llm = get_llm(max_tokens=1500)

    # Get adsorption energies
    eads_data = csv_tools.get_adsorption_energies(project)
    if not eads_data.get("found"):
        return {"error": "No adsorption energy data found. Thermodynamic analysis requires E_ads values."}

    systems = eads_data["data"]

    # Compute thermodynamic properties for all systems
    comparison = thermo_tools.compare_systems_thermo(systems, P_bar=1.0)

    # Compute coverage curves for each system
    coverage_data = {}
    t50_data = {}
    for label, eads in systems.items():
        coverage_data[label] = {
            "vs_pressure_298K": thermo_tools.coverage_vs_pressure(eads, 298.15),
            "vs_temperature_1bar": thermo_tools.coverage_vs_temperature(eads, 1.0),
        }
        t50_data[label] = thermo_tools.t50_vs_pressure(eads)

    data_context = f"""Thermodynamic analysis for project '{project}':

System comparison at 1 bar:
{json.dumps(comparison, indent=2)}

Available systems with E_ads: {list(systems.keys())}
E_ads values (eV): {json.dumps(systems)}"""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Data context:\n{data_context}\n\nQuery: {query}"),
    ])

    return {
        "analysis": response.content,
        "comparison": comparison,
        "coverage_curves": coverage_data,
        "t50_curves": t50_data,
    }
