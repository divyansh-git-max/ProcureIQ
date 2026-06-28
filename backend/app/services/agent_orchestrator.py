from app.agents import analysis, report, retrieval, supervisor, websearch
from app.agents.state import AgentState


async def run_procurement_graph(initial_state: AgentState) -> AgentState:
    """Temporary linear stand-in for the planned LangGraph workflow."""
    state = await supervisor.route(initial_state)
    state = await retrieval.retrieve_context(state)

    if state.get("intent") == "vendor_lookup":
        state = await websearch.refresh_external_vendor_signals(state)

    state = await analysis.analyze_procurement_risk(state)
    return await report.build_grounded_report(state)

