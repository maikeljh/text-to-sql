import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from common import Config, LLMConfig
from core import RewriterPrompt, QueryGenerator


class TextToSQL:
    def __init__(self, config: Config):
        self.config = config
        self._load_modules()

    def _load_modules(self):
        self.rewriter = RewriterPrompt(config=self.config.rewriter_config)
        self.query_generator = QueryGenerator(config=self.config.query_generator_config)

    def load_data_rewriter(self, data):
        return

    def load_data_schema_linker(self, data):
        return

    def generate(self, user_prompt):
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        print(f"Rewritten Prompt: {rewritten_prompt}")
        query = self.query_generator.generate(user_prompt=rewritten_prompt)
        return query
