from pathlib import Path
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# Compute the project root and .env file absolute path
BASE_DIR = Path(__file__).resolve().parents[2]  # Project root: /Users/iqbal/Desktop/Code/Platform
ENV_PATH = BASE_DIR / "src" / "config" / ".env"


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    """Loads the dotenv file. Including this is necessary to get
    pydantic to load a .env file."""
    model_config = SettingsConfigDict(env_file=str(ENV_PATH), extra="ignore")


class GlobalConfig(BaseConfig):
    MONGODB_URI: Optional[str] = None
    DB_NAME: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: Optional[str] = None
    PROBLEM_LIST: Optional[str] = None
    ASSETS_COLLECTION: Optional[str] = None
    TESTCASE_COLLECTION: Optional[str] = None
    SESSION_ID: Optional[str] = None
    TEST_CASES: Optional[str] = None
    LOCAL_TEST_ASSETS: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = 1
    LISTING_FILE: Optional[str] = None
    PROBLEM_COLLECTION: Optional[str] = None
    LISTING_URL: Optional[str] = None
    BASE_SITE: Optional[str] = None
    SCRAPE_LIMIT: int = 0

    REDIS_URL: Optional[str] = None
    TERMINAL: Optional[List[str]] = []
    ACCEPTED_LANGUAGES: List[str] = []
    SUBMISSION_QUEUE_KEY: Optional[str] = None

    @field_validator("TERMINAL", "ACCEPTED_LANGUAGES", mode="before")
    def _split_str_to_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_")


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_")


class TestConfig(GlobalConfig):
    MONGODB_URI: str = "mongodb://localhost:27017"

    model_config = SettingsConfigDict(env_prefix="TEST_")


@lru_cache()
def get_config(env_state: str):
    """Instantiate config based on the environment."""
    configs = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfig}
    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
