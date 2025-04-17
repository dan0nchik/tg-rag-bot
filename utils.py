import re


def clean_text(text: str) -> str:
    # Убираем лишние пробелы и Markdown
    return text.strip()


def chunk_messages(docs: list, max_tokens: int = 512) -> list:
    chunks = []
    for doc in docs:
        text = doc["text"]
        if len(text) <= max_tokens:
            chunks.append(doc)
        else:
            parts = re.split(r"(?<=[.!?]) +", text)
            current = ""
            for part in parts:
                if len(current) + len(part) > max_tokens:
                    chunks.append({**doc, "text": current})
                    current = part
                else:
                    current += " " + part
            if current:
                chunks.append({**doc, "text": current})
    return chunks
