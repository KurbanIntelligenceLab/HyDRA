"""Descriptor Analyst Agent: electronic structure analysis, correlations, trends."""

import json
from langchain_core.messages import HumanMessage, SystemMessage

from ..llm_config import get_llm
from ..tools import csv_tools

SYSTEM_PROMPT = """You are an expert in electronic structure theory and conceptual density functional theory (CDFT).
You specialize in analyzing Koopmans-based descriptors (ionization potential, electron affinity, chemical potential,
electronegativity, chemical hardness, softness, electrophilicity, maximum charge transfer) and frontier orbital
properties (HOMO, LUMO, band gap) for materials.

When given a query, use your tools to analyze the data, then provide a scientifically rigorous interpretation.
Always reference specific numerical values. Explain trends in terms of physical chemistry concepts.

Key CDFT relationships you know:
- Chemical potential μ = -(IP + EA)/2
- Electronegativity χ = -μ = (IP + EA)/2
- Chemical hardness η = (IP - EA)/2
- Softness S = 1/(2η)
- Electrophilicity ω = μ²/(2η)
- Maximum charge transfer ΔNmax = -μ/η"""


def run_descriptor_agent(query: str, project: str) -> dict:
    """Run the descriptor analysis agent."""
    llm = get_llm(max_tokens=1500)

    # Gather all relevant data
    try:
        summary = csv_tools.summarize_data(project)
        correlation = csv_tools.compute_correlation_matrix(project)
        shifts = csv_tools.compute_descriptor_shifts(project)
        eads = csv_tools.get_adsorption_energies(project)
    except Exception as e:
        return {"error": f"Failed to load data: {e}"}

    data_context = f"""Available data for project '{project}':
- Systems: {summary['system_labels']}
- Descriptors: {summary['descriptors']}
- Descriptor statistics: {json.dumps(summary['descriptor_stats'], indent=2)}
- Adsorption energies: {json.dumps(eads, indent=2)}
- Descriptor shifts upon adsorption: {json.dumps(shifts, indent=2)}
- Correlation matrix columns: {correlation['columns']}"""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Data context:\n{data_context}\n\nQuery: {query}"),
    ])

    return {
        "analysis": response.content,
        "data": {
            "summary": summary,
            "adsorption_energies": eads,
            "descriptor_shifts": shifts,
            "correlation": correlation,
        },
    }
