"""
LLM Client - supports OpenAI-compatible APIs and Anthropic Claude.
Auto-detects provider from API key or LLM_PROVIDER env var.
Includes automatic retry with backoff for rate limits.
"""
import json
import re
import time
from typing import List, Dict, Any, Optional

from ..config import Settings
from .logger import get_logger

log = get_logger("vedang.llm")


class LLM:
    """Stateless LLM helper — one instance per lifetime is fine."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or Settings.LLM_API_KEY
        self.base_url = base_url or getattr(Settings, 'LLM_BASE_URL', '')
        self.model = model or Settings.LLM_MODEL_NAME
        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")

        # Detect provider
        provider = getattr(Settings, 'LLM_PROVIDER', '').lower()
        if provider == 'anthropic' or self.api_key.startswith('sk-ant-'):
            self._provider = 'anthropic'
            import anthropic
            self._anthropic = anthropic.Anthropic(api_key=self.api_key)
        else:
            self._provider = 'openai'
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=60.0)

    # ── plain text completion with retry ──────────────────────
    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_retries: int = 5,
    ) -> str:
        if self._provider == 'anthropic':
            return self._complete_anthropic(messages, temperature, max_tokens, max_retries)
        return self._complete_openai(messages, temperature, max_tokens, max_retries)

    def _complete_anthropic(self, messages, temperature, max_tokens, max_retries):
        """Call Anthropic Claude API."""
        # Separate system message from user/assistant messages
        system_text = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text += m["content"] + "\n"
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})

        # Ensure messages alternate user/assistant and start with user
        if not chat_messages or chat_messages[0]["role"] != "user":
            chat_messages.insert(0, {"role": "user", "content": "Please respond."})

        last_error = None
        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": chat_messages,
                }
                if system_text.strip():
                    kwargs["system"] = system_text.strip()

                resp = self._anthropic.messages.create(**kwargs)
                text = resp.content[0].text if resp.content else ""
                text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
                return text
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower() or "overloaded" in error_str.lower():
                    wait = self._extract_retry_delay(error_str, attempt)
                    log.warning("Claude rate limited (attempt %d/%d), waiting %.0fs", attempt + 1, max_retries, wait)
                    time.sleep(wait)
                else:
                    wait = min(2 ** attempt, 30)
                    log.warning("Claude error (attempt %d/%d): %s, retrying in %ds", attempt + 1, max_retries, error_str[:150], wait)
                    time.sleep(wait)
        raise last_error

    def _complete_openai(self, messages, temperature, max_tokens, max_retries):
        """Call OpenAI-compatible API."""
        last_error = None
        for attempt in range(max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = resp.choices[0].message.content or ""
                text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
                return text
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate" in error_str.lower():
                    wait = self._extract_retry_delay(error_str, attempt)
                    log.warning("Rate limited (attempt %d/%d), waiting %.0fs", attempt + 1, max_retries, wait)
                    time.sleep(wait)
                else:
                    wait = min(2 ** attempt, 30)
                    log.warning("LLM error (attempt %d/%d): %s, retrying in %ds", attempt + 1, max_retries, error_str[:150], wait)
                    time.sleep(wait)
        raise last_error

    @staticmethod
    def _extract_retry_delay(error_str: str, attempt: int) -> float:
        match = re.search(r"retry\s+in\s+([\d.]+)\s*s", error_str, re.I)
        if match:
            return float(match.group(1)) + 2
        return min(15 * (2 ** attempt), 60)

    # ── JSON completion ────────────────────────────────────────
    def complete_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        raw = self.complete(messages, temperature=temperature, max_tokens=max_tokens)
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(raw: str) -> Any:
        """Try hard to extract JSON from messy LLM output."""
        if not raw or not raw.strip():
            return {}

        text = raw.strip()

        # Strip markdown fences
        text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.I)
        text = re.sub(r"\n?```\s*$", "", text).strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Find JSON array
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return {}
