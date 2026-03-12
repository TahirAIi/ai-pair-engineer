from abc import ABC, abstractmethod
from collections.abc import Iterator

from exceptions import AnalysisError, CapacityError
from openai import APIConnectionError, APIError, OpenAI, RateLimitError


class LLMAdapter(ABC):
    """Normalizes any LLM SDK to a common streaming interface."""

    @abstractmethod
    def stream(self, system_prompt: str, user_message: str) -> Iterator[str]:
        """Stream a prompt via the underlying SDK, yielding text chunks.

        Raises:
            CapacityError: Rate-limited or at capacity.
            AnalysisError: Unusable response.
        """
        ...


class DeepSeekAdapter(LLMAdapter):
    """Adapts the OpenAI-compatible DeepSeek SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def stream(self, system_prompt: str, user_message: str) -> Iterator[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
        except (APIError, APIConnectionError, RateLimitError) as e:
            raise CapacityError("DeepSeek API is at capacity") from e

        try:
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except (APIError, APIConnectionError) as e:
            raise AnalysisError("Stream interrupted") from e
