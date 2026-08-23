"""Provider-agnostic LLM client."""
from __future__ import annotations

import json
import re
import sys
import time
from typing import Optional

from .helpers import env, model_config

_RETRY_AFTER = re.compile(r"try again in\s*([\d.]+)\s*s", re.IGNORECASE)


def _transient_error_types() -> tuple:
    """Groq exception classes that are worth retrying (network/rate/5xx)."""
    try:
        from groq import (
            APIConnectionError, APITimeoutError, InternalServerError, RateLimitError,
        )
        return (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError)
    except Exception:
        return (Exception,)


def _rate_limit_type():
    try:
        from groq import RateLimitError

        return RateLimitError
    except Exception:
        return None


def _suggested_wait(exc: Exception, fallback: float, cap: float = 20.0) -> float:
    """Seconds to wait before retrying a rate-limited call: prefer the API's
    Retry-After header, then the 'try again in Ns' hint, else the fallback."""
    header = None
    try:
        header = exc.response.headers.get("retry-after")  # type: ignore[attr-defined]
    except Exception:
        header = None
    if header:
        try:
            return min(float(header) + 0.5, cap)
        except ValueError:
            pass
    match = _RETRY_AFTER.search(str(exc))
    if match:
        return min(float(match.group(1)) + 0.5, cap)
    return min(fallback, cap)


class LLMClient:
    def __init__(self) -> None:
        cfg = model_config().get("llm", {})
        self.provider = env("LLM_PROVIDER", cfg.get("provider", "mock")).lower()
        self.model = env("GROQ_MODEL", cfg.get("model", "openai/gpt-oss-20b"))
        self.temperature = float(cfg.get("temperature", 0.1))
        self.max_tokens = int(cfg.get("max_tokens", 800))
        self.timeout = int(env("GROQ_TIMEOUT", cfg.get("request_timeout_seconds", 60)))
        self.max_retries = int(cfg.get("max_retries", 2))
        self.rate_limit_retries = int(cfg.get("rate_limit_retries", 4))
        self.retry_backoff = float(cfg.get("retry_backoff_seconds", 1.5))
        self._client = None
        self._transient = (Exception,)
        self._rate_limit = None
        self._init_error: Optional[str] = None
        self._warned = False
        if self.provider == "groq":
            self._init_groq()

    def _init_groq(self) -> None:
        api_key = env("GROQ_API_KEY")
        if not api_key:
            self._init_error = "GROQ_API_KEY is not set; falling back to mock behaviour."
            self.provider = "mock"
            return
        try:
            from groq import Groq

            # Our own retry loop owns retries/backoff, so disable the SDK's.
            self._client = Groq(api_key=api_key, timeout=self.timeout, max_retries=0)
            self._transient = _transient_error_types()
            self._rate_limit = _rate_limit_type()
        except Exception as exc:
            self._init_error = f"Groq SDK unavailable ({exc}); falling back to mock behaviour."
            self.provider = "mock"

    @property
    def available(self) -> bool:
        """True when real LLM calls can be made."""
        return self.provider == "groq" and self._client is not None

    def chat(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """Single-turn chat completion. Only call when `available` is True."""
        if not self.available:
            raise RuntimeError("LLMClient.chat called while provider is mock/unavailable.")
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        last_exc: Optional[Exception] = None
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._client.chat.completions.create(**kwargs)
                return (resp.choices[0].message.content or "").strip()
            except Exception as exc:
                last_exc = exc
                is_rate_limit = self._rate_limit is not None and isinstance(exc, self._rate_limit)
                if is_rate_limit and attempt <= self.rate_limit_retries:
                    # Pace under the rate limit using the API's own hint.
                    time.sleep(_suggested_wait(exc, self.retry_backoff * attempt))
                    continue
                if (not is_rate_limit and isinstance(exc, self._transient)
                        and attempt <= self.max_retries):
                    time.sleep(self.retry_backoff * attempt)  # linear backoff
                    continue
                break

        if not self._warned:
            self._warned = True
            print(f"[llm_client] WARNING: Groq call failed for model '{self.model}' "
                  f"after {attempt - 1} retr(y/ies) - falling back to offline "
                  f"draft/heuristics. Reason: {last_exc}", file=sys.stderr)
        raise last_exc

    def chat_json(self, system: str, user: str, temperature: Optional[float] = None) -> dict:
        """Chat expecting a JSON object back. Returns {} on parse failure."""
        raw = self.chat(system, user, temperature=temperature, json_mode=True)
        try:
            return json.loads(raw)
        except Exception:
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except Exception:
                    return {}
            return {}

    def describe(self) -> str:
        if self.available:
            return f"groq:{self.model}"
        note = f" ({self._init_error})" if self._init_error else ""
        return f"mock{note}"

_SINGLETON: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = LLMClient()
    return _SINGLETON
