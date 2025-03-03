from text_to_sql import (
    TextToSQL,
    Config,
    LLMConfig,
    SLConfig,
    ContextConfig,
    QueryConfig,
)
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
    retrieve_context_config=ContextConfig(data_path="./dataset/dataset_sakila.csv"),
    query_executor_config=QueryConfig(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_DATABASE"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
    ),
)
text_to_sql_model = TextToSQL(config=config)

user_prompt = input("Query: ")
result = text_to_sql_model.generate(user_prompt=user_prompt)
print(f"SQL Query: {result}")
rows = text_to_sql_model.evaluate(query=result)
