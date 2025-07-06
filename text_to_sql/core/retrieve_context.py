from common import ContextConfig
from typing import Dict, List, Any
from sentence_transformers import SentenceTransformer, util

import pandas as pd
import json
import os


class RetrieveContext:
    """
    A class for performing vector search on local files (CSV, JSON, and TXT) containing Question, Answer, and Summary.
    """

    def __init__(self, config: ContextConfig):
        """
        Initializes the VectorSearch class by loading data and computing embeddings.

        :param config: ContextConfig object containing data path and model details.
        """
        self.file_path = config.data_path
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self._load_data()
        self._generate_embeddings()

    def _load_data(self):
        """Loads data from supported file formats (CSV, JSON, TXT)."""
        file_ext = os.path.splitext(self.file_path)[-1].lower()

        try:
            if file_ext == ".csv":
                self.df = pd.read_csv(self.file_path)
            elif file_ext == ".json":
                with open(self.file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                self.df = pd.DataFrame(data)
            elif file_ext == ".txt":
                with open(self.file_path, "r", encoding="utf-8") as file:
                    lines = [line.strip().split("|") for line in file.readlines()]
                self.df = pd.DataFrame(lines, columns=["Question", "Answer", "Summary"])
            else:
                raise ValueError("Unsupported file format. Use CSV, JSON, or TXT.")

            if not {"Question", "Answer", "Summary"}.issubset(self.df.columns):
                raise ValueError(
                    "File must contain 'Question', 'Answer', and 'Summary' columns."
                )
        except Exception as e:
            raise ValueError(f"Error loading file: {e}")

    def _generate_embeddings(self):
        """Precomputes embeddings for the questions in the dataset."""
        self.df["embedding"] = self.df["Question"].apply(
            lambda q: self.model.encode(q, convert_to_tensor=True)
        )

    def search(self, query: str, top_n: int = 1) -> List[Dict[str, Any]]:
        """
        Finds the top N most similar questions to the query and returns their answers and summaries.

        :param query: The input question to match.
        :param top_n: Number of top similar results to return.
        :return: List of dictionaries containing Question, Answer, and Summary for the top matches.
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        similarities = [
            util.pytorch_cos_sim(query_embedding, emb).item()
            for emb in self.df["embedding"]
        ]

        self.df["similarity"] = similarities
        top_results = self.df.nlargest(top_n, "similarity")[
            ["Question", "Answer", "Summary", "similarity"]
        ]

        return top_results.drop(columns=["similarity"]).to_dict(orient="records")

    def generate(self, user_prompt: str) -> Dict[str, Any]:
        """
        Retrieves the most relevant question, answer, and summary based on the input user_prompt.

        :param user_prompt: The input question to match.
        :return: A dictionary containing relevant_question (question), relevant_answer (answer), and relevant_summary (summary).
        """
        result = self.search(user_prompt, top_n=1)
        if result:
            final = {
                "relevant_question": result[0]["Question"],
                "relevant_answer": result[0]["Answer"],
                "relevant_summary": result[0]["Summary"],
            }
        else:
            final = {
                "relevant_question": None,
                "relevant_answer": None,
                "relevant_summary": None,
            }
        print(f"Relevant Example: {final}")
        return final
