from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "staging", "prod"] = "local"
    database_url: str
    jwt_secret: str
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_expire_seconds: int = 604800
    wechat_appid: str
    wechat_secret: str = ""
    media_root: Path
    api_prefix: str = "/api/v1"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    embedding_dim: int = 1024
    embedding_min_cosine: float = 0.25

    def is_local_fake_wechat(self) -> bool:
        return self.app_env == "local" and not self.wechat_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
