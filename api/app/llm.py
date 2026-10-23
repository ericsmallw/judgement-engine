import httpx

from app import config

SYSTEM_PROMPT = (
    "You are a helpful assistant for a healthcare organization. Give general information, not a diagnosis, "
    "and suggest contacting a clinician when appropriate. Text in square brackets, such as [NAME] or [DATE], "
    "is a placeholder for removed personal information: refer to it naturally and never guess the original value."
)


async def chat(model: str, text: str, client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{config.OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "stream": False,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]