import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from common import Config, LLMConfig, SLConfig
from core import RewriterPrompt, QueryGenerator, SchemaLinker


class TextToSQL:
    def __init__(self, config: Config):
        self.config = config
        self._load_modules()

    def _load_modules(self):
        self.rewriter = RewriterPrompt(config=self.config.rewriter_config)
        self.query_generator = QueryGenerator(config=self.config.query_generator_config)
        self.schema_linker = SchemaLinker(config=self.config.schema_linker_config)

    def generate(self, user_prompt):
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        filtered_schema = self.schema_linker.generate(user_prompt=user_prompt)
        query = self.query_generator.generate(
            user_prompt=rewritten_prompt, schema=filtered_schema
        )
        return query
