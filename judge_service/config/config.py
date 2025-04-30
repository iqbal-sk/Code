# Platform/src/config/config.py

from pathlib import Path
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

# ─── Compute project root & env-file path ───────────────────────────────────────
CONFIG_DIR = Path(__file__).resolve().parent     # .../judge_service/config
ENV_PATH   = CONFIG_DIR / ".env"

# ─── Base class to load .env and capture ENV_STATE ─────────────────────────────
class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

# ─── All of your original settings live here ───────────────────────────────────
class GlobalConfig(BaseConfig):
    # MongoDB
    MONGO_URI: str
    DB_NAME: str

    # Redis
    REDIS_URL: str
    QUEUE_KEY: str

    # Execution & test-case services
    DOCKER_EXEC_URL: AnyHttpUrl
    TESTCASE_API_FORMAT: str

    # Terminal statuses (comma-separated in .env)
    TERMINAL_STATUSES: List[str]
    LOG_FILE_PATH: Optional[str]
    LOG_DIR: Optional[str]

    @field_validator("TERMINAL_STATUSES", mode="before")
    def _split_str_to_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

# ─── Environment-specific subclasses with prefixes ───────────────────────────────
class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        env_prefix="DEV_",
        extra="ignore",
    )

class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        env_prefix="PROD_",
        extra="ignore",
    )

class TestConfig(GlobalConfig):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        env_prefix="TEST_",
        extra="ignore",
    )

# ─── Factory to pick the right config based on ENV_STATE ────────────────────────
@lru_cache()
def get_config(env_state: Optional[str] = None) -> GlobalConfig:
    state = (env_state or BaseConfig().ENV_STATE or "dev").lower()
    mapping = {
        "dev": DevConfig,
        "prod": ProdConfig,
        "test": TestConfig,
    }
    return mapping.get(state, GlobalConfig)()

# ─── Singleton instance you can import elsewhere ────────────────────────────────
config = get_config(BaseConfig().ENV_STATE)
