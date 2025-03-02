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


class Config:
    def __init__(
        self,
        rewriter_config: LLMConfig,
        query_generator_config: LLMConfig,
        schema_linker_config: SLConfig,
    ):
        self.rewriter_config = rewriter_config
        self.query_generator_config = query_generator_config
        self.schema_linker_config = schema_linker_config

    def __repr__(self):
        return (
            f"Config(rewriter_config={self.rewriter_config}, "
            f"query_generator_config={self.query_generator_config}, "
            f"schema_linker_config={self.schema_linker_config})"
        )
