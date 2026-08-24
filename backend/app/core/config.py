from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./sahaik.db"
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    UPLOAD_DIR: Path = Path("uploads")
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def docs_dir(self) -> Path:
        return self.UPLOAD_DIR / "docs"

    @property
    def audio_dir(self) -> Path:
        return self.UPLOAD_DIR / "audio"


settings = Settings()
