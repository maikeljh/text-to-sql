from typing import Dict


class LLMConfig:
    def __init__(
        self,
        type: str,
        api_key: str = "",
        model_path: str = "",
        use_gpu: bool = False,
        model: str = "",
        provider: str = "",
    ):
        self.type = type
        self.api_key = api_key
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.model = model
        self.provider = provider

    def __repr__(self):
        return (
            f"LLMConfig(type={self.type}, provider={self.provider}, "
            f"model={self.model}, use_gpu={self.use_gpu}, "
            f"model_path={self.model_path}, api_key={'****' if self.api_key else 'None'})"
        )


class SLConfig(LLMConfig):
    def __init__(
        self,
        type: str,
        api_key: str = "",
        model_path: str = "",
        use_gpu: bool = False,
        model: str = "",
        provider: str = "",
        schema_path: Dict = None,
    ):
        super().__init__(type, api_key, model_path, use_gpu, model, provider)
        self.schema_path = schema_path if schema_path is not None else {}

    def __repr__(self):
        return (
            f"SLConfig(type={self.type}, provider={self.provider}, "
            f"model={self.model}, use_gpu={self.use_gpu}, "
            f"model_path={self.model_path}, api_key={'****' if self.api_key else 'None'}, "
            f"schema_path={self.schema_path})"
        )


class ContextConfig:
    def __init__(
        self,
        data_path: str,
    ):
        self.data_path = data_path

    def __repr__(self):
        return f"ContextConfig(data_path={self.data_path})"


class QueryConfig:
    """
    Configuration class for managing PostgreSQL database connection settings.
    """

    def __init__(
        self, host: str, database: str, user: str, password: str, port: int = 5432
    ):
        """
        Initializes the QueryConfig object.

        :param host: PostgreSQL server host.
        :param database: Database name.
        :param user: Database user.
        :param password: Database password.
        :param port: Database port (default is 5432).
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port


class Config:
    def __init__(
        self,
        rewriter_config: LLMConfig,
        query_generator_config: LLMConfig,
        schema_linker_config: SLConfig,
        retrieve_context_config: ContextConfig,
        query_executor_config: QueryConfig,
        max_retry_attempt: int = 5,
    ):
        self.rewriter_config = rewriter_config
        self.query_generator_config = query_generator_config
        self.schema_linker_config = schema_linker_config
        self.retrieve_context_config = retrieve_context_config
        self.query_executor_config = query_executor_config
        self.max_retry_attempt = max_retry_attempt

    def __repr__(self):
        return (
            f"Config(rewriter_config={self.rewriter_config}, "
            f"query_generator_config={self.query_generator_config}, "
            f"retrieve_context_config={self.retrieve_context_config}, "
            f"query_executor_config={self.query_executor_config}, "
            f"schema_linker_config={self.schema_linker_config}), "
            f"max_retry_attempt={self.max_retry_attempt}"
        )
