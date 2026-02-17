"""Orchestrator: high-level entry point for the multi-agent system."""

from .graph import run_query


async def process_query(query: str, project: str = "zr-tio2",
                        messages: list | None = None) -> dict:
    """Process a user query through the multi-agent orchestration graph.

    Args:
        query: The user's question or request
        project: Active project name (default: built-in zr-tio2)
        messages: Optional prior conversation messages

    Returns:
        dict with 'response', 'active_agents', 'agent_results'
    """
    return await run_query(query, project, messages)
