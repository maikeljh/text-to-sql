from common import LLMConfig
from .base_llm import BaseLLM


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
            config=config, system_prompt_path="files/query_generator_prompt.txt"
        )

    def generate(self, user_prompt: str) -> str:
        """
        Converts a natural language query into an SQL query.

        :param user_prompt: The natural language input.
        :return: The generated SQL query.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        sql_query = self.model.generate(
            system_prompt=self.system_prompt, user_prompt=user_prompt
        )
        return sql_query
