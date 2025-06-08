from common import LLMConfig, APIModel, LocalModel


class GeneralLLM:
    """
    Base class for LLM models, supporting both local and API-based models.
    """

    def __init__(self, config: LLMConfig):
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
            timeout=self.config.timeout,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Abstract method to generate a response. Must be implemented by subclasses.

        :param user_prompt: User's input prompt.
        :return: Model-generated response.
        """
        result = self.model.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return result.strip()
