class RiskScoringService:
    """Computes transparent vendor and finding risk scores."""

    def vendor_score(self, parts: dict[str, int]) -> int:
        return round(sum(parts.values()) / max(len(parts), 1))

