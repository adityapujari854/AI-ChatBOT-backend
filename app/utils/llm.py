import html
import re
import os
import requests
from dotenv import load_dotenv
import markdown2  # Added to convert markdown to HTML
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
    """
    Detects the language of the input text. Returns 'en' for English or the detected language code.
    For very simple English phrases (e.g., "hello"), always return 'en'.
    """
    simple_english_greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']

    # Check for very simple English phrases (e.g., "hello", "hi")
    if any(greeting in text.lower() for greeting in simple_english_greetings):
        return "en"

    try:
        detected_language = detect(text)
        if detected_language == "en":
            return "en"  # Explicitly return 'en' for English
        return detected_language
    except LangDetectException:
        return "en"  # Fallback to English if detection fails or is ambiguous


def get_system_prompt(language: str = "en", user_prompt: str = "") -> str:
    """ Returns a language-aware system prompt to enable code-mixed output. Adds more detailed responses if the user greeting is short like 'hi', 'hello', etc. """
    simple_english_greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'] 
    user_message = user_prompt.strip().lower()
    is_greeting = any(greet in user_message for greet in simple_english_greetings)
    if language == "en":
        base_prompt = (
            "You are Nimbus, a helpful, friendly, and intelligent assistant. "
            "Please always reply in English. "
            "When listing ideas, stories, or examples, use Markdown formatting as follows:\n"
            "- Use emojis before titles where appropriate.\n"
            "- Make the entire title bold using **double asterisks**.\n"
            "- Follow each bolded title with a colon and its description.\n"
            "- For code, use triple backticks and specify the language (e.g., ```python).\n"
            "- Use bullet points or numbered lists when giving multiple points.\n"
            "Be creative and well-structured in your responses."
        )
        if is_greeting:
            base_prompt += (
                "\nIf the user greets you with a simple greeting like 'hi', 'hello', etc., "
                "respond warmly and informatively with a 3–4 sentence introduction. "
                "Let them know you're Nimbus and what you're capable of doing."
            )
        return base_prompt
    else:
        return f"You are Nimbus, a helpful assistant. Reply in {language}, and be friendly and helpful."


def remove_foreign_language(text: str, target_language: str = "en") -> str:
    """
    Attempts to remove or filter non-target-language content from the response.
    Currently removes non-ASCII characters if the detected language differs.
    Also handles fallback decoding for misencoded characters (e.g., emoji).
    """
    try:
        detected_language = detect(text)
        if detected_language != target_language:
            # Remove non-ASCII characters as a simple fallback
            text = re.sub(r'[^\x00-\x7F]+', '', text)
    except LangDetectException:
        pass  # If detection fails, keep the text as-is

    # Optional: decode improperly encoded characters like emojis
    try:
        text = text.encode("latin1").decode("utf-8")
    except Exception:
        pass

    return text


def format_llm_response(text: str, format: str = "html", language: str = "en") -> str:
    """
    Formats the LLM's response into HTML, Markdown, or raw text as requested.
    Handles bold text (**bold**), code blocks (```), and lists (* item, 1. item).
    """
    if not text:
        return "Sorry, no content received from the model."

    # Remove unintended languages/symbols
    text = remove_foreign_language(text, language)

    # Optional: fix misencoded emojis or unicode (e.g. "ðŸ˜Š" → "😊")
    try:
        text = text.encode("latin1").decode("utf-8")
    except Exception:
        pass  # fallback if decode fails

    if format == "raw":
        return text

    elif format == "markdown":
        return markdown2.markdown(text.strip(), extras=["fenced-code-blocks"])

    elif format == "html":
        # Convert markdown to full HTML with fenced code support
        return markdown2.markdown(text.strip(), extras=["fenced-code-blocks"])

    else:
        return text


def query_llm(prompt: str, model: str = "nimbus", session_id: str = None, language: str = None, format: str = "html") -> str:
    """
    Queries the LLM (either OpenRouter or Groq) and returns the formatted response.
    """
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
                print("OpenRouter raw response:", result)

                if "error" in result:
                    if result["error"].get("code") == 429:
                        print("[INFO] OpenRouter rate limit hit. Switching to Groq...")
                        if session_id:
                            session_model_map[session_id] = "groq"
                        return query_llm(prompt, model="groq", session_id=session_id, language=language, format=format)
                    return f"OpenRouter Error: {result['error'].get('message', 'Unknown error')}"

                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    content = content if content else "No response from model."
                    content = remove_foreign_language(content, language)  # Apply the language filtering
                    return format_llm_response(content, format)

                return "Sorry, I couldn't understand the response from OpenRouter."

            except Exception as e:
                print(f"[OpenRouter Error]: {e}")
                print("Falling back to Groq...")
                if session_id:
                    session_model_map[session_id] = "groq"
                return query_llm(prompt, model="groq", session_id=session_id, language=language, format=format)

        elif model == "groq":
            try:
                from groq import Groq
                client = Groq()
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "system", "content": get_system_prompt(language, prompt)},
                              {"role": "user", "content": prompt}]
                )

                content = response.choices[0].message.content
                print("Groq response:", content)
                if session_id:
                    session_model_map[session_id] = "groq"
                return format_llm_response(content, format)

            except Exception as e:
                print(f"[Groq Error]: {e}")
                return "Sorry, Our Nimbus is currently unavailable."

        else:
            import cohere
            co = cohere.Client(cohere_api_key)
            response = co.chat(model=model, message=prompt, temperature=0.5)
            print("Cohere response:", response)

            if hasattr(response, "text"):
                return format_llm_response(response.text.strip(), format)
            else:
                return "Sorry, Cohere did not return a valid response."

    except Exception as e:
        print(f"[ERROR - query_llm]: {e}")
        return "Sorry, I couldn't process your request."


async def stop_stream():
    global streaming_task
    if streaming_task:
        streaming_task.cancel()  # This will stop the current streaming task
        streaming_task = None
        print("Streaming stopped.")
    else:
        print("No streaming in progress.")


async def stream_llm_response(prompt: str, model: str = "openrouter-mistral", session_id: str = None, language: str = None):
    """
    Streams the response from the LLM in chunks.
    """
    global streaming_task  # Ensure to use the global streaming_task

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

    # Create a new task and assign it to the global variable streaming_task
    streaming_task = asyncio.create_task(_stream_llm_response_internal(url, headers, payload))

    await streaming_task


async def _stream_llm_response_internal(url, headers, payload):
    """
    Internal function to handle the actual streaming process
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_response = await resp.json()
                print("Error:", error_response)
                return

            # Streaming chunks
            async for line in resp.content:
                if line:
                    print(f"Received chunk: {line.decode('utf-8')}")
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "choices" in data:
                            for choice in data["choices"]:
                                print(choice.get("text", ""))
                    except json.JSONDecodeError as e:
                        print(f"JSON Decode error: {e}")