"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

import logging
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)

COST_PER_1K_INPUT = 0.00015
COST_PER_1K_OUTPUT = 0.0006


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client using OpenAI API."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion via OpenAI API with retry logic."""
        from openai import OpenAI
        
        if not self._settings.openai_api_key or self._settings.openai_api_key == "...":
            logger.warning("OPENAI_API_KEY is not set. Using mock LLM response.")
            # Simulate a small delay
            import time
            time.sleep(1)
            
            # Simple mock response
            mock_content = f"Mock response for query. "
            if "research assistant" in system_prompt:
                mock_content += "Here are the key findings with citations [1], [2]."
            elif "analyst" in system_prompt:
                mock_content += "1) Key claim: valid. 2) Conflicting viewpoints: None. 3) Evidence: Strong."
            elif "writer" in system_prompt:
                mock_content += "This is the comprehensive final answer. According to sources [1], the state of the art is advancing rapidly. Furthermore, [2] highlights important developments."
            else:
                mock_content += "This is a standard mock response."
                
            return LLMResponse(
                content=mock_content,
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.0001
            )

        client = OpenAI(api_key=self._settings.openai_api_key)
        model = self._settings.openai_model

        logger.info("LLM request: model=%s, system_len=%d, user_len=%d", model, len(system_prompt), len(user_prompt))

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        choice = response.choices[0]
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None

        cost_usd = None
        if input_tokens is not None and output_tokens is not None:
            cost_usd = (input_tokens * COST_PER_1K_INPUT + output_tokens * COST_PER_1K_OUTPUT) / 1000

        logger.info(
            "LLM response: input=%s, output=%s, cost=%.6f",
            input_tokens,
            output_tokens,
            cost_usd or 0.0,
        )

        return LLMResponse(
            content=choice.message.content or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )
