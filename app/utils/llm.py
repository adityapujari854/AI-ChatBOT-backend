import html
import re
import os
import requests
from dotenv import load_dotenv
import aiohttp
import json

# Load environment variables
load_dotenv()

cohere_api_key = os.getenv("COHERE_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

# Session-specific model cache (in-memory)
session_model_map = {}  # key: session_id, value: model name

def get_system_prompt(language: str = "en") -> str:
    """
    Returns a language-aware system prompt to enable code-mixed output.
    """
    if language == "en":
        return (
            "You are Nimbus, a helpful, friendly, and intelligent assistant. "
            "Reply completely in English."
        )
    else:
        return (
            f"You are Nimbus, a helpful, friendly, and intelligent assistant. "
            f"Reply primarily in {language} but feel free to include some English phrases for clarity. "
            f"Be natural and conversational."
        )

def query_llm(prompt: str, model: str = "nimbus", session_id: str = None, language: str = "en") -> str:
    """
    Sends a prompt to the selected LLM provider.
    Tries OpenRouter → falls back to Groq.
    """

    if session_id and session_id in session_model_map:
        model = session_model_map[session_id]

    try:
        if model in ["openrouter-mistral", "nimbus"]:
            try:
                headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [
                        {
                            "role": "system",
                            "content": get_system_prompt(language)
                        },
                        {"role": "user", "content": prompt}
                    ]
                }

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()

                print("OpenRouter raw response:", result)

                if "error" in result:
                    if result["error"].get("code") == 429:
                        print("[INFO] OpenRouter rate limit hit. Switching to Groq...")
                        if session_id:
                            session_model_map[session_id] = "groq"
                        return query_llm(prompt, model="groq", session_id=session_id, language=language)
                    return f"OpenRouter Error: {result['error'].get('message', 'Unknown error')}"

                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    if session_id:
                        session_model_map[session_id] = "openrouter-mistral"
                    return format_llm_response(content)

                return "Sorry, I couldn't understand the response from OpenRouter."

            except Exception as e:
                print(f"[OpenRouter Error]: {e}")
                print("Falling back to Groq...")
                if session_id:
                    session_model_map[session_id] = "groq"
                return query_llm(prompt, model="groq", session_id=session_id, language=language)

        elif model == "groq":
            try:
                from groq import Groq
                client = Groq()
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {
                            "role": "system",
                            "content": get_system_prompt(language)
                        },
                        {"role": "user", "content": prompt}
                    ]
                )

                content = response.choices[0].message.content
                print("Groq response:", content)
                if session_id:
                    session_model_map[session_id] = "groq"
                return format_llm_response(content)

            except Exception as e:
                print(f"[Groq Error]: {e}")
                return "Sorry, Our Nimbus is currently unavailable."

        else:
            import cohere
            co = cohere.Client(cohere_api_key)
            response = co.chat(model=model, message=prompt, temperature=0.5)
            print("Cohere response:", response)

            if hasattr(response, "text"):
                return format_llm_response(response.text.strip())
            else:
                return "Sorry, Cohere did not return a valid response."

    except Exception as e:
        print(f"[ERROR - query_llm]: {e}")
        return "Sorry, I couldn't process your request."

def format_llm_response(text: str) -> str:
    """
    Converts raw LLM response to formatted HTML.
    """
    lines = text.strip().splitlines()
    html_parts = []

    in_list = False
    list_type = None
    buffer = []

    def flush_paragraph(paragraph_lines):
        if paragraph_lines:
            escaped = html.escape("\n".join(paragraph_lines))
            html_parts.append(f"<p>{escaped}</p>")

    def flush_list(buffer, list_type):
        if buffer:
            tag = 'ol' if list_type == 'ordered' else 'ul'
            items = ''.join(f"<li>{html.escape(item.strip())}</li>" for item in buffer)
            html_parts.append(f"<{tag}>{items}</{tag}>")

    for line in lines:
        stripped = line.strip()
        ordered_match = re.match(r"^\d+\.\s+(.*)", stripped)
        bullet_match = re.match(r"^[-*•]\s+(.*)", stripped)

        if ordered_match:
            if not in_list or list_type != 'ordered':
                flush_paragraph(buffer)
                buffer = []
                in_list = True
                list_type = 'ordered'
            buffer.append(ordered_match.group(1))

        elif bullet_match:
            if not in_list or list_type != 'unordered':
                flush_paragraph(buffer)
                buffer = []
                in_list = True
                list_type = 'unordered'
            buffer.append(bullet_match.group(1))

        elif stripped == "":
            if in_list:
                flush_list(buffer, list_type)
                buffer = []
                in_list = False
                list_type = None
            else:
                flush_paragraph(buffer)
                buffer = []
        else:
            if in_list:
                flush_list(buffer, list_type)
                buffer = []
                in_list = False
                list_type = None
            buffer.append(stripped)

    if in_list:
        flush_list(buffer, list_type)
    else:
        flush_paragraph(buffer)

    return "\n".join(html_parts)

async def stream_llm_response(prompt: str, model: str = "openrouter-mistral", session_id: str = None, language: str = "en"):
    """
    Streams chunks from OpenRouter with dynamic language-aware system prompt.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "stream": True,
        "messages": [
            {
                "role": "system",
                "content": get_system_prompt(language)
            },
            {"role": "user", "content": prompt}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print("OpenRouter Error:", error_text)
                yield "Sorry, something went wrong.\n"
                return
            async for line in resp.content:
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        chunk = decoded[6:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta and delta.strip():
                                yield delta
                        except Exception as e:
                            print("Streaming parse error:", e)
                            continue
