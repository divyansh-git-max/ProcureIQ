from agents.state import AgentState


async def refresh_external_vendor_signals(state: AgentState) -> AgentState:
    """Fetch external reputation or news signals when vendor risk needs context."""
    state.setdefault("agent_path", []).append("websearch")
    return state

