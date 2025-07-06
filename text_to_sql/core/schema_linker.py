import json, ast
from common import SLConfig
from .base_llm import BaseLLM
from typing import Dict, List, Any, Set
from sentence_transformers import SentenceTransformer, util
from collections import defaultdict


class SchemaLinker(BaseLLM):
    """
    A specialized LLM for linking schemas to user queries and generating structured representations.
    """

    def __init__(self, config: SLConfig):
        super().__init__(
            config=config, system_prompt_path="files/prompt/schema_linker_system_prompt.txt"
        )
        self.schema_path = config.schema_path
        self.metadata_path = config.metadata_path
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        if self.metadata_path:
            self._load_metadata()
        if self.schema_path:
            self._load_schema()

    def _load_schema(self):
        try:
            with open(self.schema_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    raise ValueError(f"Schema file at {self.schema_path} is empty.")
                self.schema = content
        except FileNotFoundError as e:
            raise ValueError(f"Error loading schema from {self.schema_path}: {e}")

    def _load_metadata(self):
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as file:
                self.metadata = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading metadata from {self.metadata_path}: {e}")

        self.database = self.metadata.get("database", "Unknown Database")
        self.tables = {table["name"]: table for table in self.metadata.get("tables", [])}
        self.knowledge_base = self.generate_knowledge_base_text(self.metadata)
        self.table_embeddings = self._generate_table_embeddings()

    def _generate_table_embeddings(self) -> Dict[str, Any]:
        if hasattr(self, "table_embeddings") and self.table_embeddings:
            return self.table_embeddings

        table_embeddings = {}
        for table_name, knowledge_text in self.knowledge_base.items():
            table_embeddings[table_name] = self.embedding_model.encode(
                knowledge_text, convert_to_tensor=True
            )

        self.table_embeddings = table_embeddings
        return table_embeddings

    def generate_knowledge_base_text(self, database_structure: Dict[str, Any]) -> Dict[str, str]:
        knowledge_base_mapping = {}
        for table in database_structure.get("tables", []):
            lines = [f"Table: {table['name']} - {table.get('description', 'No description')}", "Columns:"]
            for column in table.get("columns", []):
                column_desc = (
                    f"- {column['name']} ({column['type']}, "
                    f"{'NULLABLE' if column.get('nullable') else 'NOT NULL'}, "
                    f"{', '.join(column.get('attributes', [])) if column.get('attributes') else 'No attributes'}): "
                    f"{column.get('description', 'No description')}"
                )
                lines.append(column_desc)
            knowledge_base_mapping[table["name"]] = "\n".join(lines)
        return knowledge_base_mapping

    def get_related_tables(self, table_list: List[str]) -> Set[str]:
        related_tables = set()
        for table_name in table_list:
            table = self.tables.get(table_name, {})
            for relation in table.get("relations", []):
                foreign_table = relation["foreign_table"]
                if foreign_table not in table_list:
                    related_tables.add(foreign_table)
        return related_tables

    def generate(self, user_prompt: str, filter: bool = False) -> Dict[str, Any]:
        if not filter:
            return {
                "schema": self.schema,
            }

        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt cannot be empty and must be a string.")

        enriched_prompt = self._generate_schema_aware_prompt(user_prompt)
        entities = self.predict_entities(enriched_prompt)
        print(f"Entities: {entities}")

        if not entities:
            return {
                "schema": self.schema,
                "hint": "No entities detected; full schema provided.",
                "usage_note": (
                    "Use the full schema above to answer the user's question. "
                    "No strong signal was found for relevant tables, so consider all available tables."
                ),
                "potential_related_tables": [],
                "hints_detail": {}
            }

        entity_embeddings = self.embedding_model.encode(entities, convert_to_tensor=True)
        print(f"Entity Embeddings: {entity_embeddings}")
        table_scores = defaultdict(float)

        for entity_emb in entity_embeddings:
            for table_name, table_emb in self.table_embeddings.items():
                score = util.pytorch_cos_sim(entity_emb, table_emb).item()
                table_scores[table_name] += score

        sorted_tables_scores = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)
        print(f"Similarity Scores: {sorted_tables_scores}")

        top_k = len(entities)
        top_tables = [t for t, _ in sorted_tables_scores[:top_k]]
        print(f"Top Tables: {top_tables}")
        related_tables = set(top_tables).union(self.get_related_tables(top_tables))
        print(f"Related Tables: {related_tables}")

        hints_detail = {
            t: round(table_scores[t], 4)
            for t in sorted(related_tables)
            if t in table_scores
        }

        hint = (
            "The following tables might be relevant to the user's question: "
            + ", ".join(sorted(related_tables))
        )
        usage_note = (
            "Use the full schema above to answer the user's question. "
            "The hint lists some tables that may be relevant based on prior analysis, "
            "but you are not restricted to them."
        )

        return {
            "schema": self.schema,
            "hint": hint,
            "usage_note": usage_note,
            "potential_related_tables": sorted(list(related_tables)),
            "hints_detail": hints_detail,
        }

    def _generate_schema_aware_prompt(self, user_prompt: str) -> str:
        schema_context = "\n\n".join(self.knowledge_base.values())
        return f"Schema Context:\n{schema_context}\n\nUser Query: {user_prompt}"

    def predict_entities(self, enriched_prompt: str) -> List[str]:
        try:
            llm_response = self.model.generate(
                system_prompt=self.system_prompt, user_prompt=enriched_prompt
            )
            entities = ast.literal_eval(llm_response.strip())
            if isinstance(entities, list) and all(isinstance(e, str) for e in entities):
                return entities
            else:
                return []
        except (SyntaxError, ValueError, AttributeError):
            return []

    def vector_search_multi_entity(self, entities: List[str]) -> Set[str]:
        if not entities:
            return set(self.tables.keys())

        top_k = len(entities)
        entity_embeddings = self.embedding_model.encode(entities, convert_to_tensor=True)
        table_scores = defaultdict(float)

        for entity_emb in entity_embeddings:
            for table_name, table_emb in self.table_embeddings.items():
                score = util.pytorch_cos_sim(entity_emb, table_emb).item()
                table_scores[table_name] += score

        sorted_tables = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)
        return {table for table, _ in sorted_tables[:top_k]}
