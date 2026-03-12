class PairEngineerError(Exception):
    """Base exception for PairEngineer errors."""


class CapacityError(PairEngineerError):
    """Raised when the AI provider is at capacity or rate-limited."""


class AnalysisError(PairEngineerError):
    """Raised when code analysis fails."""
