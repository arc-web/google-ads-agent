"""
OpenRouter LLM client wrapper for the google_ads_agent copy engine.

Supports Kimi-K2 (default) with Gemini 2.5 Flash fallback.
Uses requests only - no OpenAI or Anthropic SDKs.
"""

import os
import time
import json
import subprocess
import requests
from pathlib import Path

DEFAULT_MODEL = "moonshotai/kimi-k2"
FALLBACK_MODEL = "google/gemini-2.5-flash"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

RETRY_STATUSES = {429, 500, 503}
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds
REQUEST_TIMEOUT = 60  # seconds

# Local cache for the key - avoids repeated SSH fetches
_TOKEN_CACHE = Path.home() / ".cache" / "google_ads_agent" / "openrouter_token"
_TOKEN_TTL = 3600  # 1 hour


def _fetch_openrouter_key() -> str:
    """
    Fetch OpenRouter API key using: env var -> local cache -> OpenBao via SSH.
    Pattern mirrors plane_agent/plane get_token().
    """
    # 1. Env var override
    if key := os.environ.get("OPENROUTER_API_KEY"):
        return key

    # 2. Local cache with TTL
    _TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if _TOKEN_CACHE.exists() and time.time() - _TOKEN_CACHE.stat().st_mtime < _TOKEN_TTL:
        cached = _TOKEN_CACHE.read_text().strip()
        if cached:
            return cached

    # 3. Fetch from 1Password via local op CLI
    try:
        result = subprocess.run(
            ["op", "item", "get", "53matr2yq5fmikn3hl2obt5kku",
             "--vault", "ARC", "--fields", "label=credential", "--reveal"],
            capture_output=True, text=True, timeout=15, check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"1Password fetch failed: {e.stderr.strip()}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("1Password fetch timed out") from e
    except FileNotFoundError as e:
        raise RuntimeError("op CLI not found - install 1Password CLI") from e

    key = result.stdout.strip()

    # Cache it
    _TOKEN_CACHE.write_text(key)
    _TOKEN_CACHE.chmod(0o600)
    return key


class OpenRouterClient:
    """Thin wrapper around the OpenRouter chat completions endpoint."""

    def __init__(self):
        api_key = _fetch_openrouter_key()
        self._api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post(self, payload: dict) -> dict:
        """POST to OpenRouter with retry logic on transient errors."""
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.post(
                    OPENROUTER_URL,
                    headers=self._headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                if resp.status_code in RETRY_STATUSES and attempt < MAX_RETRIES:
                    print(
                        f"[openrouter] HTTP {resp.status_code} on attempt {attempt}/{MAX_RETRIES} "
                        f"- retrying in {RETRY_BACKOFF}s"
                    )
                    time.sleep(RETRY_BACKOFF)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    print(
                        f"[openrouter] Request error on attempt {attempt}/{MAX_RETRIES}: {exc} "
                        f"- retrying in {RETRY_BACKOFF}s"
                    )
                    time.sleep(RETRY_BACKOFF)
        raise RuntimeError(
            f"OpenRouter request failed after {MAX_RETRIES} attempts: {last_exc}"
        )

    def _build_payload(
        self, system: str, user: str, max_tokens: int, model: str
    ) -> dict:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
        }

    def _log(self, model: str, data: dict) -> None:
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", "?")
        completion_tokens = usage.get("completion_tokens", "?")
        print(
            f"[openrouter] model={model} "
            f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 2000,
        model: str = DEFAULT_MODEL,
    ) -> str:
        """
        Call the model and return the response as a plain string.

        Args:
            system:     System prompt.
            user:       User message.
            max_tokens: Maximum tokens to generate.
            model:      Model override (defaults to moonshot/kimi-k2).

        Returns:
            Response text from the model.
        """
        payload = self._build_payload(system, user, max_tokens, model)
        data = self._post(payload)
        self._log(model, data)
        return data["choices"][0]["message"]["content"]

    def complete_json(
        self,
        system: str,
        user: str,
        schema: dict,
        max_tokens: int = 2000,
        model: str = DEFAULT_MODEL,
    ) -> dict:
        """
        Call the model expecting a JSON response that matches schema.

        Retries once on JSON parse failure before raising. The schema dict
        is appended to the user prompt as context; no strict JSON mode is
        assumed since not all OpenRouter models support it.

        Args:
            system:     System prompt.
            user:       User message.
            schema:     Expected JSON schema (dict) - appended to prompt for guidance.
            max_tokens: Maximum tokens to generate.
            model:      Model override (defaults to moonshot/kimi-k2).

        Returns:
            Parsed dict from model response.

        Raises:
            ValueError: If response cannot be parsed as JSON after one retry.
        """
        schema_hint = (
            "\n\nRespond with valid JSON only. No markdown, no code fences. "
            f"Schema: {json.dumps(schema)}"
        )
        augmented_user = user + schema_hint

        for attempt in range(1, 3):  # 2 attempts total
            payload = self._build_payload(system, augmented_user, max_tokens, model)
            data = self._post(payload)
            self._log(model, data)
            raw = data["choices"][0]["message"]["content"].strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()

            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                if attempt == 1:
                    print(
                        f"[openrouter] JSON parse failed on attempt 1: {exc} - retrying"
                    )
                    continue
                raise ValueError(
                    f"Model returned non-JSON after 2 attempts. Last error: {exc}\n"
                    f"Raw response: {raw[:500]}"
                ) from exc

        # Should never reach here, but satisfies type checkers
        raise ValueError("complete_json: unexpected exit from retry loop")
