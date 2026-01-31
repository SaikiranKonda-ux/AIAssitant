import os
from typing import Optional


class AzureOpenAIConfig:
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: str = "2024-02-01",
        deployment_name: str = "gpt-4"
    ):
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version
        self.deployment_name = deployment_name

        if not self.api_key:
            raise ValueError("Azure OpenAI API key not found. Set AZURE_OPENAI_API_KEY environment variable.")
        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint not found. Set AZURE_OPENAI_ENDPOINT environment variable.")

    def get_client_config(self) -> dict:
        return {
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "api_version": self.api_version,
            "deployment_name": self.deployment_name
        }
