class EvaluationService:
    """Tracks RAG quality, route correctness, latency, and agent success."""

    async def latest_health(self) -> dict[str, list[object]]:
        return {
            "slos": [],
            "latency_data": [],
            "ragas_metrics": [],
            "trajectory_eval": [],
            "traces": [],
            "guardrail_log": [],
        }

