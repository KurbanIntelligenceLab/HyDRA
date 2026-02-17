"""FastAPI server for the zroAgents multi-agent materials science platform."""

import math
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from .tools import project_manager, csv_tools, xyz_tools, thermo_tools, ml_tools
from .agents.orchestrator import process_query


# Startup/shutdown lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload data on startup for faster first requests."""
    print("🚀 HyDRA starting up...")
    print("📦 Preloading zr-tio2 project data...")

    try:
        # Preload built-in project data
        project = "zr-tio2"

        # 1. Load descriptor data (CSV)
        print("  ├─ Loading descriptors...")
        csv_tools.load_descriptor_data(project)

        # 2. Compute correlation matrix
        print("  ├─ Computing correlation matrix...")
        csv_tools.compute_correlation_matrix(project)

        # 3. Compute descriptor shifts
        print("  ├─ Computing descriptor shifts...")
        csv_tools.compute_descriptor_shifts(project)

        # 4. Load structures list
        print("  ├─ Loading structure list...")
        structures = xyz_tools.list_xyz_files(project)

        # 5. Preload first structure as sample
        if structures:
            print(f"  ├─ Preloading sample structure ({structures[0]['system_label']})...")
            xyz_tools.generate_3d_viz_data(project, structures[0]['system_label'])

        print("✅ Data preloaded successfully!")

    except Exception as e:
        print(f"⚠️  Warning: Could not preload data: {e}")
        print("   App will still work, data will load on first request.")

    yield  # App runs here

    # Shutdown
    print("👋 HyDRA shutting down...")


app = FastAPI(
    title="HyDRA",
    description="Hydrogen Discovery via Reactive Agents — multi-agent system for computational materials science",
    version="1.0.0",
    lifespan=lifespan,
)

# Session management
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-secret-key-change-in-production")
SESSION_COOKIE_NAME = "hydra_session_id"
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "7200"))  # 2 hours default

# CORS configuration - environment-based
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware to manage user sessions and track activity."""

    async def dispatch(self, request: Request, call_next):
        # Get or create session ID
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_id:
            session_id = secrets.token_urlsafe(32)

        # Store session ID in request state
        request.state.session_id = session_id

        # Set session ID in context variable for tools to access
        project_manager.set_current_session(session_id)

        # Update last activity timestamp for this session
        project_manager.touch_session_activity(session_id)

        # Process request
        response = await call_next(request)

        # Set session cookie in response
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            max_age=SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
        )

        # Also send in header for easy JS access
        response.headers["X-Session-ID"] = session_id

        return response


app.add_middleware(SessionMiddleware)


# ──────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    project: str = "zr-tio2"


class ThermoRequest(BaseModel):
    E_ads_eV: float | None = None
    T_K: float = 298.15
    P_bar: float = 1.0
    P_min: float = 0.01
    P_max: float = 100.0
    T_min: float = 200.0
    T_max: float = 1000.0


class ProjectCreate(BaseModel):
    name: str


# ──────────────────────────────────────────────────────────────
# Project endpoints
# ──────────────────────────────────────────────────────────────

@app.get("/api/projects")
def get_projects(request: Request):
    session_id = request.state.session_id
    return project_manager.list_projects(session_id)


@app.post("/api/projects")
def create_project(req: ProjectCreate, request: Request):
    try:
        session_id = request.state.session_id
        return project_manager.create_project(req.name, session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/projects/{project_name}/upload-csv")
async def upload_csv(project_name: str, file: UploadFile = File(...), request: Request = None):
    session_id = request.state.session_id
    content = await file.read()
    validation = project_manager.validate_csv(content)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    path = project_manager.save_csv(project_name, file.filename, content, session_id)
    return {"path": path, "validation": validation}


@app.post("/api/projects/{project_name}/upload-xyz")
async def upload_xyz(project_name: str, file: UploadFile = File(...), request: Request = None):
    session_id = request.state.session_id
    content = await file.read()
    validation = project_manager.validate_xyz(content)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    path = project_manager.save_xyz(project_name, file.filename, content, session_id)
    return {"path": path, "validation": validation}


# ──────────────────────────────────────────────────────────────
# Chat endpoint (multi-agent)
# ──────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        result = await process_query(req.query, req.project)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────
# Data endpoints
# ──────────────────────────────────────────────────────────────

def _sanitize_nan(obj):
    """Replace NaN/Inf with None for JSON serialization."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nan(v) for v in obj]
    return obj


@app.get("/api/data/{project}/descriptors")
def get_descriptors(project: str):
    try:
        df = csv_tools.load_descriptor_data(project)
        return _sanitize_nan({
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records"),
            "summary": csv_tools.summarize_data(project),
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/correlation")
def get_correlation(project: str):
    try:
        return _sanitize_nan(csv_tools.compute_correlation_matrix(project))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/shifts")
def get_descriptor_shifts(project: str):
    try:
        return csv_tools.compute_descriptor_shifts(project)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/adsorption-energies")
def get_adsorption_energies(project: str):
    try:
        return _sanitize_nan(csv_tools.get_adsorption_energies(project))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/energy-decomposition")
def get_energy_decomposition(project: str):
    try:
        return _sanitize_nan(csv_tools.get_energy_decomposition(project))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/structures")
def list_structures(project: str):
    try:
        return xyz_tools.list_xyz_files(project)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/structure/{system_label}")
def get_structure(project: str, system_label: str):
    try:
        return xyz_tools.generate_3d_viz_data(project, system_label)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/charges/{system_label}")
def get_charges(project: str, system_label: str):
    try:
        return xyz_tools.compute_charge_distribution(project, system_label)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/{project}/adsorption-site/{system_label}")
def get_adsorption_site(project: str, system_label: str):
    try:
        return xyz_tools.get_adsorption_site_geometry(project, system_label)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ──────────────────────────────────────────────────────────────
# Thermodynamics endpoints
# ──────────────────────────────────────────────────────────────

@app.post("/api/thermo/{project}/coverage-vs-pressure")
def compute_coverage_pressure(project: str, req: ThermoRequest):
    eads = req.E_ads_eV
    if eads is None:
        eads_data = csv_tools.get_adsorption_energies(project)
        if not eads_data.get("found"):
            raise HTTPException(400, "No E_ads data and none provided")
        # Return curves for all systems
        results = {}
        for label, e in eads_data["data"].items():
            results[label] = thermo_tools.coverage_vs_pressure(e, req.T_K, req.P_min, req.P_max)
        return results
    return thermo_tools.coverage_vs_pressure(eads, req.T_K, req.P_min, req.P_max)


@app.post("/api/thermo/{project}/coverage-vs-temperature")
def compute_coverage_temperature(project: str, req: ThermoRequest):
    eads = req.E_ads_eV
    if eads is None:
        eads_data = csv_tools.get_adsorption_energies(project)
        if not eads_data.get("found"):
            raise HTTPException(400, "No E_ads data and none provided")
        results = {}
        for label, e in eads_data["data"].items():
            results[label] = thermo_tools.coverage_vs_temperature(e, req.P_bar, req.T_min, req.T_max)
        return results
    return thermo_tools.coverage_vs_temperature(eads, req.P_bar, req.T_min, req.T_max)


@app.post("/api/thermo/{project}/t50")
def compute_t50(project: str, req: ThermoRequest):
    eads = req.E_ads_eV
    if eads is None:
        eads_data = csv_tools.get_adsorption_energies(project)
        if not eads_data.get("found"):
            raise HTTPException(400, "No E_ads data and none provided")
        results = {}
        for label, e in eads_data["data"].items():
            results[label] = thermo_tools.t50_vs_pressure(e, req.P_min, req.P_max)
        return results
    return thermo_tools.t50_vs_pressure(eads, req.P_min, req.P_max)


@app.post("/api/thermo/{project}/compare")
def compare_thermo(project: str, req: ThermoRequest):
    eads_data = csv_tools.get_adsorption_energies(project)
    if not eads_data.get("found"):
        raise HTTPException(400, "No E_ads data found")
    return thermo_tools.compare_systems_thermo(eads_data["data"], req.P_bar)


# ──────────────────────────────────────────────────────────────
# ML endpoints
# ──────────────────────────────────────────────────────────────

@app.post("/api/ml/{project}/symbolic-regression")
def run_symbolic_regression(project: str):
    try:
        df = csv_tools.load_descriptor_data(project)
        eads_data = csv_tools.get_adsorption_energies(project)
        if not eads_data.get("found"):
            raise HTTPException(400, "No E_ads data found")

        eads_col = eads_data["column"]
        train_df = df[df[eads_col].notna()].copy()
        exclude = {"E_surface_eV", "E_surface+H2_eV", "E_H2_eV", eads_col,
                    "E_surface", "E_surface+H2", "E_H2"}
        feature_cols = [c for c in train_df.select_dtypes(include="number").columns
                        if c not in exclude and train_df[c].notna().all()]

        X = train_df[feature_cols].values
        y = train_df[eads_col].values.astype(float)

        return ml_tools.symbolic_regression_eads(X, y, feature_cols)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/{project}/gp-predict")
def run_gp_prediction(project: str):
    try:
        eads_data = csv_tools.get_adsorption_energies(project)
        if not eads_data.get("found"):
            raise HTTPException(400, "No E_ads data found")

        systems = eads_data["data"]
        tested = set()
        for label in systems:
            if "zr" in label.lower():
                tested.add("Zr")
            if "ti" in label.lower():
                tested.add("Ti")

        candidates = ml_tools.generate_candidate_dopants(exclude=list(tested))
        if not candidates["candidates"]:
            return {"error": "No untested candidates available"}

        import numpy as np
        # Map training systems to dopant features
        dopant_features = []
        y_train = []
        for label, eads in systems.items():
            if "2zr" in label.lower() or "1zr" in label.lower():
                props = ml_tools.CANDIDATE_DOPANTS["Zr"]
            else:
                props = ml_tools.CANDIDATE_DOPANTS["Ti"]
            dopant_features.append([props[f] for f in candidates["feature_names"]])
            y_train.append(eads)

        X_train = np.array(dopant_features)
        y_train = np.array(y_train)
        X_cand = np.array([c["features"] for c in candidates["candidates"]])
        cand_labels = [c["element"] for c in candidates["candidates"]]

        gp_results = ml_tools.gaussian_process_predict(X_train, y_train, X_cand, cand_labels)
        return {**gp_results, "candidates": candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/{project}/suggest-next")
def suggest_next(project: str):
    try:
        eads_data = csv_tools.get_adsorption_energies(project)
        if not eads_data.get("found"):
            raise HTTPException(400, "No E_ads data found")

        systems = eads_data["data"]
        tested = set()
        for label in systems:
            if "zr" in label.lower():
                tested.add("Zr")
            if "ti" in label.lower():
                tested.add("Ti")

        candidates = ml_tools.generate_candidate_dopants(exclude=list(tested))

        import numpy as np
        dopant_features = []
        y_train = []
        for label, eads in systems.items():
            if "2zr" in label.lower() or "1zr" in label.lower():
                props = ml_tools.CANDIDATE_DOPANTS["Zr"]
            else:
                props = ml_tools.CANDIDATE_DOPANTS["Ti"]
            dopant_features.append([props[f] for f in candidates["feature_names"]])
            y_train.append(eads)

        X_train = np.array(dopant_features)
        y_train = np.array(y_train)

        return ml_tools.suggest_next_experiment(X_train, y_train, candidates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/{project}/feature-importance")
def run_feature_importance(project: str):
    try:
        df = csv_tools.load_descriptor_data(project)
        eads_data = csv_tools.get_adsorption_energies(project)
        if not eads_data.get("found"):
            raise HTTPException(400, "No E_ads data found")

        eads_col = eads_data["column"]
        train_df = df[df[eads_col].notna()].copy()
        exclude = {"E_surface_eV", "E_surface+H2_eV", "E_H2_eV", eads_col}
        feature_cols = [c for c in train_df.select_dtypes(include="number").columns
                        if c not in exclude and train_df[c].notna().all()]

        X = train_df[feature_cols].values
        y = train_df[eads_col].values.astype(float)

        return ml_tools.feature_importance_analysis(X, y, feature_cols)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


# ──────────────────────────────────────────────────────────────
# Serve frontend static files (for production deployment)
# ──────────────────────────────────────────────────────────────

# Check if frontend build exists
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Mount static files (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # Serve index.html for all non-API routes (SPA fallback)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # Try to serve the requested file
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Otherwise serve index.html (SPA fallback)
        return FileResponse(frontend_dist / "index.html")
