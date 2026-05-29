# Central configuration and environment variables management.

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    app_name: str = "NaijaHealth"
    app_version: str = "1.0.0"

    # Postgres
    postgres_dsn: str = "postgresql+asyncpg://naijahealth:naijahealth@localhost:5432/naijahealth"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "nh_embeddings"
    qdrant_api_key: str | None = None
    qdrant_vector_size: int = 1024

    # Cohere embedder + generator
    cohere_api_key: str | None = None
    cohere_embed_model: str = "embed-multilingual-v3.0"
    cohere_generate_model: str = "command-r-plus-08-2024"
    embed_batch_size: int = 96
    rag_top_k: int = 5

    # Scraper
    scraper_output_dir: str = "data"

    # Scheduler
    scrape_hour: int = 2
    scrape_minute: int = 0
    run_pipeline_after_scrape: bool = True

    # WhatsApp Cloud API
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_verify_token: str = "naijahealth_verify"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_config() -> Config:
    return Config()
