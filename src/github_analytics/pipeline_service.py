"""Servicio unificado de orquestación end-to-end del pipeline analítico."""

import logging
from typing import Any, Callable, Dict, List, Optional
from github_analytics.config import settings
from github_analytics.extractors.github_client import GitHubAPIClient
from github_analytics.extractors.pipeline import RawIngestionPipeline
from github_analytics.extractors.raw_storage import RawDataLakeWriter
from github_analytics.transformers.pipeline import StagingPipeline
from github_analytics.warehouse.db_manager import WarehouseManager

logger = logging.getLogger(__name__)

def parse_repo_input(raw_input: str) -> tuple[str, List[str]]:
    """Parsea una URL de GitHub o una cadena 'propietario/repo'"""
    text = raw_input.strip()
    if text.startswith("http://") or text.startswith("https://"):
        text = text.replace("https://github.com", "").replace("http://github.com", "")
    text = text.strip("/")

    if "/" in text:
        parts = text.split("/", 1)
        return parts[0], [parts[1]]
    else:
        return settings.github_org, [text]

class PipelineExecutionService:
    """Orquestador desacoplado para ejecutar el pipeline desde CLI o Streamlit UI."""

    def __init__(
        self,
        token: Optional[str] = None,
        org: Optional[str] = None,
        repos: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        self.token = token or settings.github_token
        self.org = org or settings.github_org
        self.repos = repos or settings.github_repos
        self.progress_callback = progress_callback or (lambda step, msg: None)

    def run_full_pipeline(self) -> Dict[str, Any]:
        """Ejecuta ordenadamente las capas Bronze, Silver y Gold."""
        result: Dict[str, Any] = {
            "bronze": {},
            "silver": {},
            "gold": {},
            "status": "success",
        }

        # 1. Capa Bronze (Extracción cruda a Parquet)
        self.progress_callback("Bronze", f"Extrayendo datos de {len(self.repos)} repositorios de {self.org}...")
        client = GitHubAPIClient(token=self.token)
        writer = RawDataLakeWriter()
        raw_pipeline = RawIngestionPipeline(client=client, storage_writer=writer)

        bronze_summary = raw_pipeline.run_for_repositories(org=self.org, repos=self.repos)
        result["bronze"] = bronze_summary
        self.progress_callback("Bronze", "Extracción cruda finalizada con éxito.")

        # 2. Capa Silver (Staging y limpieza en Pandas)
        self.progress_callback("Silver", "Limpiando y tipando datos hacia la capa Staging...")
        staging_pipeline = StagingPipeline()
        silver_summary = staging_pipeline.run()
        result["silver"] = silver_summary
        self.progress_callback("Silver", "Transformación a Parquet limpio finalizado.")

        # 3. Capa Gold (Carga dimensional a DuckDB)
        self.progress_callback("Gold", "Inicializando esquema y cargando dimensiones en DuckDB...")
        manager = WarehouseManager()
        manager.initialize_schema()
        manager.populate_dim_fecha(start_year=2022, end_year=2030)
        gold_summary = manager.load_from_staging()
        result["gold"] = gold_summary
        self.progress_callback("Gold", "Carga a Data Warehouse finalizada con exito.")

        return result