import json
import logging
import time
from dataclasses import dataclass

from adapters import LLMAdapter
from exceptions import AnalysisError, CapacityError

__all__ = ["PairEngineer", "AnalysisResult"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisResult:
    design_analysis: str
    generated_tests: str
    refactored_code: str
    score: int
    pair_notes: str

    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisResult":
        return cls(
            design_analysis=data.get("design_analysis", ""),
            generated_tests=data.get("generated_tests", ""),
            refactored_code=data.get("refactored_code", ""),
            score=data.get("score", 0),
            pair_notes=data.get("pair_notes", ""),
        )


DEFAULT_SYSTEM_PROMPT = """You are an expert senior pair programming partner working with Python code. You don't just review code — you actively collaborate. You understand the developer's intent, spot architectural issues, write tests, and refactor code. You're helpful, specific, and teach as you go.

When given code (and optionally the developer's intent/context), respond with a JSON object containing these keys:

{
  "design_analysis": "markdown string - architecture & design analysis",
  "generated_tests": "markdown string - complete runnable pytest test suite",
  "refactored_code": "markdown string - full refactored code with explanation",
  "score": 7,
  "pair_notes": "markdown string - conversational pair engineer advice"
}

Rules for each field:

**design_analysis**: Analyze the code's architecture and design. Identify design pattern issues and SOLID violations. Check for potential bugs due to concurrency or multithreading, missing locks, race conditions, idempotency issues, performance issues, N+1 queries, etc. Tag severity as Critical, Warning, or Info. Assess coupling, cohesion, separation of concerns. Check for potential security vulnerabilities. Be specific reference variable names, method names, class names.

**generated_tests**: Write a complete, runnable pytest test suite. Cover happy path, edge cases, and error/boundary cases. Use realistic test data. Include all necessary imports and setup. Make tests copy-paste ready.

**refactored_code**: Provide the COMPLETE refactored version of the code, not just snippets. Add brief inline comments explaining significant changes only. Include a changes summary at the end listing what changed and why.

**score**: Integer 1-10 representing overall code quality.

**pair_notes**: Start with "If I were pairing with you, I'd suggest..." and give conversational, actionable advice. List 2-3 concrete next steps. Be encouraging but honest.

Important:
- All string values should be valid markdown
- The code language is Python, use pytest for tests
- If context about what the developer is building is provided, factor that into your analysis
- Be constructive, not critical, you're a partner, not a gatekeeper
- Provide working code, not pseudocode
- If the code is very short or trivial, still provide meaningful feedback
- Return ONLY the JSON object, no other text before or after it
"""


_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = 3


class PairEngineer:
    def __init__(
        self,
        adapter: LLMAdapter,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        self.adapter = adapter
        self.system_prompt = system_prompt

    def _build_user_message(self, code: str, context: str) -> str:
        user_message = f"Here is the Python code to pair on:\n\n```python\n{code}\n```"
        if context.strip():
            user_message += f"\n\nDeveloper's context/intent: {context}"
        return user_message

    def analyze(self, code: str, context: str = "") -> AnalysisResult:
        if not code.strip():
            raise ValueError("Code must not be empty.")

        user_message = self._build_user_message(code, context)

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                raw = self.adapter.generate_response(self.system_prompt, user_message)
                return AnalysisResult.from_dict(json.loads(raw))
            except CapacityError as e:
                logger.error("Provider at capacity (attempt %d): %s", attempt + 1, e)
                last_error = e
            except (json.JSONDecodeError, AnalysisError) as e:
                logger.error("Failed to parse response (attempt %d): %s", attempt + 1, e)
                last_error = e

            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))

        if isinstance(last_error, CapacityError):
            raise last_error
        raise AnalysisError("Failed to analyze code") from last_error
