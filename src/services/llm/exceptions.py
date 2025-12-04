class GeminiServiceError(Exception):
    pass


class GeminiRateLimitError(GeminiServiceError):
    def __init__(self, message: str, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds