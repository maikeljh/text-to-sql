from transformers import pipeline
import torch


class LocalModel:
    def __init__(self, model_path: str, use_gpu: bool = False):
        """
        Initializes the LLM model for query rewriting.

        :param model_path: Hugging Face model name (e.g., 'deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B')
        :param use_gpu: Whether to use GPU for inference.
        """
        self.model_path = model_path
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() and use_gpu else "cpu"
        )
        self._load_pipeline()

    def _load_pipeline(self):
        """Loads the Hugging Face pipeline for text generation."""
        print(f"Loading model from {self.model_path} on {self.device}")

        self.pipeline = pipeline(
            "text-generation",
            model=self.model_path,
            tokenizer=self.model_path,
            device=0 if self.device.type == "cuda" else -1,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
            return_full_text=False,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_length: int = 512,
        temperature: float = 0.3,
        top_k: int = 50,
        top_p: float = 0.9,
    ):
        """
        Generates a rewritten query based on user input.

        :param system_prompt: Instruction for rewriting.
        :param user_prompt: The original user query.
        :param max_length: Maximum length of the output.
        :param temperature: Controls randomness.
        :param top_k: Sampling control.
        :param top_p: Nucleus filtering.
        :return: Rewritten query only (no extra text).
        """
        full_prompt = f"""
        {system_prompt}

        Input: {user_prompt}
        Output:
        """

        response = self.pipeline(
            full_prompt.strip(),
            max_length=max_length,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            num_return_sequences=1,
            do_sample=True,
            truncation=True,
        )

        rewritten_query = response[0]["generated_text"].strip()
        rewritten_query = rewritten_query.replace(full_prompt.strip(), "").strip()

        return rewritten_query
