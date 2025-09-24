# app/llm_utils.py
import requests
from .prompts import SYSTEM_PROMPT  # lean runtime system prompt

def call_llm(provider: str, api_key: str, question: str, context: str) -> str:
    provider = (provider or "").strip().lower()
    if provider == "groq":
        return _groq_call(api_key, question, context)
    if provider == "openai":
        return _openai_call(api_key, question, context)
    if provider == "gemini":
        return _gemini_call(api_key, question, context)
    if provider == "claude":
        return _claude_call(api_key, question, context)
    if provider in ("xai", "openrouter"):
        return "Provider integration not implemented yet."
    return "No provider selected; showing semantic chunk only."

# Backward compatibility alias if any older code refers to SYSTEM
SYSTEM = SYSTEM_PROMPT

def _raise_for_bad_response(r: requests.Response, key_path: str):
    try:
        data = r.json()
    except Exception:
        r.raise_for_status()
        raise RuntimeError("Non-JSON response from provider.")

    # Follow a simple dotted key lookup like "choices.0.message.content"
    cur = data
    for part in key_path.split("."):
        if part.isdigit():
            idx = int(part)
            if not isinstance(cur, list) or idx >= len(cur):
                raise RuntimeError(data.get("error", {}).get("message", str(data)))
            cur = cur[idx]
        else:
            if part not in cur:
                # Surface provider error if present
                if "error" in data:
                    raise RuntimeError(data["error"].get("message", str(data["error"])))
                r.raise_for_status()
                raise RuntimeError(str(data))
            cur = cur[part]
    return cur

def _groq_call(api_key, question, context):
    # Groq: OpenAI-compatible endpoint. Common errors: leading/trailing whitespace,
    # using a placeholder key, or selecting a model not enabled for the account.
    api_key = (api_key or "").strip()
    if not api_key or api_key.lower().startswith("sk-xxxx"):
        raise RuntimeError("Groq API key missing or placeholder.")
    # Common mistake: user pastes a GitHub PAT (ghp_) instead of a Groq key (gsk_)
    if api_key.startswith("ghp_"):
        raise RuntimeError("Detected a GitHub Personal Access Token (ghp_...). Please use a Groq API key (starts with gsk_).")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Provide a default model; allow easy switch later.
    model = "llama-3.1-8b-instant"
    user_msg = (
        "CONTEXT:\n" + context +
        "\n\nINSTRUCTIONS:\n" + question +
        "\n\nRULES:\n- Answer ONLY from CONTEXT.\n"
        "- If unsure, say: I don't know based on the provided context.\n"
        "- If given a word-count instruction, match it exactly."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.2,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    try:
        return _raise_for_bad_response(r, "choices.0.message.content")
    except RuntimeError as e:
        # Enrich error for common 401 cases
        if r.status_code in (401, 403):
            raise RuntimeError(f"Groq auth failed ({r.status_code}): {e}")
        raise

def _openai_call(api_key, question, context):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    user_msg = (
        "CONTEXT:\n" + context +
        "\n\nINSTRUCTIONS:\n" + question +
        "\n\nRULES:\n- Answer ONLY from CONTEXT.\n"
        "- If unsure, say: I don't know based on the provided context.\n"
        "- If given a word-count instruction, match it exactly."
    )
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.2,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    return _raise_for_bad_response(r, "choices.0.message.content")

def _gemini_call(api_key, question, context):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    user_msg = (
    f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context}\n\nINSTRUCTIONS:\n{question}\n\nRULES:\n"
        "- Answer ONLY from CONTEXT.\n"
        "- If unsure, say: I don't know based on the provided context.\n"
        "- If given a word-count instruction, match it exactly."
    )
    payload = {"contents": [{"parts": [{"text": user_msg}]}]}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    return _raise_for_bad_response(r, "candidates.0.content.parts.0.text")

def _claude_call(api_key, question, context):
    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    user_msg = (
        "CONTEXT:\n" + context +
        "\n\nINSTRUCTIONS:\n" + question +
        "\n\nRULES:\n- Answer ONLY from CONTEXT.\n"
        "- If unsure, say: I don't know based on the provided context.\n"
        "- If given a word-count instruction, match it exactly."
    )
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 500,
    "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_msg}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    return _raise_for_bad_response(r, "content.0.text")
