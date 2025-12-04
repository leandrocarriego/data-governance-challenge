from pydantic import BaseModel


class LLMConfig(BaseModel):
    api_key: str | None = None
    model: str
