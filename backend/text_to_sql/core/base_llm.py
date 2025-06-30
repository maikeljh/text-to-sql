from abc import ABC, abstractmethod
from text_to_sql.common import LLMConfig, APIModel, LocalModel
from typing import Optional
import os


class BaseLLM(ABC):
    """
    Base class for LLM models, supporting both local and API-based models.
    """

    def __init__(self, config: LLMConfig, system_prompt_path: str):
        """
        Initializes the LLM model based on the configuration.

        :param config: Configuration object containing model details.
        """
        self.type = config.type
        self.config = config
        self.model = None

        if self.type == "local":
            self.model = self._load_local_model()
        elif self.type == "api":
            self.model = self._load_api_model()
        else:
            raise ValueError(
                "Invalid model type specified. Choose either 'local' or 'api'."
            )

        self.system_prompt = self._load_system_prompt(
            system_prompt_path=system_prompt_path
        )

    def _load_local_model(self) -> LocalModel:
        """Loads a local model if specified in the configuration."""
        if not self.config.model_path:
            raise ValueError("Model path must be provided for local models.")
        return LocalModel(
            model_path=self.config.model_path, use_gpu=self.config.use_gpu
        )

    def _load_api_model(self) -> APIModel:
        """Loads an API-based model if specified in the configuration."""
        if not self.config.api_key:
            raise ValueError("API key must be provided for API models.")
        return APIModel(
            api_key=self.config.api_key,
            model=self.config.model,
            provider=self.config.provider,
        )

    def _load_system_prompt(self, system_prompt_path: Optional[str] = None) -> str:
        """
        Loads the system prompt from a file.

        :param system_prompt_path: Path to the system prompt text file.
        :return: System prompt as a string.
        """
        if not system_prompt_path or not os.path.exists(system_prompt_path):
            raise FileNotFoundError(
                f"System prompt file not found at {system_prompt_path}."
            )

        with open(system_prompt_path, encoding="utf-8") as file:
            return file.read().strip()

    @abstractmethod
    def generate(self, user_prompt: str) -> str:
        """
        Abstract method to generate a response. Must be implemented by subclasses.

        :param user_prompt: User's input prompt.
        :return: Model-generated response.
        """
        pass
