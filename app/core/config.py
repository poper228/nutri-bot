from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProviderName = Literal["gemini", "anthropic"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: SecretStr | None = Field(default=None, alias="BOT_TOKEN")

    llm_provider: LLMProviderName = Field(default="gemini", alias="LLM_PROVIDER")

    gemini_api_key: SecretStr | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")

    anthropic_api_key: SecretStr | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-4-6", alias="ANTHROPIC_MODEL")

    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_http_port: int = Field(default=6333, alias="QDRANT_HTTP_PORT")
    qdrant_grpc_port: int = Field(default=6334, alias="QDRANT_GRPC_PORT")
    qdrant_lectures_collection: str = Field(
        default="lecture_chunks_v1", alias="QDRANT_LECTURES_COLLECTION"
    )

    embedding_model: str = Field(
        default="intfloat/multilingual-e5-large", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=1024, alias="EMBEDDING_DIMENSION")

    log_level: LogLevel = Field(default="INFO", alias="LOG_LEVEL")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_http_port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
