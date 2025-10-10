"""
Unified LLM Client for OpenAI and Anthropic APIs

Provides a consistent interface for:
- OpenAI GPT-4-Turbo
- Anthropic Claude-3.5-Sonnet
- Anthropic Claude-3.5-Haiku

Features:
- Async/await support for parallel execution
- Error handling with exponential backoff
- Token usage tracking
- Response caching
- Model selection and configuration
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from dataclasses import dataclass
import json

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import aiohttp


@dataclass
class LLMResponse:
    """Standardized LLM response object"""
    content: str
    provider: str
    model: str
    tokens_used: Dict[str, int]  # {prompt: X, completion: Y, total: Z}
    finish_reason: str
    timestamp: datetime
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class LLMUsageStats:
    """Track token usage for cost monitoring"""
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_requests: int = 0
    total_cost: float = 0.0

    def add_usage(self, prompt: int, completion: int, cost: float):
        """Add usage from a request"""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += (prompt + completion)
        self.total_requests += 1
        self.total_cost += cost


class LLMClient:
    """
    Unified client for OpenAI and Anthropic LLM APIs

    Usage:
        client = LLMClient()
        response = await client.chat(
            messages=[{"role": "user", "content": "Analyze this stock..."}],
            provider="openai",
            model="gpt-4-turbo"
        )
    """

    # Model pricing (per 1K tokens)
    PRICING = {
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3.5-haiku": {"input": 0.0008, "output": 0.004},
    }

    # Model name mappings
    MODEL_NAMES = {
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "claude-3.5-sonnet": "claude-3-5-sonnet-latest",  # Latest available
        "claude-3-opus": "claude-3-opus-20240229",  # Fallback
        "claude-3.5-haiku": "claude-3-5-haiku-latest",
    }

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None
    ):
        """
        Initialize LLM client with API keys

        Args:
            openai_api_key: OpenAI API key (defaults to env var)
            anthropic_api_key: Anthropic API key (defaults to env var)
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')

        self.logger = logging.getLogger(__name__)
        self.usage_stats = LLMUsageStats()

        # Initialize clients
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        if self.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
        else:
            self.anthropic_client = None

    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Literal["openai", "anthropic"] = "openai",
        model: str = "gpt-4-turbo",
        temperature: float = 0.2,
        max_tokens: int = 4000,
        json_mode: bool = False,
        retry_attempts: int = 3
    ) -> LLMResponse:
        """
        Send chat completion request to LLM

        Args:
            messages: List of message dicts with role and content
            provider: "openai" or "anthropic"
            model: Model name (simplified)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response tokens
            json_mode: Force JSON output (OpenAI only)
            retry_attempts: Number of retries on failure

        Returns:
            LLMResponse object with standardized response
        """
        for attempt in range(retry_attempts):
            try:
                if provider == "openai":
                    return await self._openai_chat(
                        messages, model, temperature, max_tokens, json_mode
                    )
                elif provider == "anthropic":
                    return await self._anthropic_chat(
                        messages, model, temperature, max_tokens
                    )
                else:
                    raise ValueError(f"Unknown provider: {provider}")

            except Exception as e:
                self.logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{retry_attempts}): {e}"
                )

                if attempt < retry_attempts - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    # Final attempt failed
                    raise

    async def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> LLMResponse:
        """Call OpenAI API (New API >= 1.0.0)"""

        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        # Map to actual model name
        actual_model = self.MODEL_NAMES.get(model, model)

        # Prepare request
        request_params = {
            "model": actual_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if json_mode:
            request_params["response_format"] = {"type": "json_object"}

        # Make request using new API
        response = await self.openai_client.chat.completions.create(**request_params)

        # Extract data
        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        usage = response.usage

        # Calculate cost
        cost = self._calculate_cost(
            model,
            usage.prompt_tokens,
            usage.completion_tokens
        )

        # Track usage
        self.usage_stats.add_usage(
            usage.prompt_tokens,
            usage.completion_tokens,
            cost
        )

        self.logger.info(
            f"OpenAI {model}: {usage.total_tokens} tokens, ${cost:.4f}"
        )

        return LLMResponse(
            content=content,
            provider="openai",
            model=model,
            tokens_used={
                "prompt": usage.prompt_tokens,
                "completion": usage.completion_tokens,
                "total": usage.total_tokens
            },
            finish_reason=finish_reason,
            timestamp=datetime.now(),
            raw_response=response.model_dump()
        )

    async def _anthropic_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Call Anthropic API"""

        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")

        # Map to actual model name
        actual_model = self.MODEL_NAMES.get(model, model)

        # Convert messages to Anthropic format
        # Anthropic requires system message separate
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Make request
        request_params = {
            "model": actual_model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if system_message:
            request_params["system"] = system_message

        response = await self.anthropic_client.messages.create(**request_params)

        # Extract data
        content = response.content[0].text
        finish_reason = response.stop_reason

        # Calculate tokens and cost
        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens

        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        # Track usage
        self.usage_stats.add_usage(prompt_tokens, completion_tokens, cost)

        self.logger.info(
            f"Anthropic {model}: {prompt_tokens + completion_tokens} tokens, ${cost:.4f}"
        )

        return LLMResponse(
            content=content,
            provider="anthropic",
            model=model,
            tokens_used={
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": prompt_tokens + completion_tokens
            },
            finish_reason=finish_reason,
            timestamp=datetime.now(),
            raw_response=response.model_dump()
        )

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for a request"""

        if model not in self.PRICING:
            self.logger.warning(f"No pricing info for model: {model}")
            return 0.0

        pricing = self.PRICING[model]

        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            "total_requests": self.usage_stats.total_requests,
            "total_tokens": self.usage_stats.total_tokens,
            "prompt_tokens": self.usage_stats.prompt_tokens,
            "completion_tokens": self.usage_stats.completion_tokens,
            "total_cost": round(self.usage_stats.total_cost, 4),
            "avg_tokens_per_request": (
                self.usage_stats.total_tokens / self.usage_stats.total_requests
                if self.usage_stats.total_requests > 0 else 0
            ),
            "avg_cost_per_request": (
                self.usage_stats.total_cost / self.usage_stats.total_requests
                if self.usage_stats.total_requests > 0 else 0
            )
        }

    def reset_usage_stats(self):
        """Reset usage statistics"""
        self.usage_stats = LLMUsageStats()
        self.logger.info("Usage statistics reset")


class CachedLLMClient(LLMClient):
    """
    LLM client with built-in response caching

    Useful for management analyst (quarterly reports) and other
    analyses that don't change frequently
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        cache_ttl_seconds: int = 7776000  # 90 days default
    ):
        super().__init__(openai_api_key, anthropic_api_key)
        self.cache: Dict[str, tuple[LLMResponse, float]] = {}
        self.cache_ttl = cache_ttl_seconds
        self.cache_hits = 0
        self.cache_misses = 0

    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Literal["openai", "anthropic"] = "openai",
        model: str = "gpt-4-turbo",
        temperature: float = 0.2,
        max_tokens: int = 4000,
        json_mode: bool = False,
        retry_attempts: int = 3,
        cache_key: Optional[str] = None
    ) -> LLMResponse:
        """
        Chat with caching support

        Args:
            cache_key: If provided, will cache/retrieve based on this key
            ... (other args same as parent class)
        """

        # Check cache if key provided
        if cache_key:
            cached = self._get_from_cache(cache_key)
            if cached:
                self.cache_hits += 1
                self.logger.info(f"Cache HIT for key: {cache_key}")
                return cached
            else:
                self.cache_misses += 1

        # Cache miss or no caching - call API
        response = await super().chat(
            messages, provider, model, temperature,
            max_tokens, json_mode, retry_attempts
        )

        # Store in cache if key provided
        if cache_key:
            self._store_in_cache(cache_key, response)

        return response

    def _get_from_cache(self, key: str) -> Optional[LLMResponse]:
        """Get response from cache if not expired"""
        if key not in self.cache:
            return None

        response, timestamp = self.cache[key]
        age = datetime.now().timestamp() - timestamp

        if age > self.cache_ttl:
            # Expired
            del self.cache[key]
            return None

        return response

    def _store_in_cache(self, key: str, response: LLMResponse):
        """Store response in cache"""
        self.cache[key] = (response, datetime.now().timestamp())

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_ttl_seconds": self.cache_ttl
        }


# Example usage
async def example_usage():
    """Example usage of LLM client"""

    # Initialize client
    client = LLMClient()

    # OpenAI request
    messages = [
        {
            "role": "system",
            "content": "You are a financial analyst providing stock analysis."
        },
        {
            "role": "user",
            "content": "Analyze Reliance Industries fundamentals in 100 words."
        }
    ]

    response = await client.chat(
        messages=messages,
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.2
    )

    print(f"Response: {response.content}")
    print(f"Tokens: {response.tokens_used}")

    # Anthropic request
    response2 = await client.chat(
        messages=messages,
        provider="anthropic",
        model="claude-3.5-haiku",
        temperature=0.2
    )

    print(f"\nClaude Response: {response2.content}")

    # Get usage stats
    stats = client.get_usage_stats()
    print(f"\nUsage Stats: {stats}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(example_usage())
