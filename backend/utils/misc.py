def generate_title(text: str, max_words: int = 5) -> str:
    return " ".join(text.strip().split()[:max_words])
