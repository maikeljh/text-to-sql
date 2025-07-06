import os
import re

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
    """Main class for generating and evaluating SQL queries from natural language prompts."""

    def __init__(self, config: Config):
        """Initialize all core modules with given configuration."""
        self.config = config
        self._load_modules()

    def _load_modules(self):
        """Load core modules for text-to-SQL pipeline."""
        self.rewriter = RewriterPrompt(config=self.config.rewriter_config)
        self.query_generator = QueryGenerator(config=self.config.query_generator_config)
        self.schema_linker = SchemaLinker(config=self.config.schema_linker_config)
        self.retrieve_context = RetrieveContext(config=self.config.retrieve_context_config)
        self.query_executor = QueryExecutor(config=self.config.query_executor_config)
        self.evaluator = QueryEvaluator()

    def generate_baseline(self, user_prompt: str) -> str:
        """Generate baseline SQL query without context, rewriter, or error handling."""
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        return self.query_generator.generate_baseline(user_prompt=user_prompt, schema=schema)

    def generate_v1(self, user_prompt: str) -> str:
        """Generate SQL using rewritten prompt and retrieved context, no error handling."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        relevant_example = self.retrieve_context.generate(user_prompt=rewritten_prompt)
        return self.query_generator.generate_v1(user_prompt=rewritten_prompt, schema=schema, example=relevant_example)

    def generate_v2(self, user_prompt: str) -> str:
        """Same as V1, but adds multistage error handling."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        relevant_example = self.retrieve_context.generate(user_prompt=rewritten_prompt)
        attempts_left = self.config.max_retry_attempt
        query = self.query_generator.generate_v1(user_prompt=rewritten_prompt, schema=schema, example=relevant_example)

        while attempts_left > 0:
            try:
                self.query_executor.execute_query(query)
                break
            except Exception as e:
                attempts_left -= 1
                query = self.query_generator.fix_query(
                    user_prompt=rewritten_prompt,
                    sql_query=query,
                    error_message=str(e),
                    schema=schema,
                )
        return query

    def generate_v3(self, user_prompt: str) -> str:
        """Same as V2, but adds schema filtering."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        schema = self.schema_linker.generate(user_prompt=user_prompt, filter=True)
        relevant_example = self.retrieve_context.generate(user_prompt=rewritten_prompt)
        attempts_left = self.config.max_retry_attempt
        query = self.query_generator.generate_v1(user_prompt=rewritten_prompt, schema=schema, example=relevant_example)

        while attempts_left > 0:
            try:
                self.query_executor.execute_query(query)
                break
            except Exception as e:
                attempts_left -= 1
                query = self.query_generator.fix_query(
                    user_prompt=rewritten_prompt,
                    sql_query=query,
                    error_message=str(e),
                    schema=schema,
                )
        return query

    def _generate_incremental_query_baseline(self, user_prompt: str, schema: str) -> str:
        """Split question into sub-steps and build final SQL incrementally."""
        step_split_prompt = (
            f"You are given a complex natural language question about a database.\n"
            f"Your task is to break this question into a series of step-by-step sub-questions that build towards the final answer.\n\n"
            f"Database Schema:\n{schema}\n\n"
            f"{user_prompt}\nReturn a list of step-by-step sub-questions."
        )

        subquestions_text = self.query_generator.model.generate(
            system_prompt="You are a helpful assistant who splits complex questions into logical, incremental steps.",
            user_prompt=step_split_prompt,
        )

        subquestions = [line.strip("- ").strip() for line in subquestions_text.strip().splitlines() if line.strip()]
        print(f"Sub-questions: {subquestions}")

        intermediate_queries = []
        for step in subquestions:
            step_sql = self.query_generator.generate_baseline(user_prompt=step, schema=schema)
            intermediate_queries.append({"step": step, "sql": step_sql})
        print(f"Steps: {intermediate_queries}")

        final_sql_prompt = (
            f"Given the following SQL steps and their sub-questions, generate a final SQL query that answers the original question:\n\n"
            f"{user_prompt}\nPlease use the most complete question\n\nSteps:\n"
        )
        for i, q in enumerate(intermediate_queries, 1):
            final_sql_prompt += f"Step {i}: {q['step']}\nSQL: {q['sql']}\n\n"
        final_sql_prompt += "Return only the final SQL query that answers the full question."

        return self.query_generator.generate_baseline(
            user_prompt=final_sql_prompt, schema=schema
        ).strip()

    def _generate_incremental_query_v1(self, user_prompt: str, schema: str) -> str:
        """Split question into sub-steps and build final SQL incrementally."""
        step_split_prompt = (
            f"You are given a complex natural language question about a database.\n"
            f"Your task is to break this question into a series of step-by-step sub-questions that build towards the final answer.\n\n"
            f"Database Schema:\n{schema}\n\n"
            f"{user_prompt}\nReturn a list of step-by-step sub-questions."
        )

        subquestions_text = self.query_generator.model.generate(
            system_prompt="You are a helpful assistant who splits complex questions into logical, incremental steps.",
            user_prompt=step_split_prompt,
        )

        subquestions = [line.strip("- ").strip() for line in subquestions_text.strip().splitlines() if line.strip()]
        print(f"Sub-questions: {subquestions}")

        intermediate_queries = []
        for step in subquestions:
            relevant_example = self.retrieve_context.generate(user_prompt=step)
            step_sql = self.query_generator.generate_v1(user_prompt=step, schema=schema, example=relevant_example)
            intermediate_queries.append({"step": step, "sql": step_sql})
        print(f"Steps: {intermediate_queries}")

        final_sql_prompt = (
            f"Given the following SQL steps and their sub-questions, generate a final SQL query that answers the original question:\n\n"
            f"{user_prompt}\nPlease use the most complete question\n\nSteps:\n"
        )
        for i, q in enumerate(intermediate_queries, 1):
            final_sql_prompt += f"Step {i}: {q['step']}\nSQL: {q['sql']}\n\n"
        final_sql_prompt += "Return only the final SQL query that answers the full question."

        relevant_example = self.retrieve_context.generate(user_prompt=final_sql_prompt)
        return self.query_generator.generate_v1(
            user_prompt=final_sql_prompt, schema=schema, example=relevant_example
        ).strip()

    def generate_v4(self, user_prompt: str) -> str:
        """Uses incremental sub-question splitting and multistage error correction."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        final_query = self._generate_incremental_query_v1(rewritten_prompt, schema)
        attempts_left = self.config.max_retry_attempt

        while attempts_left > 0:
            try:
                self.query_executor.execute_query(final_query)
                break
            except Exception as e:
                attempts_left -= 1
                final_query = self.query_generator.fix_query(
                    user_prompt=rewritten_prompt,
                    sql_query=final_query,
                    error_message=str(e),
                    schema=schema,
                )
        return final_query

    def generate_v5(self, user_prompt: str) -> str:
        """Same as V4 but includes schema filtering."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        schema = self.schema_linker.generate(user_prompt=user_prompt, filter=True)
        final_query = self._generate_incremental_query_v1(rewritten_prompt, schema)
        attempts_left = self.config.max_retry_attempt

        while attempts_left > 0:
            try:
                self.query_executor.execute_query(final_query)
                break
            except Exception as e:
                attempts_left -= 1
                final_query = self.query_generator.fix_query(
                    user_prompt=rewritten_prompt,
                    sql_query=final_query,
                    error_message=str(e),
                    schema=schema,
                )
        return final_query

    def clean_sql_query(self, query: str) -> str:
        """Clean SQL query string by removing code block markers and comments."""
        query = re.sub(r"```sql|```", "", query, flags=re.IGNORECASE)
        query = re.sub(r"--.*", "", query)
        query = re.sub(r"\n\s*\n", "\n", query).strip()
        return query

    def evaluate(self, query: str, true_query: str, expected_columns: list) -> float:
        """Compare actual SQL query result with true query result.

        Returns accuracy score between 0.0 and 1.0.
        """
        try:
            query = self.clean_sql_query(query)
            true_query = self.clean_sql_query(true_query)
            predicted_result = self.query_executor.execute_query(query)
            expected_result = self.query_executor.execute_query(true_query)

            filtered_expected_result = [
                {col: row[col] for col in expected_columns if col in row}
                for row in expected_result
            ]

            return self.evaluator.calculate_accuracy(
                expected=filtered_expected_result, actual=predicted_result
            )
        except Exception as e:
            print(f"Evaluation error: {e}")
            return 0.0

    def execute_query(self, query: str) -> dict:
        """Execute raw SQL query and return result or error message."""
        try:
            result = self.query_executor.execute_query(query)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    # For experiment use only 
    def predict_rewriter_only(self, user_prompt: str) -> str:
        """Return the rewritten_prompt for the given prompt."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        return rewritten_prompt

    def predict_schema_only(self, user_prompt: str) -> str:
        """Return the filtered schema for the given prompt."""
        schema = self.schema_linker.generate(user_prompt=user_prompt, filter=True)
        return schema

    def predict_relevance_only(self, user_prompt: str) -> str:
        """Return the relevance example for the given prompt."""
        example = self.retrieve_context.generate(user_prompt=user_prompt)
        return example
    
    def predict_schema_rewriter_only(self, user_prompt: str) -> str:
        """Return the filtered schema for the rewritten prompt."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        schema = self.schema_linker.generate(user_prompt=rewritten_prompt, filter=True)
        return schema

    def predict_sql_multistage_only(self, user_prompt: str) -> str:
        """Generate SQL with multistage error handling only (no rewriter or example)."""
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        query = self.query_generator.generate_baseline(user_prompt=user_prompt, schema=schema)
        attempts_left = self.config.max_retry_attempt

        while attempts_left > 0:
            try:
                self.query_executor.execute_query(query)
                break
            except Exception as e:
                attempts_left -= 1
                query = self.query_generator.fix_query(
                    user_prompt=user_prompt,
                    sql_query=query,
                    error_message=str(e),
                    schema=schema,
                )
        return query

    def predict_sql_incremental_only(self, user_prompt: str) -> str:
        """Generate SQL by incrementally breaking down the question only."""
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        return self._generate_incremental_query_baseline(user_prompt=user_prompt, schema=schema)

    def predict_sql_rewriter_only(self, user_prompt: str) -> str:
        """Generate SQL using rewriter only (no example or error handling)."""
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        return self.query_generator.generate_baseline(user_prompt=rewritten_prompt, schema=schema)

    def predict_sql_with_example_only(self, user_prompt: str) -> str:
        """Generate SQL using relevant example only (no rewriter or error handling)."""
        schema = self.schema_linker.generate(user_prompt=user_prompt)
        example = self.retrieve_context.generate(user_prompt=user_prompt)
        return self.query_generator.generate_v1(user_prompt=user_prompt, schema=schema, example=example)

    def predict_sql_schema_only(self, user_prompt: str) -> str:
        """Generate SQL using schema linker only (no example or error handling)."""
        schema = self.schema_linker.generate(user_prompt=user_prompt, filter=True)
        return self.query_generator.generate_baseline(user_prompt=user_prompt, schema=schema)
