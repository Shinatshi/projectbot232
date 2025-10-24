from deep_translator import GoogleTranslator, MyMemoryTranslator
import textwrap

def translate_to_rus(text: str) -> str:
    if not text.strip():
        return ""
    

    try:
        chunks = textwrap.wrap(text, width=500, break_long_words=False, replace_whitespace=False)
        translated_chunks = []
        for chunk in chunks:
            translated = GoogleTranslator(source="auto", target="ru").translate(chunk)
            translated_chunks.append(translated)
        return " ".join(translated_chunks)
    except Exception:
        try:
            return MyMemoryTranslator(source="en-GB", target="ru-RU").translate(text)
        except Exception as e:
            return f"[Ошибка перевода: {type(e).__name__} — {e}]"