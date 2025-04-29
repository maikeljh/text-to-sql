import os

ENUM = {
    "gemini": os.getenv("API_KEY_GEMINI"),
    "openai": os.getenv("API_KEY_OPENAI"),
    "deepseek": os.getenv("API_KEY_DEEPSEEK"),
    "database": {
        "sakila": {
            "DB_SOURCE_HOST": os.getenv("DB_SAKILA_HOST"),
            "DB_SOURCE_DATABASE": os.getenv("DB_SAKILA_DATABASE"),
            "DB_SOURCE_USER": os.getenv("DB_SAKILA_USER"),
            "DB_SOURCE_PASSWORD": os.getenv("DB_SAKILA_PASSWORD"),
            "DB_SOURCE_PORT": os.getenv("DB_SAKILA_PORT"),
        },
        "northwind": {
            "DB_SOURCE_HOST": os.getenv("DB_NORTHWIND_HOST"),
            "DB_SOURCE_DATABASE": os.getenv("DB_NORTHWIND_DATABASE"),
            "DB_SOURCE_USER": os.getenv("DB_NORTHWIND_USER"),
            "DB_SOURCE_PASSWORD": os.getenv("DB_NORTHWIND_PASSWORD"),
            "DB_SOURCE_PORT": os.getenv("DB_NORTHWIND_PORT"),
        },
        "academic": {
            "DB_SOURCE_HOST": os.getenv("DB_ACADEMIC_HOST"),
            "DB_SOURCE_DATABASE": os.getenv("DB_ACADEMIC_DATABASE"),
            "DB_SOURCE_USER": os.getenv("DB_ACADEMIC_USER"),
            "DB_SOURCE_PASSWORD": os.getenv("DB_ACADEMIC_PASSWORD"),
            "DB_SOURCE_PORT": os.getenv("DB_ACADEMIC_PORT"),
        },
        "soccer": {
            "DB_SOURCE_HOST": os.getenv("DB_SOCCER_HOST"),
            "DB_SOURCE_DATABASE": os.getenv("DB_SOCCER_DATABASE"),
            "DB_SOURCE_USER": os.getenv("DB_SOCCER_USER"),
            "DB_SOURCE_PASSWORD": os.getenv("DB_SOCCER_PASSWORD"),
            "DB_SOURCE_PORT": os.getenv("DB_SOCCER_PORT"),
        },
        "tpc-ds": {
            "DB_SOURCE_HOST": os.getenv("DB_TPCDS_HOST"),
            "DB_SOURCE_DATABASE": os.getenv("DB_TPCDS_DATABASE"),
            "DB_SOURCE_USER": os.getenv("DB_TPCDS_USER"),
            "DB_SOURCE_PASSWORD": os.getenv("DB_TPCDS_PASSWORD"),
            "DB_SOURCE_PORT": os.getenv("DB_TPCDS_PORT"),
        },
        "adventureworks": {
            "DB_SOURCE_HOST": os.getenv("DB_ADVENTUREWORKS_HOST"),
            "DB_SOURCE_DATABASE": os.getenv("DB_ADVENTUREWORKS_DATABASE"),
            "DB_SOURCE_USER": os.getenv("DB_ADVENTUREWORKS_USER"),
            "DB_SOURCE_PASSWORD": os.getenv("DB_ADVENTUREWORKS_PASSWORD"),
            "DB_SOURCE_PORT": os.getenv("DB_ADVENTUREWORKS_PORT"),
        },
    },
}
