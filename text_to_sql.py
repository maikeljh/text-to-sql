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

    def generate_baseline(self, user_prompt, method):
        filtered_schema = self.schema_linker.generate(user_prompt=user_prompt)
        if method == "Multistage":
            attempts_left = self.config.max_retry_attempt
            query = self.query_generator.generate_baseline(
                user_prompt=user_prompt,
                schema=filtered_schema,
            )
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
                        schema=filtered_schema,
                    )
        elif method == "Incremental":
            step_split_prompt = (
                f"You are given a complex natural language question about a database.\n"
                f"Your task is to break this question into a series of step-by-step sub-questions "
                f"that build towards the final answer.\n\n"
                f"Database Schema:\n{filtered_schema}\n\n"
                f"Question: {user_prompt}\n\n"
                f"Return a list of step-by-step sub-questions."
            )

            # Step 1: Split into incremental sub-questions
            subquestions_text = self.query_generator.model.generate(
                system_prompt="You are a helpful assistant who splits complex questions into logical, incremental steps.",
                user_prompt=step_split_prompt,
            )

            # Parse subquestions into a list (could be numbered list or newline-separated)
            subquestions = [
                line.strip("- ").strip()
                for line in subquestions_text.strip().splitlines()
                if line.strip()
            ]

            # Step 2: Generate SQL for each step
            intermediate_queries = []
            for step in subquestions:
                step_sql = self.query_generator.generate_baseline(
                    user_prompt=step,
                    schema=filtered_schema,
                )
                intermediate_queries.append({"step": step, "sql": step_sql})

            # Step 3: Generate final query based on all steps
            final_sql_prompt = (
                f"Given the following SQL steps and their sub-questions, generate a final SQL query that answers the original question:\n\n"
                f"Original Question: {user_prompt}\n\n"
                f"Steps:\n"
            )
            for i, q in enumerate(intermediate_queries, 1):
                final_sql_prompt += f"Step {i}: {q['step']}\nSQL: {q['sql']}\n\n"

            final_sql_prompt += "Return only the final SQL query that answers the full question."

            final_query = self.query_generator.model.generate(
                system_prompt="You are an expert SQL assistant that synthesizes multiple steps into one correct SQL query.",
                user_prompt=final_sql_prompt,
            )

            return final_query.strip()
        else:
            query = self.query_generator.generate_baseline(
                user_prompt=user_prompt,
                schema=filtered_schema,
            )
        return query

    def generate_v1(self, user_prompt, method):
        rewritten_prompt = self.rewriter.generate(user_prompt=user_prompt)
        filtered_schema = self.schema_linker.generate(user_prompt=user_prompt)
        if method == "Multistage":
            relevant_example = self.retrieve_context.generate(user_prompt=user_prompt)
            attempts_left = self.config.max_retry_attempt
            query = self.query_generator.generate_v1(
                user_prompt=rewritten_prompt,
                schema=filtered_schema,
                example=relevant_example,
            )
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
                        schema=filtered_schema,
                    )
        elif method == "Incremental":
            step_split_prompt = (
                f"You are given a complex natural language question about a database.\n"
                f"Your task is to break this question into a series of step-by-step sub-questions "
                f"that build towards the final answer.\n\n"
                f"Database Schema:\n{filtered_schema}\n\n"
                f"Question: {user_prompt}\n\n"
                f"Return a list of step-by-step sub-questions."
            )

            # Step 1: Split into incremental sub-questions
            subquestions_text = self.query_generator.model.generate(
                system_prompt="You are a helpful assistant who splits complex questions into logical, incremental steps.",
                user_prompt=step_split_prompt,
            )

            # Parse subquestions into a list (could be numbered list or newline-separated)
            subquestions = [
                line.strip("- ").strip()
                for line in subquestions_text.strip().splitlines()
                if line.strip()
            ]

            # Step 2: Generate SQL for each step
            intermediate_queries = []
            for step in subquestions:
                relevant_example = self.retrieve_context.generate(user_prompt=step)
                step_sql = self.query_generator.generate_v1(
                    user_prompt=step,
                    schema=filtered_schema,
                    relevant_example=relevant_example,
                )
                intermediate_queries.append({"step": step, "sql": step_sql})

            # Step 3: Generate final query based on all steps
            final_sql_prompt = (
                f"Given the following SQL steps and their sub-questions, generate a final SQL query that answers the original question:\n\n"
                f"Original Question: {user_prompt}\n\n"
                f"Steps:\n"
            )
            for i, q in enumerate(intermediate_queries, 1):
                final_sql_prompt += f"Step {i}: {q['step']}\nSQL: {q['sql']}\n\n"

            final_sql_prompt += "Return only the final SQL query that answers the full question."

            final_query = self.query_generator.model.generate(
                system_prompt="You are an expert SQL assistant that synthesizes multiple steps into one correct SQL query.",
                user_prompt=final_sql_prompt,
            )

            return final_query.strip()
        else:
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
