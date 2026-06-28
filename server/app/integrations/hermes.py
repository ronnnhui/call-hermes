from collections.abc import AsyncIterator

import httpx

from app.config import Settings


class HermesClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def health(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(f"{self._settings.hermes_base_url.rstrip('/')}/health")
            if response.status_code < 500:
                return True, f"HTTP {response.status_code}"
            return False, f"HTTP {response.status_code}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    async def stream_chat(self, user_text: str) -> AsyncIterator[str]:
        headers = {"Accept": "text/event-stream"}
        if self._settings.hermes_api_key:
            headers["Authorization"] = f"Bearer {self._settings.hermes_api_key}"

        payload = {
            "model": self._settings.hermes_model,
            "messages": [],
            "stream": True,
        }
        if self._settings.hermes_system_prompt:
            payload["messages"].append(
                {"role": "system", "content": self._settings.hermes_system_prompt}
            )
        payload["messages"].append({"role": "user", "content": user_text})

        timeout = httpx.Timeout(self._settings.hermes_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self._settings.hermes_base_url.rstrip('/')}/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ").strip()
                    if data == "[DONE]":
                        break
                    text = _extract_openai_delta(data)
                    if text:
                        yield text


def _extract_openai_delta(data: str) -> str:
    import json

    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return ""
    choices = payload.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    return content if isinstance(content, str) else ""
