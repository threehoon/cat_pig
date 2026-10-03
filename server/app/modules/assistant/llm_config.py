from functools import lru_cache

from pydantic import SecretStr, field_serializer
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.settings import ENV_FILE


class LlmConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    assistant_llm: str = "off"
    xai_api_key: SecretStr = SecretStr("")
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.7"
    openai_api_key: SecretStr = SecretStr("")
    openai_base_url: str = ""
    openai_model: str = ""

    @field_serializer("xai_api_key", "openai_api_key")
    def hide_keys(self, _value: SecretStr) -> str:
        return ""


@lru_cache
def get_llm_config() -> LlmConfig:
    return LlmConfig()
