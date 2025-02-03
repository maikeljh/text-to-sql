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


class Config:
    def __init__(self, rewriter_config: LLMConfig, query_generator_config: LLMConfig):
        self.rewriter_config = rewriter_config
        self.query_generator_config = query_generator_config

    def __repr__(self):
        return f"Config(rewriter_config={self.rewriter_config}, query_generator_config={self.query_generator_config})"
