import logging
import sys
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from github_analytics.config import settings
from github_analytics.extractors.github_client import GitHubAPIClient
from github_analytics.extractors.pipeline import RawIngestionPipeline
from github_analytics.extractors.raw_storage import RawDataLakeWriter

console = Console()
logging.basicConfig(
    level=getattr(loggin, settings.log_level.upper(). logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def main() -> None:

    console.rule("[bold cyan]Pipeline de Ingesta Cruda a Parquet[/bold cyan]")
    start_time = time.perf_counter()

    org = settings.github_org
    repos = settings.github_repos

    if not repos:
        console.print("[bold red]No hay repositorios configurados en GITHUB_REPOS.[/bold red]")
        sys.exit(1)
    
    console.print(f"Organizacion: [bold green]{org}[/bold green]")
    console.print(f"Repositorios: [bold yellow]{', '.join(repos)}[/bold yellow]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Extrayendo y serializando a Parquet", total=None )

        with GitHubAPIClient() as client:
            writer = RawDataLakeWriter()
            pipeline = RawIngestionPipeline(client=client, writer=writer)
            summary = pipeline.run_for_repositories(org, repos)
    
    duration = time.perf_counter() - start_time

    console.print("\n[bold green] Ingesta completada con éxito.[/bold green]")
    console.print(f"* Repositorios procesados: {summary['repos']}")
    console.print(f"* Total Issues/PRs guardados: {summary['issues']}")
    console.print(f"* Total Commits guardados: {summary['commits']}")
    console.print(f"* Tiempo de ejecucion: {duration:.2f} segundos")

if __name__ == "__main__":
    main()