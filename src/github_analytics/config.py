from pathlib import Path
from typing import List
pron pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuraciones globales"""

    # Autenticación GitHub
    github_token: str = Field(
        default="",
        description="Personal Access Token de GitHub para la autenticación en la API REST",
    )

    github_org: str = Field(
        default="propietario",
        description="Organización o usuario dueño de los repositorios a auditar",
    )

    github_repos: List[str] = Field(
        default_factory=lambda: ["repo1", "repo2"],
        description="Lista de repositorios a extraer",
    )

    # Parámetros del cliente HTTP
    api_max_retries: int = Field(default=5, ge=1, le=10)
    api_timeout_seconds: float = Field(default=30.0, gt=0.0)
    api_base_url: str = Field(default="https://api.github.com")

    data_raw_dir: Path = Field(default=Path("data/raw"))
    data_staging_dir: Path = Field(default=Path("data/staging"))
    data_warehouse_path: Path = Field(
        default=Path("data/warehouse/github_analytics.duckdb")
    )

    log_level: str = Field(default="INFO")
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("github_repos", mode="before")
    @classmethod
    def parse_github_repos(cls, value:object) -> List[str]:

        if isinstance(value, str):
            return [repo.strip() for repo in value.split(",") if repo.strip()]
        if isinstance(value, list):
            return [str(repo).strip() for repo in value if str(repo).strip()]
        return []
    
    def ensure_directories_exist(self) -> None:

        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        self.data_staging_dir.mkdir(parents=True, exist_ok=True)
        self.data_warehouse_path.parent.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories_exist()
