"""LangGraph multi-agent state graph for materials science analysis."""

from __future__ import annotations

import json
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from ..llm_config import get_llm

from .descriptor_agent import run_descriptor_agent
from .structure_agent import run_structure_agent
from .thermo_agent import run_thermo_agent
from .screening_agent import run_screening_agent
from .reasoning_agent import run_reasoning_agent


class AgentState(TypedDict):
    """State passed between agents in the graph."""
    messages: list  # Chat history
    project: str  # Active project name
    query: str  # Current user query
    route: str  # Which agent to route to
    agent_results: Annotated[dict, operator.ior]  # Results from specialist agents
    final_response: str  # Synthesized final response
    active_agents: list[str]  # Which agents were invoked


# The LLM used for routing and synthesis
def _get_llm():
    return get_llm(max_tokens=1000)  # Reduced for faster responses


ROUTER_SYSTEM_PROMPT = """Route user queries to agents. Respond with JSON only.

Agents:
- descriptor: Electronic properties (HOMO, LUMO, band gap)
- structure: 3D geometry, coordination, charges
- thermo: Coverage, desorption temp, thermodynamics
- screening: ML predictions, symbolic regression
- reasoning: Explanations and context

Examples:
{"routes": ["descriptor"]} - properties questions
{"routes": ["structure"]} - 3D structure
{"routes": ["thermo"]} - coverage/temperature
{"routes": ["screening"]} - ML/predictions
{"routes": ["descriptor", "thermo", "reasoning"]} - "why" questions

Respond ONLY with JSON: {"routes": [...]}


SYNTHESIS_SYSTEM_PROMPT = """You are a materials science expert synthesizing results from multiple specialist agents.
You have received analysis from different specialists. Combine their findings into a clear, concise response.

Guidelines:
- Lead with the most important finding
- Use specific numbers and values from the agent results
- Explain the physical significance of computational results
- Keep the response focused and actionable
- If results include visualization data (3D structures, plots), mention that visualizations are available in the corresponding tabs
- Format nicely with markdown when helpful"""


def route_query(state: AgentState) -> AgentState:
    """Use LLM to classify the query and determine which agents to invoke."""
    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=f"Project: {state['project']}\nQuery: {state['query']}"),
    ])

    try:
        routing = json.loads(response.content)
        routes = routing.get("routes", ["reasoning"])
    except (json.JSONDecodeError, AttributeError):
        routes = ["reasoning"]  # Fallback

    # Validate routes
    valid_routes = {"descriptor", "structure", "thermo", "screening", "reasoning"}
    routes = [r for r in routes if r in valid_routes]
    if not routes:
        routes = ["reasoning"]

    return {**state, "route": routes[0], "active_agents": routes, "agent_results": {}}


def run_agents(state: AgentState) -> AgentState:
    """Run all routed specialist agents and collect results."""
    results = {}
    agent_map = {
        "descriptor": run_descriptor_agent,
        "structure": run_structure_agent,
        "thermo": run_thermo_agent,
        "screening": run_screening_agent,
        "reasoning": run_reasoning_agent,
    }

    # Run agents sequentially (safe for Uvicorn/FastAPI)
    for agent_name in state["active_agents"]:
        if agent_name in agent_map:
            try:
                results[agent_name] = agent_map[agent_name](state["query"], state["project"])
            except Exception as e:
                results[agent_name] = {"error": str(e)}
        else:
            results[agent_name] = {"error": "Unknown agent"}

    return {**state, "agent_results": results}


def synthesize_response(state: AgentState) -> AgentState:
    """Synthesize results from all agents into a final response."""
    llm = _get_llm()

    # Build context from agent results
    results_text = ""
    for agent_name, result in state["agent_results"].items():
        results_text += f"\n--- {agent_name.upper()} AGENT ---\n"
        if isinstance(result, dict):
            results_text += json.dumps(result, indent=2, default=str)[:3000]
        else:
            results_text += str(result)[:3000]

    response = llm.invoke([
        SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(content=f"User query: {state['query']}\n\nProject: {state['project']}\n\nAgent results:\n{results_text}"),
    ])

    return {**state, "final_response": response.content}


def build_graph() -> StateGraph:
    """Build the LangGraph state graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", route_query)
    graph.add_node("agents", run_agents)
    graph.add_node("synthesizer", synthesize_response)

    # Add edges: router → agents → synthesizer → END
    graph.set_entry_point("router")
    graph.add_edge("router", "agents")
    graph.add_edge("agents", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Compiled graph instance
materials_graph = build_graph()


async def run_query(query: str, project: str, messages: list | None = None) -> dict:
    """Run a query through the multi-agent graph.

    Returns dict with 'response', 'active_agents', and 'agent_results'.
    """
    initial_state: AgentState = {
        "messages": messages or [],
        "project": project,
        "query": query,
        "route": "",
        "agent_results": {},
        "final_response": "",
        "active_agents": [],
    }

    # Use ainvoke for async execution (better for FastAPI)
    result = await materials_graph.ainvoke(initial_state)

    return {
        "response": result["final_response"],
        "active_agents": result["active_agents"],
        "agent_results": {
            k: _sanitize_for_json(v)
            for k, v in result["agent_results"].items()
        },
    }


def _sanitize_for_json(obj):
    """Make objects JSON-serializable."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        if obj != obj:  # NaN check
            return None
        return obj
    if isinstance(obj, (int, str, bool, type(None))):
        return obj
    return str(obj)
