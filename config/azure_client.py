from typing import Optional
from openai import AzureOpenAI
from .azure_config import AzureOpenAIConfig


class AzureClientManager:
    _instance: Optional[AzureOpenAI] = None
    _config: Optional[AzureOpenAIConfig] = None

    @classmethod
    def get_client(cls, config: Optional[AzureOpenAIConfig] = None) -> AzureOpenAI:
        if config is None:
            config = AzureOpenAIConfig()

        if cls._instance is None or cls._config != config:
            config_dict = config.get_client_config()
            cls._instance = AzureOpenAI(
                api_key=config_dict["api_key"],
                api_version=config_dict["api_version"],
                azure_endpoint=config_dict["endpoint"]
            )
            cls._config = config

        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None
        cls._config = None
