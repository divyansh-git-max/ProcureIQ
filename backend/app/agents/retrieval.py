from app.agents.state import AgentState


async def retrieve_context(state: AgentState) -> AgentState:
    """Run hybrid search over contracts, POs, invoices, GRNs, and vendor evidence."""
    state.setdefault("agent_path", []).append("retrieval")
    return state

