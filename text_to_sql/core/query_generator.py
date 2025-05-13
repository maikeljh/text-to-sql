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
            config=config, system_prompt_path="files/prompt/query_generator_system_prompt.txt"
        )
        self.system_prompt_baseline = self._load_system_prompt(
            system_prompt_path="files/prompt/query_generator_system_prompt_baseline.txt"
        )
        self.system_prompt_multistage = self._load_system_prompt(
            system_prompt_path="files/prompt/query_generator_system_prompt_multistage.txt"
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

    def generate_baseline(self, user_prompt: str, schema: Dict[str, Any]) -> str:
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

    def fix_query(
        self,
        user_prompt: str,
        schema: Dict[str, Any],
        sql_query: str,
        error_message: str,
    ) -> str:
        """
        Fixes a previously generated SQL query based on the provided error message.

        :param sql_query: The original SQL query.
        :param error_message: The error message received during query execution.
        :return: A corrected SQL query.
        """
        if not sql_query or not isinstance(sql_query, str):
            raise ValueError("SQL query must be a non-empty string.")

        if not error_message or not isinstance(error_message, str):
            raise ValueError("Error message must be a non-empty string.")

        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        if not schema or not isinstance(schema, dict):
            raise ValueError("Schema must be a non-empty dictionary.")

        schema_json = json.dumps(schema, indent=2)
        formatted_system_prompt = self.system_prompt_multistage.format(
            sql_query=sql_query,
            error_message=error_message,
            database_schema=schema_json,
        )

        fixed_query = self.model.generate(
            system_prompt=formatted_system_prompt,
            user_prompt=user_prompt,
        )

        return fixed_query.strip()
