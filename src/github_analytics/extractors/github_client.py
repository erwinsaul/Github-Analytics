"""Cliente HTTP para la extracción de GitHub."""

import logging
import re
import time
from typing import Any, Dict, Generator, List, Optional
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from github_analytics.config import settings
from github_analytics.extractors.rate_limiter import RateLimitTracker

logger = logging.getLogger(__name__)

class GitHubAPIException(Exception):
    """Base para las excepciones de GitHub API."""
    pass

class GitHubAPIClient:
    """Cliente HTTP para la extracción de GitHub."""

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.token = token if token is not None else settings.github_token
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout or settings.api_timeout_seconds
        self.rate_limiter = RateLimitTracker()

        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-analytics/0.1.0",
        }

        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        
        self._client = httpx.Client(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
        )
    
    def close(self) -> None:
        """Cierra el cliente HTTP subyacente."""
        self._client.close()
    
    def __enter__(self) -> "GitHubAPIClient":
        return self
    
    def __exit__(self, ext_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
    
    @staticmethod
    def _parse_next_link(link_header: Optional[str]) -> Optional[str]:
        """Extrae la URL"""
        if not link_header:
            return None
        
        match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
        return match.group(1) if match else None
    
    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1.5, min=2, max=30),
        reraise=True,
    )
    def _execute_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Ejecuta una petición HTTP individual con política de reintentos."""
        self.rate_limiter.check_and_wait_if_needed()

        response = self._client.get(url, params=params)
        self.rate_limiter.update_from_headers(response.headers)

        if response.status_code in (403, 429):
            # Si el rate limit fue alcanzado durante la llamada
            retry_after = response.headers.get("retry-after")
            reset_ts = response.headers.get("x-ratelimit-reset")
            if retry_after:
                wait_time = int(retry_after) + 1
            elif reset_ts:
                wait_time = max(int(reset_ts) - int(time.time()) + 1, 2)
            else:
                wait_time = 10
            
            logger.warning("Bloqueo de tasa detectado (%d). Esperando %d s...", response.status_code, wait_time)
            time.sleep(wait_time)
            response.raise_for_status()
        
        if response.status_code >= 500:
            logger.warning("Error de servidor en GitHub (%d). Reintentando...", response.status_code)
            response.raise_for_status()
        
        if response.status_code == 404:
            logger.error("Recurso no encotrado en GitHub: %s", url)
            raise GitHubAPIException(f"Recurso 404 no encontrado: {url}")
        
        response.raise_for_status()
        return response
    
    def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """Recorre todas las páginas de un endpoint de lista."""
        current_url: Optional[str] = f"{self.base_url}/{endpoint.lstrip('/')}"
        current_params = dict(params or {})
        current_params.setdefault("per_page", 100)
        page_counter = 0

        while current_url:
            page_counter = page_counter + 1
            logger.debug("Solicitando página %d de %s", page_counter, current_url)

            response = self._execute_request(current_url, params=current_params if page_counter == 1 else None)
            data = response.json()

            if not isinstance(data, list):
                if isinstance(data, dict):
                    yield [data]
                break
            
            if not data:
                break
            
            yield data

            if max_pages and page_counter >= max_pages:
                logger.info("Límite de %d páginas alcanzado para %s", max_pages, endpoint)
                break
            
            current_url = self._parse_next_link(response.headers.get("link"))
    
    def get_repository_details(self, org: str, repo: str) -> Dict[str, Any]:
        """Obtiene la información general de un repositorio."""
        url = f"{self.base_url}/repos/{org}/{repo}"
        response = self._execute_request(url)
        return response.json()
    
    def get_issues_and_prs(
        self,
        org: str,
        repo: str,
        state: str = "all",
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Extrae todos los issues y PRs de un repositorio."""
        endpoint = f"repos/{org}/{repo}/issues"
        params = {"state": state, "sort": "created", "direction": "asc""}
        all_records = []
        for page in self.paginate(endpoint, params=params, max_pages=max_pages):
            all_records.extend(page)
        return all_records
    
    def get_commits(
        self,
        org: str,
        repo: str,
        since: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Extrae el historial de commits de un repositorio."""
        endpoint = f"repos/{org}/{repo}/commits"
        params: Dict[str, Any] = {}
        if since:
            params["since"] = since
        
        all_commits = []

        for page in self.paginate(endpoint, params=params, max_pages=max_pages):
            all_commits.extend(page)
        return all_commits
