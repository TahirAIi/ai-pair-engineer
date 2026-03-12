import json
import logging
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Read from env var first, fall back to st.secrets."""
    value = os.getenv(key, "")
    if not value:
        try:
            value = st.secrets.get(key, default)
        except FileNotFoundError:
            value = default
    return value

SYSTEM_PROMPT = """You are an expert senior pair programming partner working with Python code. You don't just review code — you actively collaborate. You understand the developer's intent, spot architectural issues, write tests, and refactor code. You're helpful, specific, and teach as you go.

When given code (and optionally the developer's intent/context), respond with a JSON object containing these keys:

{
  "design_analysis": "markdown string - architecture & design analysis",
  "generated_tests": "markdown string - complete runnable pytest test suite",
  "refactored_code": "markdown string - full refactored code with explanation",
  "score": 7,
  "pair_notes": "markdown string - conversational pair engineer advice"
}

Rules for each field:

**design_analysis**: Analyze the code's architecture and design. Identify design pattern issues and SOLID violations. Check for potential bugs due to concurrency or multithreading, missing locks, race conditions, idempotency issues, peroformance issues, N+1 queries, etc. Tag severity as Critical, Warning, or Info. Assess coupling, cohesion, separation of concerns. Check for potential security vulnerabilities. Be specific reference variable names, method names, class names.

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


class PairEngineer:
    def __init__(self):
        api_key = _get_secret("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found.")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        self.model = _get_secret("DEEPSEEK_MODEL", "deepseek-chat")

    def _call_api(self, code: str, context: str) -> dict:
        user_message = f"Here is the Python code to pair on:\n\n```python\n{code}\n```"
        if context.strip():
            user_message += f"\n\nDeveloper's context/intent: {context}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        return json.loads(raw)

    def analyze(self, code: str, context: str = "") -> dict:
        for attempt in range(2):
            try:
                return self._call_api(code, context)
            except Exception as e:
                logger.error("API call failed (attempt %d): %s", attempt + 1, e)
                if attempt == 0:
                    continue
                raise RuntimeError("capacity") from e
