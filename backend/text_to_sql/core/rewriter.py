from text_to_sql.common import LLMConfig
from .base_llm import BaseLLM


class RewriterPrompt(BaseLLM):
    """
    A specialized LLM for rewriting user prompts into structured queries.
    """

    def __init__(self, config: LLMConfig):
        """
        Initializes the RewriterPrompt model.

        :param config: LLMConfig object containing model type, API key, and other settings.
        """
        super().__init__(
            config=config, system_prompt_path="files/prompt/rewriter_prompt_system_prompt.txt"
        )

    def generate(self, user_prompt: str) -> str:
        """
        Rewrites the user's natural language query into a structured prompt.

        :param user_prompt: The natural language query.
        :return: The rewritten query.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        rewritten_prompt = self.model.generate(
            system_prompt=self.system_prompt, user_prompt=user_prompt
        )
        print(f"Rewritten Prompt: {rewritten_prompt}")
        return rewritten_prompt
