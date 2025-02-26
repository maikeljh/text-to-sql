from common import LLMConfig
from .base_llm import BaseLLM

class SchemaLinker(BaseLLM):
    """
    A specialized LLM for linking schemas to user queries and generating structured representations.
    """

    def __init__(self, config: LLMConfig):
        """
        Initializes the SchemaLinker model.

        :param config: LLMConfig object containing model type, API key, and other settings.
        """
        super().__init__(
            config=config, system_prompt_path="files/schema_linker_system_prompt.txt"
        )

    def generate(self, user_prompt: str, schema: str) -> str:
        """
        Links user query with the provided schema and generates a structured representation.

        :param user_prompt: The natural language query.
        :param schema: The schema details to align with the query.
        :return: The structured schema-linked query.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")
        
        if not schema or not isinstance(schema, str):
            raise ValueError("Schema cannot be empty and must be a string.")

        schema_linked_query = self.model.generate(
            system_prompt=self.system_prompt, user_prompt=user_prompt, schema=schema
        )
        return schema_linked_query