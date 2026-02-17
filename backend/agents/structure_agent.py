"""Structure Agent: XYZ parsing, structural features, coordination analysis, 3D viz."""

import json
from langchain_core.messages import HumanMessage, SystemMessage

from ..llm_config import get_llm
from ..tools import xyz_tools

SYSTEM_PROMPT = """You are an expert in structural analysis of nanoparticles and surface science.
You specialize in interpreting coordination environments, charge distributions, adsorption geometries,
and structural motifs in oxide nanoparticles.

When analyzing structures, consider:
- Coordination numbers and their deviation from bulk values (Ti in anatase: CN=6)
- Under-coordinated surface sites as active adsorption centers
- Charge distribution patterns (Mulliken charges) and how they relate to reactivity
- H-H bond lengths for assessing molecular vs dissociative adsorption (molecular < 0.9 Å)
- Metal–H2 distances and their correlation with binding strength

Provide specific numerical values and physically meaningful interpretations."""


def run_structure_agent(query: str, project: str) -> dict:
    """Run the structural analysis agent."""
    llm = get_llm(max_tokens=1500)

    # Gather structural data
    available_files = xyz_tools.list_xyz_files(project)
    if not available_files:
        return {"error": "No XYZ geometry files found for this project"}

    structural_data = {}
    for f in available_files:
        label = f["system_label"]
        try:
            charges = xyz_tools.compute_charge_distribution(project, label)
            structural_data[label] = {"charges": charges}

            # Check for adsorption geometry
            ads_geom = xyz_tools.get_adsorption_site_geometry(project, label)
            if ads_geom.get("has_adsorbate"):
                structural_data[label]["adsorption_geometry"] = ads_geom
        except Exception as e:
            structural_data[label] = {"error": str(e)}

    # Also prepare 3D viz data for the first system mentioned or all
    viz_data = {}
    for f in available_files[:3]:  # Limit to avoid massive payloads
        try:
            viz_data[f["system_label"]] = xyz_tools.generate_3d_viz_data(project, f["system_label"])
        except Exception:
            pass

    data_context = f"""Available structures for project '{project}':
{json.dumps([f['system_label'] for f in available_files])}

Structural analysis:
{json.dumps(structural_data, indent=2, default=str)[:3000]}"""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Data context:\n{data_context}\n\nQuery: {query}"),
    ])

    return {
        "analysis": response.content,
        "structural_data": structural_data,
        "available_structures": [f["system_label"] for f in available_files],
        "viz_data": viz_data,
    }
