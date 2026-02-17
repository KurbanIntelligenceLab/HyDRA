"""Tools for parsing XYZ geometry files and computing structural features."""

import numpy as np
from pathlib import Path
from .project_manager import get_project_xyz_dir


# Cache for parsed structures
_structure_cache = {}
_structure_list_cache = {}


# Covalent radii (Å) for common elements in oxide nanoparticles
COVALENT_RADII = {
    "H": 0.31, "O": 0.66, "Ti": 1.60, "Zr": 1.75, "N": 0.71,
    "C": 0.76, "S": 1.05, "V": 1.53, "Nb": 1.64, "Mo": 1.54,
    "W": 1.62, "Hf": 1.75, "Ce": 2.04, "La": 2.07, "Fe": 1.32,
    "Co": 1.26, "Ni": 1.24, "Cu": 1.32, "Zn": 1.22, "Al": 1.21,
    "Si": 1.11, "P": 1.07, "Mn": 1.39, "Cr": 1.39,
}

# CPK-like colors for 3Dmol.js
ELEMENT_COLORS = {
    "H": "#FFFFFF", "O": "#FF0D0D", "Ti": "#73C2FB", "Zr": "#00CC00",
    "N": "#3050F8", "C": "#909090", "S": "#FFFF30", "V": "#A6A6AB",
    "Nb": "#73C2C9", "Mo": "#54B5B5", "W": "#2194D6", "Hf": "#4DC2FF",
    "Ce": "#FFFFC7", "La": "#70D4FF", "Fe": "#E06633", "Cu": "#C88033",
}

# Atomic radii for visualization
VIZ_RADII = {
    "H": 0.3, "O": 0.6, "Ti": 1.2, "Zr": 1.4, "N": 0.6,
    "C": 0.7, "S": 1.0, "V": 1.2, "Nb": 1.3, "Mo": 1.3,
    "W": 1.3, "Hf": 1.4, "Ce": 1.5, "La": 1.5,
}


def parse_xyz(filepath: str | Path) -> dict:
    """Parse an XYZ file into structured data.
    Returns dict with atoms list (element, x, y, z, charge), metadata."""
    filepath = Path(filepath)
    with open(filepath) as f:
        lines = f.readlines()

    num_atoms = int(lines[0].strip())
    comment = lines[1].strip()

    atoms = []
    for i in range(2, 2 + num_atoms):
        parts = lines[i].split()
        element = parts[0]
        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
        charge = float(parts[4]) if len(parts) >= 5 else None
        atoms.append({
            "element": element,
            "x": x, "y": y, "z": z,
            "charge": charge,
            "index": i - 2,
        })

    elements = set(a["element"] for a in atoms)
    return {
        "num_atoms": num_atoms,
        "comment": comment,
        "atoms": atoms,
        "elements": sorted(elements),
        "filepath": str(filepath),
    }


def list_xyz_files(project: str) -> list[dict]:
    """List available XYZ files for a project with caching."""
    cache_key = f"{project}_list"
    if cache_key in _structure_list_cache:
        return _structure_list_cache[cache_key]

    xyz_dir = get_project_xyz_dir(project)
    if not xyz_dir.exists():
        return []
    files = []
    for f in sorted(xyz_dir.glob("*.xyz")):
        files.append({
            "filename": f.name,
            "system_label": f.stem,
            "path": str(f),
        })

    _structure_list_cache[cache_key] = files
    return files


def compute_coordination_numbers(atoms: list[dict], cutoff: float = 2.8) -> list[dict]:
    """Compute coordination number for each atom using distance cutoff.
    Returns list of {index, element, cn, neighbors}."""
    positions = np.array([[a["x"], a["y"], a["z"]] for a in atoms])
    n = len(atoms)
    results = []

    for i in range(n):
        neighbors = []
        for j in range(n):
            if i == j:
                continue
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < cutoff:
                neighbors.append({"index": j, "element": atoms[j]["element"], "distance": round(dist, 4)})
        results.append({
            "index": i,
            "element": atoms[i]["element"],
            "cn": len(neighbors),
            "neighbors": neighbors,
        })

    return results


def get_adsorption_site_geometry(project: str, system_label: str) -> dict:
    """Analyze the adsorption site geometry for a system with adsorbed species.
    Looks for H atoms and finds the nearest metal site."""
    xyz_dir = get_project_xyz_dir(project)
    filepath = xyz_dir / f"{system_label}.xyz"
    if not filepath.exists():
        raise ValueError(f"XYZ file not found: {filepath}")

    data = parse_xyz(filepath)
    atoms = data["atoms"]

    # Find H atoms (adsorbate)
    h_atoms = [a for a in atoms if a["element"] == "H"]
    if not h_atoms:
        return {"has_adsorbate": False, "note": "No H atoms found"}

    # Find metal atoms (non-O, non-H)
    metals = [a for a in atoms if a["element"] not in ("H", "O", "N", "C", "S")]

    # Compute H-H distance if there are 2 H atoms
    h_h_distance = None
    if len(h_atoms) >= 2:
        pos1 = np.array([h_atoms[0]["x"], h_atoms[0]["y"], h_atoms[0]["z"]])
        pos2 = np.array([h_atoms[1]["x"], h_atoms[1]["y"], h_atoms[1]["z"]])
        h_h_distance = float(np.linalg.norm(pos1 - pos2))

    # Find nearest metal to centroid of H atoms
    h_centroid = np.mean([[a["x"], a["y"], a["z"]] for a in h_atoms], axis=0)
    nearest_metal = None
    min_dist = float("inf")
    for m in metals:
        pos = np.array([m["x"], m["y"], m["z"]])
        dist = float(np.linalg.norm(pos - h_centroid))
        if dist < min_dist:
            min_dist = dist
            nearest_metal = m

    return {
        "has_adsorbate": True,
        "num_h_atoms": len(h_atoms),
        "h_h_distance_ang": round(h_h_distance, 4) if h_h_distance else None,
        "nearest_metal_element": nearest_metal["element"] if nearest_metal else None,
        "metal_h2_distance_ang": round(min_dist, 4) if nearest_metal else None,
        "h_positions": [{"x": a["x"], "y": a["y"], "z": a["z"]} for a in h_atoms],
        "metal_position": {"x": nearest_metal["x"], "y": nearest_metal["y"], "z": nearest_metal["z"]} if nearest_metal else None,
        "is_molecular": h_h_distance is not None and h_h_distance < 1.0,
    }


def compute_charge_distribution(project: str, system_label: str) -> dict:
    """Compute Mulliken charge statistics by element type."""
    xyz_dir = get_project_xyz_dir(project)
    filepath = xyz_dir / f"{system_label}.xyz"
    if not filepath.exists():
        raise ValueError(f"XYZ file not found: {filepath}")

    data = parse_xyz(filepath)
    atoms = data["atoms"]

    if atoms[0]["charge"] is None:
        return {"has_charges": False, "note": "No charge data in XYZ file"}

    by_element = {}
    for a in atoms:
        el = a["element"]
        if el not in by_element:
            by_element[el] = []
        by_element[el].append(a["charge"])

    stats = {}
    for el, charges in by_element.items():
        arr = np.array(charges)
        stats[el] = {
            "count": len(charges),
            "mean": round(float(arr.mean()), 6),
            "std": round(float(arr.std()), 6),
            "min": round(float(arr.min()), 6),
            "max": round(float(arr.max()), 6),
        }

    total_charge = sum(a["charge"] for a in atoms)
    return {
        "has_charges": True,
        "total_charge": round(total_charge, 6),
        "by_element": stats,
        "num_atoms": len(atoms),
    }


def generate_3d_viz_data(project: str, system_label: str) -> dict:
    """Generate JSON data for 3Dmol.js visualization with caching."""
    cache_key = f"{project}_{system_label}"
    if cache_key in _structure_cache:
        return _structure_cache[cache_key]

    xyz_dir = get_project_xyz_dir(project)
    filepath = xyz_dir / f"{system_label}.xyz"
    if not filepath.exists():
        raise ValueError(f"XYZ file not found: {filepath}")

    data = parse_xyz(filepath)
    atoms = data["atoms"]

    # Build atom data for 3Dmol.js
    viz_atoms = []
    has_charges = atoms[0]["charge"] is not None
    charges = [a["charge"] for a in atoms if a["charge"] is not None] if has_charges else []
    charge_min = min(charges) if charges else 0
    charge_max = max(charges) if charges else 1
    charge_range = charge_max - charge_min if charge_max != charge_min else 1

    for a in atoms:
        el = a["element"]
        atom_data = {
            "elem": el,
            "x": a["x"],
            "y": a["y"],
            "z": a["z"],
            "color": ELEMENT_COLORS.get(el, "#808080"),
            "radius": VIZ_RADII.get(el, 0.8),
        }
        if a["charge"] is not None:
            # Normalize charge to 0-1 for colormap
            atom_data["charge"] = a["charge"]
            atom_data["charge_normalized"] = (a["charge"] - charge_min) / charge_range
        viz_atoms.append(atom_data)

    # Generate XYZ text for 3Dmol.js (it can parse XYZ directly)
    xyz_lines = [str(data["num_atoms"]), data["comment"]]
    for a in atoms:
        line = f"{a['element']}  {a['x']:.8f}  {a['y']:.8f}  {a['z']:.8f}"
        xyz_lines.append(line)
    xyz_text = "\n".join(xyz_lines)

    result = {
        "system_label": system_label,
        "num_atoms": data["num_atoms"],
        "elements": data["elements"],
        "atoms": viz_atoms,
        "xyz_text": xyz_text,
        "has_charges": has_charges,
        "charge_range": {"min": charge_min, "max": charge_max} if has_charges else None,
    }

    # Cache the result
    _structure_cache[cache_key] = result
    return result
