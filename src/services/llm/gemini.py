import logging

from google import genai
from google.genai import types

from src.services.llm.base import LLMService
from src.services.llm.exceptions import GeminiServiceError, GeminiRateLimitError
from src.services.llm.schemas import LLMConfig
from src.settings import settings


logger = logging.getLogger(__name__)


class GeminiService(LLMService):
    """Gemini LLM client wrapper."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config

        api_key = self._config.api_key or settings.gemini_api_key
        if not api_key or not genai:
            raise GeminiServiceError("Gemini service not configured or SDK missing")
        self._client = genai.Client(api_key=api_key)

        self.model = self._config.model

    def generate(self, prompt: str) -> str:
        """Generate text content from Gemini for the given prompt."""
        
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(tools=[], response_mime_type="text/plain")
                if types
                else None,
            )

            text = response.text if hasattr(response, "text") else None

            parts: list[str] = []
            if not text and hasattr(response, "candidates"):
                for candidate in response.candidates or []:
                    for part in getattr(getattr(candidate, "content", None), "parts", []) or []:
                        val = getattr(part, "text", None)
                        if isinstance(val, str):
                            parts.append(val)
                text = " ".join(parts) if parts else None

            return (text or " ".join(parts)).strip()
        
        except Exception as e:
            msg = str(e)

            is_rate_limit_error = "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()
            if is_rate_limit_error:
                retry_after = None
                # naive extraction of retry seconds if present
                for token in msg.split():
                    if token.endswith("s.") and token[:-2].replace(".", "", 1).isdigit():
                        try:
                            retry_after = float(token[:-2])
                            break
                        except ValueError:
                            retry_after = None
                logger.error("Gemini rate limit exceeded: %s", msg)
                raise GeminiRateLimitError(msg, retry_after_seconds=retry_after) from e
            
            logger.exception("Gemini generate failed.")
            raise GeminiServiceError(str(e)) from e

    def list_models(self) -> list[str]:
        """List available Gemini models."""
        
        try:
            models = self._client.models.list()

            return [m.name for m in models] if models else [] # type: ignore
        
        except Exception as e:
            logger.exception("Failed to list Gemini models.")
            raise GeminiServiceError(str(e)) from e
