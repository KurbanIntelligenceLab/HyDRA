# HyDRA — Hydrogen Discovery via Reactive Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

Multi-agent materials science platform for computational screening of doped metal-oxide nanoparticles for H₂ storage. Built with LangGraph orchestration, interpretable ML, and interactive visualization.

**🎯 Features:**
- Multi-agent system with 5 specialist agents + orchestrator
- Session-based file management (automatic cleanup)
- Production-ready deployment configs (free-tier optimized)
- Active learning for experiment planning
- 3D molecular visualization with charge coloring

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│  (3Dmol.js · Recharts · Tailwind CSS)                       │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend                             │
├──────────────────────┬───────────────────────────────────────┤
│              LangGraph Orchestrator                           │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐   │
│  │  Data    │Structure │  Thermo  │    ML    │  Viz     │   │
│  │ Analyst  │ Analyst  │ Analyst  │ Analyst  │ Agent    │   │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘   │
│       │          │          │          │          │           │
│  csv_tools  xyz_tools  thermo_tools ml_tools  viz_tools     │
└──────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-agent orchestration** — 5 specialist agents coordinated by a LangGraph orchestrator, each with domain-specific tools
- **Session-based file management** — Automatic cleanup after 2 hours of inactivity, multi-user support with session isolation
- **Interpretable ML** — Symbolic regression (PySR) discovers human-readable formulas; Gaussian Process provides uncertainty-quantified predictions
- **Active learning** — Suggests most informative next experiment via maximum GP uncertainty
- **Thermodynamic screening** — Langmuir isotherm, van't Hoff analysis, T50 desorption midpoint, DOE window compliance
- **3D visualization** — Interactive molecular viewer (3Dmol.js) with Mulliken charge coloring
- **Project system** — Upload any CSV + XYZ dataset to analyze new material systems
- **Production-ready** — Deploy to Vercel + Railway for $0-5/month (free-tier optimized)
- **CDFT descriptors** — Works with conceptual DFT descriptors (electronegativity, hardness, electrophilicity, etc.)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenRouter](https://openrouter.ai) API key (for LLM-powered agents)

### Backend

```bash
# Install Python dependencies
pip install fastapi uvicorn langchain-openai langgraph pandas numpy scikit-learn

# Set your API key
cp .env.example .env  # or create .env with OPENROUTER_API_KEY=your-key-here

# Start the server
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## API Reference

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create new project |
| POST | `/api/projects/{name}/upload-csv` | Upload CSV descriptors |
| POST | `/api/projects/{name}/upload-xyz` | Upload XYZ geometry |

### Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/data/{project}/descriptors` | Get descriptor table + summary |
| GET | `/api/data/{project}/correlation` | Correlation matrix |
| GET | `/api/data/{project}/shifts` | Descriptor shifts upon adsorption |
| GET | `/api/data/{project}/structures` | List XYZ structures |
| GET | `/api/data/{project}/structure/{label}` | 3D visualization data |
| GET | `/api/data/{project}/charges/{label}` | Mulliken charge distribution |

### Thermodynamics
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/thermo/{project}/coverage-vs-pressure` | Langmuir isotherm vs P |
| POST | `/api/thermo/{project}/coverage-vs-temperature` | Coverage vs T |
| POST | `/api/thermo/{project}/t50` | Desorption midpoint T50 |
| POST | `/api/thermo/{project}/compare` | Compare systems thermodynamically |

### Machine Learning
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ml/{project}/symbolic-regression` | Discover interpretable formulas |
| POST | `/api/ml/{project}/gp-predict` | Gaussian Process predictions |
| POST | `/api/ml/{project}/suggest-next` | Active learning suggestions |
| POST | `/api/ml/{project}/feature-importance` | Feature importance ranking |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Multi-agent query (requires API key) |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

## Project System

The built-in `zr-tio2` project contains data for Zr-decorated TiO2 nanoparticles (pristine, 1Zr, 2Zr configurations, with and without adsorbed H2).

To analyze your own materials:

1. Create a project via the UI or `POST /api/projects`
2. Upload a CSV with a `system_label` column and numeric descriptor columns
3. Upload XYZ geometry files (optionally with Mulliken charges as a 5th column)
4. All analysis tools automatically work with your data

## ML Capabilities

| Method | Purpose | Best For |
|--------|---------|----------|
| Symbolic Regression | Discover E_ads = f(descriptors) | Interpretable relationships |
| Gaussian Process | Predict E_ads with uncertainty | Small datasets (n < 20) |
| Active Learning | Rank untested dopants | Experiment planning |
| Feature Importance | Identify key descriptors | Understanding what drives adsorption |

## Tech Stack

- **Backend**: Python, FastAPI, LangGraph, LangChain, scikit-learn, PySR
- **Frontend**: React, Vite, Tailwind CSS, 3Dmol.js, Recharts
- **LLM**: OpenRouter (Claude Sonnet)
- **Data**: CDFT descriptors from Gaussian 16, XYZ geometries with Mulliken charges

## License

MIT
