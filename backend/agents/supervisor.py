from agents.state import AgentState


async def route(state: AgentState) -> AgentState:
    """Decide which agent nodes should run for the current procurement task."""
    state.setdefault("agent_path", []).append("supervisor")
    return state

