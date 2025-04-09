import json, ast
from text_to_sql.common import SLConfig
from .base_llm import BaseLLM
from typing import Dict, List, Any, Set
from sentence_transformers import SentenceTransformer, util


class SchemaLinker(BaseLLM):
    """
    A specialized LLM for linking schemas to user queries and generating structured representations.
    """

    def __init__(self, config: SLConfig):
        """
        Initializes the SchemaLinker model.

        :param config: SLConfig object containing model type, API key, and schema path.
        """
        super().__init__(
            config=config, system_prompt_path="files/schema_linker_system_prompt.txt"
        )
        self.schema_path = config.schema_path
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self._load_schema()

    def _load_schema(self):
        """
        Loads schema details from a JSON file into instance attributes.
        """
        try:
            with open(self.schema_path, "r", encoding="utf-8") as file:
                self.schema = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading schema from {self.schema_path}: {e}")

        self.database = self.schema.get("database", "Unknown Database")
        self.tables = {table["name"]: table for table in self.schema.get("tables", [])}
        self.knowledge_base = self.generate_knowledge_base_text(self.schema)
        self.table_embeddings = self._generate_table_embeddings()

    def _generate_table_embeddings(self) -> Dict[str, Any]:
        """
        Precompute embeddings for table descriptions using a text embedding model.
        If embeddings are already computed, return cached values.
        """
        if hasattr(self, "table_embeddings") and self.table_embeddings:
            return self.table_embeddings

        table_embeddings = {}
        for table_name, knowledge_text in self.knowledge_base.items():
            table_embeddings[table_name] = self.embedding_model.encode(
                knowledge_text, convert_to_tensor=True
            )

        self.table_embeddings = table_embeddings
        return table_embeddings

    def generate_knowledge_base_text(
        self, database_structure: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generates a textual knowledge base from the database schema.
        """
        knowledge_base_mapping = {}

        for table in database_structure.get("tables", []):
            table_name = table["name"]
            table_description = table.get("description", "No description available")

            knowledge_text = f"Table '{table_name}': {table_description}\n\nColumns:\n"

            for column in table.get("columns", []):
                column_name = column["name"]
                column_type = column["type"]
                column_nullable = "NULLABLE" if column.get("nullable") else "NOT NULL"
                column_attributes = (
                    ", ".join(column.get("attributes", []))
                    if column.get("attributes")
                    else "No special attributes"
                )
                column_description = column.get(
                    "description", "No description available"
                )

                knowledge_text += f"- {column_name} ({column_type}, {column_nullable}, {column_attributes}): {column_description}\n"

            knowledge_base_mapping[table_name] = knowledge_text

        return knowledge_base_mapping

    def get_related_tables(self, table_list: List[str]) -> Set[str]:
        """
        Finds all tables related to the given list of tables, including indirect relationships.

        :param table_list: List of table names.
        :return: Set of all related table names.
        """
        related_tables = set(table_list)
        queue = list(table_list)

        while queue:
            table_name = queue.pop(0)
            table = self.tables.get(table_name, {})

            for relation in table.get("relations", []):
                foreign_table = relation["foreign_table"]
                if foreign_table not in related_tables:
                    related_tables.add(foreign_table)
                    queue.append(foreign_table)

        return related_tables

    def generate(self, user_prompt: str) -> Dict[str, Any]:
        """
        Links user query with the provided schema and generates a structured representation.

        :param user_prompt: The natural language query.
        :return: The structured schema-linked query.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        entities = self.predict_entities(user_prompt)
        initial_tables = self.vector_search(entities)
        related_tables = self.get_related_tables(initial_tables)
        print(f"Related Tables: {related_tables}")

        linked_schema = {
            "database": self.database,
            "tables": [
                self.tables[table] for table in related_tables if table in self.tables
            ],
        }

        return linked_schema

    def predict_entities(self, user_prompt: str) -> List[str]:
        """
        Extracts relevant entities from the user query.
        If entity extraction fails, return all table names.
        """
        try:
            llm_response = self.model.generate(
                system_prompt=self.system_prompt, user_prompt=user_prompt
            )

            entities = ast.literal_eval(llm_response.strip())

            if isinstance(entities, list) and all(isinstance(e, str) for e in entities):
                return entities
            else:
                return list(self.tables.keys())

        except (SyntaxError, ValueError, AttributeError):
            print("Error in entity extraction. Returning all tables.")
            return list(self.tables.keys())

    def vector_search(self, entities: List[str], threshold: float = 0.3) -> Set[str]:
        """
        Performs a semantic vector-based search using embeddings to find the most relevant tables.

        :param entities: List of extracted keywords/entities.
        :param threshold: Minimum similarity score to consider a table relevant.
        :return: Set of relevant table names.
        """
        if not entities:
            return set(self.tables.keys())

        entity_embeddings = self.embedding_model.encode(
            entities, convert_to_tensor=True
        )
        relevant_tables = set()

        for i, entity_embedding in enumerate(entity_embeddings):
            best_table = None
            best_score = 0

            for table_name, table_embedding in self.table_embeddings.items():
                similarity_score = util.pytorch_cos_sim(
                    entity_embedding, table_embedding
                ).item()

                if similarity_score > best_score:
                    best_table = table_name
                    best_score = similarity_score

            if best_table and best_score >= threshold:
                relevant_tables.add(best_table)

        return relevant_tables if relevant_tables else set(self.tables.keys())
