import os

ENUM = {
    "gemini": os.getenv("API_KEY_GEMINI"),
    "openai": os.getenv("API_KEY_OPENAI"),
    "deepsek": os.getenv("API_KEY_DEEPSEEK"),
    "DB_SOURCE_HOST": os.getenv("DB_SOURCE_HOST"),
    "DB_SOURCE_DATABASE": os.getenv("DB_SOURCE_DATABASE"),
    "DB_SOURCE_USER": os.getenv("DB_SOURCE_USER"),
    "DB_SOURCE_PASSWORD": os.getenv("DB_SOURCE_PASSWORD"),
    "DB_SOURCE_PORT": os.getenv("DB_SOURCE_PORT"),
}