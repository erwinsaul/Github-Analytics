"""Script de prueba para validar la extraccion de datos con GitHubAPIClient."""

import logging
from rich.console import Console
from rich.panel import Panel
from github_analytics.config import settings
from github_analytics.extractors.github_client import GitHubAPIClient

logging.basicConfig(level=logging.INFO)
console = Console()

def test_extraction() -> None:
    """Ejecuta una extraccion de prueba sobre un repositorio."""
    org = settings.github_org
    repos = settings.github_repos
    target_repo = repos[0] if repos else "proyectos"

    console.print(Panel(f"Probando extraccion en: [bold cyan]{org}/{target_repo}[/bold cyan]"))

    with GitHubAPIClient() as client:
        try:
            # 1. Metadatos del repositorio
            repo_info = client.get_repository_details(org, target_repo)
            console.print(f"Repositorio: {repo_info.get('full_name')} (Stars: {repo_info.get('stargazers_count')})")

            # 2. Issues (Página 1 para prueba rápida)
            issues = client.get_issues_and_prs(org, target_repo, state="all", max_pages=1)
            console.print(f"Issues/PRs extraídos (pág 1): {len(issues)} items")

            # 3. Commits (Página 1 para prueba rápida)
            commits = client.get_commits(org, target_repo, max_pages=1)
            console.print(f"Commits extraídos (pág 1): {len(commits)} items")

            console.print("\n[bold green] Cliente de GitHub API funcionando al 100%.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error durante la extraccion de prueba:[/bold red] {e}")
            console.print("Nota: Si el repositorio no existe, prueba configurando un repositorio público válido en .env.")

if __name__ == "__main__":
    test_extraction()
