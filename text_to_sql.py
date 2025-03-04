import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from common import Config, LLMConfig, SLConfig, ContextConfig, QueryConfig
from core import (
    RewriterPrompt,
    QueryGenerator,
    SchemaLinker,
    RetrieveContext,
    QueryExecutor,
    QueryEvaluator,
)


class TextToSQL:
    def __init__(self, config: Config):
        self.config = config
        self._load_modules()

    def _load_modules(self):
        self.rewriter = RewriterPrompt(config=self.config.rewriter_config)
        self.query_generator = QueryGenerator(config=self.config.query_generator_config)
        self.schema_linker = SchemaLinker(config=self.config.schema_linker_config)
        self.retrieve_context = RetrieveContext(
            config=self.config.retrieve_context_config
        )
        self.query_executor = QueryExecutor(config=self.config.query_executor_config)
        self.evaluator = QueryEvaluator()
    
    def generate_baseline(self, user_prompt):
        filtered_schema = self.schema_linker.generate(user_prompt=user_prompt)
        query = self.query_generator.generate_baseline(
            user_prompt=user_prompt,
            schema=filtered_schema,
        )
        return query

    def generate_v1(self, user_prompt):
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        filtered_schema = self.schema_linker.generate(user_prompt=user_prompt)
        relevant_example = self.retrieve_context.generate(user_prompt=user_prompt)
        query = self.query_generator.generate_v1(
            user_prompt=rewritten_prompt,
            schema=filtered_schema,
            example=relevant_example,
        )
        return query

    def evaluate(self, query, true_query):
        try:
            predicted_result = self.query_executor.execute_query(query)
            expected_result = self.query_executor.execute_query(true_query)
            acc = self.evaluator.calculate_accuracy(
                expected=expected_result, actual=predicted_result
            )
            return acc
        except:
            return 0.0
