from common import LLMConfig
from .base_llm import BaseLLM
from typing import Dict, Any

import json


class QueryGenerator(BaseLLM):
    """
    A specialized LLM for generating SQL queries from user input.
    """

    def __init__(self, config: LLMConfig):
        """
        Initializes the QueryGenerator model.

        :param config: LLMConfig object containing model type, API key, and other settings.
        """
        super().__init__(
            config=config, system_prompt_path="files/query_generator_system_prompt.txt"
        )
        self.system_prompt_baseline = self._load_system_prompt(
            system_prompt_path="files/query_generator_system_prompt_baseline.txt"
        )
    
    def generate(
        self, user_prompt: str, schema: Dict[str, Any], example: Dict[str, Any]
    ) -> str:
        """
        Converts a natural language query into an SQL query.

        :param user_prompt: The natural language input.
        :param schema: The relevant database schema (JSON format).
        :return: The generated SQL query.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        if not schema or not isinstance(schema, dict):
            raise ValueError("Schema must be a non-empty dictionary.")

        schema_json = json.dumps(schema, indent=2)
        formatted_system_prompt = self.system_prompt.format(
            database_schema=schema_json,
            relevant_question=example["relevant_question"],
            relevant_answer=example["relevant_answer"],
            relevant_summary=example["relevant_summary"],
        )
        sql_query = self.model.generate(
            system_prompt=formatted_system_prompt, user_prompt=user_prompt
        )

        return sql_query.strip()
    
    def generate_baseline(
        self, user_prompt: str, schema: Dict[str, Any]
    ) -> str:
        """
        Converts a natural language query into an SQL query.

        :param user_prompt: The natural language input.
        :param schema: The relevant database schema (JSON format).
        :return: The generated SQL query.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        if not schema or not isinstance(schema, dict):
            raise ValueError("Schema must be a non-empty dictionary.")

        schema_json = json.dumps(schema, indent=2)
        formatted_system_prompt = self.system_prompt_baseline.format(
            database_schema=schema_json,
        )
        sql_query = self.model.generate(
            system_prompt=formatted_system_prompt, user_prompt=user_prompt
        )

        return sql_query.strip()

    def generate_v1(
        self, user_prompt: str, schema: Dict[str, Any], example: Dict[str, Any]
    ) -> str:
        """
        Converts a natural language query into an SQL query.

        :param user_prompt: The natural language input.
        :param schema: The relevant database schema (JSON format).
        :return: The generated SQL query.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        if not schema or not isinstance(schema, dict):
            raise ValueError("Schema must be a non-empty dictionary.")

        schema_json = json.dumps(schema, indent=2)
        formatted_system_prompt = self.system_prompt.format(
            database_schema=schema_json,
            relevant_question=example["relevant_question"],
            relevant_answer=example["relevant_answer"],
            relevant_summary=example["relevant_summary"],
        )
        sql_query = self.model.generate(
            system_prompt=formatted_system_prompt, user_prompt=user_prompt
        )

        return sql_query.strip()
