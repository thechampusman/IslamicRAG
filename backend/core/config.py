from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    environment: str = "dev"
    port: int = 8000
    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "dolphin-llama3:8b"
    embedding_model: str = "nomic-embed-text"
    top_k: int = 4
    max_generated_tokens: int = 512
    temperature: float = 0.2
    data_raw_dir: str = "data/raw"
    data_processed_dir: str = "data/processed"
    vectordb_dir: str = "data/vectordb"
    allowed_origins: str = "*"
    rate_limit_per_minute: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    @property
    def allowed_origins_list(self) -> List[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

settings = Settings()
