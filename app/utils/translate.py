# app/utils/translate.py

import os
import re
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the credentials path from environment variable
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Ensure path is valid
if not GOOGLE_CREDENTIALS_PATH or not os.path.exists(GOOGLE_CREDENTIALS_PATH):
    raise FileNotFoundError(
        f"Google credentials file not found at path: {GOOGLE_CREDENTIALS_PATH}"
    )

# Load credentials and initialize translation client
credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)
translate_client = translate.Client(credentials=credentials)


# Optional: Remove emojis from translated text
def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)


# Main translation function
def translate_text(text: str, target_lang: str = "en") -> str:
    if not text:
        return ""

    try:
        result = translate_client.translate(
            text,
            target_language=target_lang,
            format_='text'
        )
        translated = result["translatedText"]

        if isinstance(translated, bytes):
            translated = translated.decode("utf-8")

        # Optionally remove emojis
        # translated = remove_emojis(translated)

        return translated

    except Exception as e:
        print(f"[Translation Error]: {e}")
        return text  # fallback to original text if translation fails
