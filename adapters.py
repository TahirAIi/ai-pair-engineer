from abc import ABC, abstractmethod

from exceptions import AnalysisError, CapacityError
from openai import APIConnectionError, APIError, RateLimitError, OpenAI


class LLMAdapter(ABC):
    """Normalizes any LLM SDK to a common interface.
    """

    @abstractmethod
    def generate_response(self, system_prompt: str, user_message: str) -> str:
        """Send a prompt via the underlying SDK and return raw response text.

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

    def generate_response(self, system_prompt: str, user_message: str) -> str:

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
        except (APIError, APIConnectionError, RateLimitError) as e:
            raise CapacityError("DeepSeek API is at capacity") from e

        if not response.choices:
            raise AnalysisError("DeepSeek returned an empty response")

        raw = response.choices[0].message.content
        if not raw:
            raise AnalysisError("DeepSeek returned empty message content")

        return raw
