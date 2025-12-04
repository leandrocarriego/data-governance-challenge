from abc import ABC, abstractmethod

class LLMService(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text completion given a prompt."""
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return available model identifiers."""
        raise NotImplementedError
