from text_to_sql.common import LLMConfig
from .base_llm import BaseLLM
from typing import Any


class Summarization(BaseLLM):
    """
    A specialized LLM for summarizing SQL queries.
    """

    def __init__(self, config: LLMConfig):
        """
        Initializes the Summarization model.

        :param config: LLMConfig object containing model type, API key, and other settings.
        """
        super().__init__(
            config=config, system_prompt_path="files/summarization_system_prompt.txt"
        )

    def generate(self, sql: str) -> str:
        """
        Summarizes an SQL query.

        :param sql: The SQL query to summarize.
        :return: The summarized SQL query as a string.
        """
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError(
                "SQL query cannot be empty and must be a non-empty string."
            )

        summary = self.model.generate(system_prompt=self.system_prompt, user_prompt=sql)

        return summary.strip()
