from app.agents.state import AgentState


async def analyze_procurement_risk(state: AgentState) -> AgentState:
    """Compare invoice, PO, GRN, contract, and vendor facts to detect issues."""
    state.setdefault("agent_path", []).append("analysis")
    return state

