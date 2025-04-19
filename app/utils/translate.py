# app/utils/translate.py

import os
import re
from dotenv import load_dotenv
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

# Load environment variables
load_dotenv()

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Ensure credentials file exists
if not GOOGLE_CREDENTIALS_PATH or not os.path.exists(GOOGLE_CREDENTIALS_PATH):
    raise FileNotFoundError(
        f"Google credentials file not found at path: {GOOGLE_CREDENTIALS_PATH}"
    )

# Set up credentials
credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)
translate_client = translate.Client(credentials=credentials)

# Optional: Emoji filter
def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "[" +
        u"\U0001F600-\U0001F64F" +  # emoticons
        u"\U0001F300-\U0001F5FF" +  # symbols & pictographs
        u"\U0001F680-\U0001F6FF" +  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF" +  # flags
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# Translate text to target language
def translate_text(text: str, target_lang: str = "en") -> str:
    """
    Translates input text to target_lang.
    Returns original text if translation fails.
    """
    if not text or not text.strip():
        return ""

    try:
        result = translate_client.translate(
            text,
            target_language=target_lang,
            format_='text'
        )
        translated = result.get("translatedText", "")

        if isinstance(translated, bytes):
            translated = translated.decode("utf-8")

        # Optional: clean emojis from output
        # translated = remove_emojis(translated)

        return translated

    except Exception as e:
        print(f"[Translation Error]: {e}")
        return text  # fallback: return original if translation fails
