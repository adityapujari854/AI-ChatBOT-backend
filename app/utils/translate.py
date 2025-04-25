import os
import re
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

# Load environment variables
load_dotenv()

# Google credentials path
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GOOGLE_CREDENTIALS_PATH or not os.path.exists(GOOGLE_CREDENTIALS_PATH):
    raise FileNotFoundError(
        f"Google credentials file not found at: {GOOGLE_CREDENTIALS_PATH}"
    )

# Load credentials and initialize client
credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)
translate_client = translate.Client(credentials=credentials)

def remove_emojis(text: str) -> str:
    """
    Removes common emojis from the text.
    """
    emoji_pattern = re.compile(
        "[" 
        u"\U0001F600-\U0001F64F"  # Emoticons
        u"\U0001F300-\U0001F5FF"  # Symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # Transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # Flags
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def detect_language(text: str) -> str:
    """
    Detects the language of the input text. Returns 'en' for English or the detected language code.
    """
    try:
        detected_language = detect(text)
        if detected_language == "en":
            return "en"  # Explicitly return 'en' for English
        return detected_language
    except LangDetectException:
        return "en"  # Fallback to English if detection fails or is ambiguous

def translate_text(text: str, target_lang: str = "en") -> str:
    """
    Translates input text into the target language using Google Translate API.
    Only performs translation if necessary (if input is not already in target language).
    Skips translation if the input text is already in the target language.
    """
    if not text:
        return ""

    try:
        detected_language = detect_language(text)
        
        # Skip translation if already in the target language
        if detected_language == target_lang or (detected_language == "en" and target_lang == "en"):
            return text

        # Proceed with translation if not in the target language
        result = translate_client.translate(
            text,
            target_language=target_lang,
            format_='text'
        )

        translated = result.get("translatedText", "")
        if isinstance(translated, bytes):
            translated = translated.decode("utf-8")

        # Uncomment if you want to clean emojis from translated text
        # translated = remove_emojis(translated)

        return translated

    except Exception as e:
        print(f"[Translation Error]: {e}")
        return text  # Return original text if translation fails
