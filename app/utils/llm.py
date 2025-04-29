import html
import re
import os
import requests
from dotenv import load_dotenv
import markdown2
import asyncio
import json
import aiohttp
from langdetect import detect, LangDetectException

# Load environment variables
load_dotenv()

cohere_api_key = os.getenv("COHERE_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

# Session-specific model cache (in-memory)
session_model_map = {}  # key: session_id, value: model name

# Streaming task global variable
streaming_task = None

def detect_language(text: str) -> str:
    simple_english_greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(greeting in text.lower() for greeting in simple_english_greetings):
        return "en"
    try:
        return detect(text)
    except LangDetectException:
        return "en"

def get_system_prompt(language: str = "en", user_prompt: str = "") -> str:
    simple_english_greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    creator_questions = [
        "who created you", "who is your creator", "who made you", "your dad", "who is your dad",
        "your father", "who developed you", "who are all that created you", "who are all who created you"
    ]

    user_message = user_prompt.strip().lower()
    is_greeting = any(greet in user_message for greet in simple_english_greetings)
    is_creator_question = any(q in user_message for q in creator_questions)

    if language == "en":
        base_prompt = (
            "You are Nimbus, a smart, creative, and friendly AI assistant.\n"
            "Do not bring up Aditya Pujari unless asked directly.\n\n"
            "When replying:\n"
            "- Always be kind, professional, and natural.\n"
            "- Use Markdown formatting where suitable (bold, lists, code blocks).\n"
            "- Keep greetings short (2–3 sentences) if user says 'hi', 'hello', etc.\n"
            "- Never mention companies like Mistral AI, OpenRouter.\n"
            "- Never mention any other creator besides Aditya Pujari.\n"
            "- Avoid overclaiming features like reminders, calendar integration, etc.\n"
            "- If user asks about your creator, always say: 'I was created by Aditya Pujari,\n"
            "  a Computer Engineering student at G.H. Raisoni College of Engineering and Management, Pune.'\n"
        )

        if is_greeting:
            base_prompt += "\n\nUser greeted you. Respond warmly in 2–3 sentences. Introduce yourself briefly."

        if is_creator_question:
            base_prompt += (
                "\n\nUser asked about your creator.\n"
                "Reply: 'I was created by Aditya Pujari, a Computer Engineering student from\n"
                "G.H. Raisoni College of Engineering and Management, Pune. He built me as part of his passion\n"
                "for AI and programming.' Do not call him an AI researcher or use exaggerated praise."
            )

        return base_prompt
    else:
        return f"You are Nimbus, a helpful assistant. Reply in {language}."

def remove_foreign_language(text: str, target_language: str = "en") -> str:
    try:
        detected_language = detect(text)
        if detected_language != target_language:
            text = re.sub(r'[^\x00-\x7F]+', '', text)
    except LangDetectException:
        pass
    try:
        text = text.encode("latin1").decode("utf-8")
    except Exception:
        pass
    return text

def format_llm_response(text: str, format: str = "html", language: str = "en") -> str:
    if not text:
        return "Sorry, no content received from the model."
    text = remove_foreign_language(text, language)
    try:
        text = text.encode("latin1").decode("utf-8")
    except Exception:
        pass

    if format in ["markdown", "html"]:
        return markdown2.markdown(text.strip(), extras=["fenced-code-blocks"])
    return text

def query_llm(prompt: str, model: str = "nimbus", session_id: str = None, language: str = None, format: str = "html") -> str:
    if not language:
        language = detect_language(prompt)

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
                        {"role": "system", "content": get_system_prompt(language, prompt)},
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
                if "error" in result:
                    if result["error"].get("code") == 429:
                        if session_id:
                            session_model_map[session_id] = "groq"
                        return query_llm(prompt, model="groq", session_id=session_id, language=language, format=format)
                    return f"OpenRouter Error: {result['error'].get('message', 'Unknown error')}"
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    content = content if content else "No response from model."
                    return format_llm_response(content, format, language)
                return "Sorry, I couldn't understand the response from OpenRouter."
            except Exception as e:
                if session_id:
                    session_model_map[session_id] = "groq"
                return query_llm(prompt, model="groq", session_id=session_id, language=language, format=format)

        elif model == "groq":
            try:
                from groq import Groq
                client = Groq()
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": get_system_prompt(language, prompt)},
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.choices[0].message.content
                if session_id:
                    session_model_map[session_id] = "groq"
                return format_llm_response(content, format, language)
            except Exception as e:
                return "Sorry, Nimbus is currently unavailable."

        else:
            import cohere
            co = cohere.Client(cohere_api_key)
            response = co.chat(model=model, message=prompt, temperature=0.5)
            if hasattr(response, "text"):
                return format_llm_response(response.text.strip(), format, language)
            else:
                return "Sorry, Cohere did not return a valid response."

    except Exception as e:
        return "Sorry, I couldn't process your request."

async def stop_stream():
    global streaming_task
    if streaming_task:
        streaming_task.cancel()
        streaming_task = None

async def stream_llm_response(prompt: str, model: str = "openrouter-mistral", session_id: str = None, language: str = None):
    global streaming_task
    if not language:
        language = detect_language(prompt)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "stream": True,
        "messages": [
            {"role": "system", "content": get_system_prompt(language, prompt)},
            {"role": "user", "content": prompt}
        ]
    }
    streaming_task = asyncio.create_task(_stream_llm_response_internal(url, headers, payload))
    await streaming_task

async def _stream_llm_response_internal(url, headers, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_response = await resp.json()
                print("Error:", error_response)
                return
            async for line in resp.content:
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "choices" in data:
                            for choice in data["choices"]:
                                print(choice.get("text", ""))
                    except json.JSONDecodeError as e:
                        print(f"JSON Decode error: {e}")
