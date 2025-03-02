from text_to_sql import TextToSQL, Config, LLMConfig, SLConfig
from dotenv import load_dotenv

import os

load_dotenv()


config = Config(
    rewriter_config=LLMConfig(
        type="api",
        model="gemini-1.5-flash",
        provider="gemini",
        api_key=os.getenv("API_KEY"),
    ),
    query_generator_config=LLMConfig(
        type="api",
        model="gemini-1.5-flash",
        provider="gemini",
        api_key=os.getenv("API_KEY"),
    ),
    schema_linker_config=SLConfig(
        type="api",
        model="gemini-1.5-flash",
        provider="gemini",
        api_key=os.getenv("API_KEY"),
        schema_path="./metadata/sakila.json",
    ),
)
text_to_sql_model = TextToSQL(config=config)

user_prompt = input("Query: ")
result = text_to_sql_model.generate(user_prompt=user_prompt)
print(f"SQL Query: {result}")
