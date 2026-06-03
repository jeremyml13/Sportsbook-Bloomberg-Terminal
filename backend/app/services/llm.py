from typing import Any
from urllib.request import Request, urlopen
import json

from app.core.config import settings


class LLMError(RuntimeError):
    pass


SYSTEM_PROMPT = """You are Market Copilot for a sports betting market intelligence terminal.
Explain odds, market movement, book disagreement, stale prices, no-vig probability, injuries, and EV math.
Do not claim a bet is guaranteed profitable. Use only the provided application context.
If context is missing, say what is missing. Keep the answer concise and analytical.
Format with short markdown headings, bullets, and at most one compact markdown table when useful. Do not use HTML."""


def ask_market_copilot(message: str, context: dict[str, Any]) -> tuple[str, str]:
    if not settings.do_model_access_key:
        raise LLMError("DO_MODEL_ACCESS_KEY is not configured.")

    model = settings.do_inference_model
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Application context:\n"
                    f"{json.dumps(context, default=str)}\n\n"
                    f"User question: {message}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 180,
    }
    request = Request(
        f"{settings.do_inference_base_url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.do_model_access_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except Exception as exc:
        raise LLMError(f"DigitalOcean inference request failed: {exc}") from exc

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("DigitalOcean inference returned an unexpected response shape.") from exc

    return answer.strip(), model
