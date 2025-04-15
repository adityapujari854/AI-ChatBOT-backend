# app/utils/translate.py

from google.cloud import translate_v2 as translate
import os
import re

# Initialize the translation client
translate_client = translate.Client()


# OPTIONAL: To remove emojis from translation (use if needed)
def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)


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

        # Force UTF-8 decoding if necessary
        if isinstance(translated, bytes):
            translated = translated.decode("utf-8")

        # OPTIONAL: Uncomment below to remove emojis from translation
        # translated = remove_emojis(translated)

        return translated
    
    except Exception as e:
        print(f"[Translation Error]: {e}")
        return text  # fallback to original if translation fails
