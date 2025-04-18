import html
import re
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

cohere_api_key = os.getenv("COHERE_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

# Session-specific model cache (in-memory)
session_model_map = {}  # key: session_id, value: model name

def query_llm(prompt: str, model: str = "nimbus", session_id: str = None) -> str:
    """
    Sends a prompt to the selected LLM provider.
    Tries OpenRouter → falls back to Groq.
    Keeps the model fixed for the session until changed manually or fails.
    """

    # Always use cached model if set for session
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
                            "content": (
                                "You are Nimbus, a helpful, friendly, and intelligent assistant. "
                                "If someone asks your name, you must reply with: "
                                "'Hello! It's nice to meet you. I don't have a personal name, but you can call me Nimbus. "
                                "How can I assist you today?' Respond helpfully and kindly."
                            )
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
                        return query_llm(prompt, model="groq", session_id=session_id)
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
                return query_llm(prompt, model="groq", session_id=session_id)

        elif model == "groq":
            try:
                from groq import Groq
                client = Groq()
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are Nimbus, a helpful, friendly, and intelligent assistant. "
                                "If someone asks your name, you must reply with: "
                                "'Hello! It's nice to meet you. I don't have a personal name, but you can call me Nimbus. "
                                "How can I assist you today?' Respond helpfully and kindly."
                            )
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
            # Optional Cohere fallback
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
    Supports paragraphs, bullet points, and numbered lists.
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
