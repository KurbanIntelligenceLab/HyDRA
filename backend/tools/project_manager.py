"""Project management: create, list, upload, and validate material datasets."""

import os
import shutil
import time
from contextvars import ContextVar
from pathlib import Path

import pandas as pd

# Session-based storage
SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
BUILTIN_PROJECTS_DIR = Path(__file__).parent.parent / "projects"
BUILTIN_PROJECT = "zr-tio2"

# Context variable to store current session ID
_current_session: ContextVar[str] = ContextVar("current_session", default=None)


def _session_path(session_id: str) -> Path:
    """Get the base path for a session."""
    return SESSIONS_DIR / session_id


def set_current_session(session_id: str) -> None:
    """Set the current session ID in the context."""
    _current_session.set(session_id)


def get_current_session() -> str:
    """Get the current session ID from the context."""
    return _current_session.get()


def _project_path(name: str, session_id: str = None) -> Path:
    """Get project path - session-scoped for user projects, built-in for built-in projects."""
    # Use explicitly passed session_id, or fall back to context session_id
    if session_id is None:
        session_id = get_current_session()

    print(f"[Project] _project_path(name={name}, session_id={session_id})")
    print(f"[Project] BUILTIN_PROJECT={BUILTIN_PROJECT}, BUILTIN_PROJECTS_DIR={BUILTIN_PROJECTS_DIR}")

    if name == BUILTIN_PROJECT:
        # Built-in project is shared (read-only)
        path = BUILTIN_PROJECTS_DIR / name
        print(f"[Project] Using built-in project path: {path}")
        print(f"[Project] Path exists: {path.exists()}")
        if path.exists():
            print(f"[Project] Contents: {list(path.iterdir())}")
        return path
    elif session_id:
        # User projects are session-scoped
        path = _session_path(session_id) / "projects" / name
        print(f"[Project] Using session project path: {path}")
        return path
    else:
        # Fallback to built-in projects dir (for backwards compatibility)
        path = BUILTIN_PROJECTS_DIR / name
        print(f"[Project] Using fallback project path: {path}")
        return path


def list_projects(session_id: str = None) -> list[dict]:
    """Return list of available projects with metadata (session-scoped + built-in)."""
    projects = []

    # Add built-in project (always available)
    if BUILTIN_PROJECTS_DIR.exists():
        for entry in sorted(BUILTIN_PROJECTS_DIR.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                csv_files = list(entry.glob("*.csv"))
                xyz_dir = entry / "geo"
                xyz_files = list(xyz_dir.glob("*.xyz")) if xyz_dir.exists() else []
                projects.append({
                    "name": entry.name,
                    "builtin": True,
                    "has_csv": len(csv_files) > 0,
                    "csv_file": csv_files[0].name if csv_files else None,
                    "num_xyz": len(xyz_files),
                    "systems": _get_system_labels(csv_files[0]) if csv_files else [],
                })

    # Add session-specific projects
    if session_id:
        session_projects_dir = _session_path(session_id) / "projects"
        if session_projects_dir.exists():
            for entry in sorted(session_projects_dir.iterdir()):
                if entry.is_dir() and not entry.name.startswith("."):
                    csv_files = list(entry.glob("*.csv"))
                    xyz_dir = entry / "geo"
                    xyz_files = list(xyz_dir.glob("*.xyz")) if xyz_dir.exists() else []
                    projects.append({
                        "name": entry.name,
                        "builtin": False,
                        "has_csv": len(csv_files) > 0,
                        "csv_file": csv_files[0].name if csv_files else None,
                        "num_xyz": len(xyz_files),
                        "systems": _get_system_labels(csv_files[0]) if csv_files else [],
                    })

    return projects


def _get_system_labels(csv_path: Path) -> list[str]:
    try:
        df = pd.read_csv(csv_path)
        if "system_label" in df.columns:
            return df["system_label"].tolist()
    except Exception:
        pass
    return []


def create_project(name: str, session_id: str = None) -> dict:
    """Create a new empty project workspace (session-scoped)."""
    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name.lower())
    path = _project_path(safe_name, session_id)
    if path.exists():
        raise ValueError(f"Project '{safe_name}' already exists")
    path.mkdir(parents=True)
    (path / "geo").mkdir()
    return {"name": safe_name, "path": str(path)}


def validate_csv(content: bytes) -> dict:
    """Validate an uploaded CSV file. Returns validation result."""
    import io
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        return {"valid": False, "error": f"Cannot parse CSV: {e}"}

    if "system_label" not in df.columns:
        return {"valid": False, "error": "Missing required column: 'system_label'"}

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    has_eads = "E_ads_eV" in df.columns or "E_ads" in df.columns

    return {
        "valid": True,
        "num_systems": len(df),
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "has_adsorption_energy": has_eads,
        "system_labels": df["system_label"].tolist(),
    }


def validate_xyz(content: bytes) -> dict:
    """Validate an uploaded XYZ file."""
    try:
        text = content.decode("utf-8")
        lines = text.strip().split("\n")
        num_atoms = int(lines[0].strip())
        # Check that we have enough lines
        if len(lines) < num_atoms + 2:
            return {"valid": False, "error": f"Expected {num_atoms + 2} lines, got {len(lines)}"}
        # Check first atom line parses
        parts = lines[2].split()
        if len(parts) < 4:
            return {"valid": False, "error": "Atom lines must have at least 4 columns (element x y z)"}
        element = parts[0]
        float(parts[1])
        float(parts[2])
        float(parts[3])
        has_charges = len(parts) >= 5
        return {
            "valid": True,
            "num_atoms": num_atoms,
            "comment": lines[1].strip(),
            "has_charges": has_charges,
            "sample_element": element,
        }
    except Exception as e:
        return {"valid": False, "error": f"Cannot parse XYZ: {e}"}


def save_csv(project_name: str, filename: str, content: bytes, session_id: str = None) -> str:
    """Save a validated CSV to a project (session-scoped)."""
    path = _project_path(project_name, session_id)
    if not path.exists():
        raise ValueError(f"Project '{project_name}' not found")
    dest = path / filename
    dest.write_bytes(content)
    return str(dest)


def save_xyz(project_name: str, filename: str, content: bytes, session_id: str = None) -> str:
    """Save a validated XYZ file to a project (session-scoped)."""
    path = _project_path(project_name, session_id) / "geo"
    path.mkdir(exist_ok=True)
    dest = path / filename
    dest.write_bytes(content)
    return str(dest)


def get_project_data_path(project_name: str, session_id: str = None) -> Path:
    """Get the path to a project's data directory."""
    path = _project_path(project_name, session_id)
    if not path.exists():
        raise ValueError(f"Project '{project_name}' not found")
    return path


def get_project_csv_path(project_name: str, session_id: str = None) -> Path:
    """Get the CSV file path for a project."""
    path = _project_path(project_name, session_id)

    # Prefer labels.csv if it exists (main descriptor file)
    labels_path = path / "labels.csv"
    if labels_path.exists():
        return labels_path

    # Otherwise, look for any CSV with system_label column
    csv_files = sorted(path.glob("*.csv"))  # Sort for consistency
    if not csv_files:
        raise ValueError(f"No CSV file in project '{project_name}'")

    # Try to find a CSV with system_label column
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, nrows=1)
            if "system_label" in df.columns:
                return csv_file
        except Exception:
            continue

    # Fallback to first CSV
    return csv_files[0]


def get_project_xyz_dir(project_name: str, session_id: str = None) -> Path:
    """Get the geo directory for a project."""
    return _project_path(project_name, session_id) / "geo"


# ──────────────────────────────────────────────────────────────
# Session management functions
# ──────────────────────────────────────────────────────────────

def touch_session_activity(session_id: str) -> None:
    """Update the last activity timestamp for a session."""
    session_dir = _session_path(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    activity_file = session_dir / "last_activity.txt"
    activity_file.write_text(str(time.time()))


def get_session_last_activity(session_id: str) -> float:
    """Get the last activity timestamp for a session."""
    activity_file = _session_path(session_id) / "last_activity.txt"
    if not activity_file.exists():
        return 0.0
    try:
        return float(activity_file.read_text().strip())
    except (ValueError, OSError):
        return 0.0


def list_sessions() -> list[dict]:
    """List all sessions with their metadata."""
    sessions = []
    if not SESSIONS_DIR.exists():
        return sessions

    for session_dir in SESSIONS_DIR.iterdir():
        if session_dir.is_dir() and not session_dir.name.startswith("."):
            last_activity = get_session_last_activity(session_dir.name)
            projects_dir = session_dir / "projects"
            num_projects = len(list(projects_dir.iterdir())) if projects_dir.exists() else 0

            sessions.append({
                "session_id": session_dir.name,
                "last_activity": last_activity,
                "num_projects": num_projects,
                "path": str(session_dir),
            })

    return sessions


def cleanup_session(session_id: str) -> bool:
    """Delete all data for a session. Returns True if deleted."""
    session_dir = _session_path(session_id)
    if session_dir.exists():
        shutil.rmtree(session_dir)
        return True
    return False
