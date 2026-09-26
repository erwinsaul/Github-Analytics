"""Orquestador de extracción de GitHub"""

import logging
from datetime import datetime, timezone
from typing import Dict, List
from github_analytics.config import settings
from github_analytics.extractors.github_client import GitHubAPIClient
from github_analytics.extractors.raw_storage import RawDataLakeWriter

logger = logging.getLogger(__name__)


class RawIngestionPipeline:
    """Pipeline orquestador para extraer y persistir datos"""

    def __init__(self, client: GitHubAPIClient | None = None, writer: RawDataLakeWriter | None = None) -> None:
        self.client = client or GitHubAPIClient()
        self.writer = writer or RawDataLakeWriter()
    
    def run_for_repositories(self, org: str, repositories: List[str]) -> Dict[str, int]:
        """Ejecuta el ciclo de extracción"""

        summary = {"repos": 0, "issues": 0, "commits": 0}
        now_utc = datetime.now(timezone.utc)

        logger.info("Iniciando ingesta para la org '%s' (%d repos)", org, len(repositories))

        for repo_name in repositories:
            try:
                logger.info("=== Extrayendo metadatos de '%s/%s' ===", org, repo_name)
                repo_info = self.client.get_repository_details(org, repo_name)
                self.writer.save_raw_batch("repository", org, repo_name, [repo_info], now_utc)
                summary["repos"] += 1

                logger.info("=== Extrayendo issues y pull requests de '%s/%s' ===", org, repo_name)
                issues = self.client.get_issues_and_prs(org, repo_name, state="all")
                if issues:
                    self.writer.save_raw_batch("issues", org, repo_name, issues, now_utc)
                    summary["issues"] += len(issues)

                logger.info("=== Extrayendo commits de '%s/%s' ===", org, repo_name)
                commits = self.client.get_commits(org, repo_name)
                if commits:
                    self.writer.save_raw_batch("commits", org, repo_name, commits, now_utc)
                    summary["commits"] += len(commits)

            except Exception as e:
                logger.error("Error al procesar el repositorio '%s/%s': %s", org, repo_name, e, exc_info=True)

        logger.info("Ingesta completada. Resumen: %s", summary)
        return summary  
        