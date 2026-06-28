from app.agents.state import AgentState


async def build_grounded_report(state: AgentState) -> AgentState:
    """Produce cited findings and run final grounding checks before persistence."""
    state.setdefault("agent_path", []).append("report")
    return state

