class IngestionService:
    """Coordinates document intake before expensive AI work starts."""

    async def enqueue(self, filename: str) -> str:
        return f"queued_{filename}"

