# core/openai_safe.py  (new tiny helper)
from __future__ import annotations
import openai, json

def chat(system_msg: str,
         model: str = "gpt-4o-mini",
         temperature: float = 0.1) -> str:
    """Client-version–safe ChatCompletion wrapper."""
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    if hasattr(openai, "chat"):                  # ≥1.0
        rsp = openai.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[{"role": "system", "content": system_msg}],
        )
        return rsp.choices[0].message.content

    # 0.x fallback (sync)
    rsp = openai.ChatCompletion.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "system", "content": system_msg}],
    )
    return rsp["choices"][0]["message"]["content"]