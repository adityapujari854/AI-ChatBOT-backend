import html
import re
import cohere
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Cohere client
cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.Client(cohere_api_key)

def query_llm(prompt: str, model: str = "command-r-plus") -> str:
    """
    Sends a prompt to the LLM and returns its response.
    """
    try:
        response = co.chat(
            model=model,
            message=prompt,
            temperature=0.5,
        )
        raw_output = response.text.strip()
        return format_llm_response(raw_output)  # Optional: return plain text if formatting not needed
    except Exception as e:
        print(f"[ERROR - query_llm]: {e}")
        return "Sorry, I couldn't process your request."

def format_llm_response(text: str) -> str:
    """
    Converts raw LLM response to HTML.
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
