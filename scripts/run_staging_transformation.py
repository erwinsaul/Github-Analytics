import logging
import time
from rich.console import Console
from rich.table import Table
from github_analytics.config import settings
from github_analytics.transformers.staging_cleaner import StagingDataCleaner

console = Console()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

def main() -> None:

    console.rule("[bold cyan]Pipeline de Transformación y Limpieza (Staging)[/bold cyan]")
    start = time.perf_counter()

    cleaner = StagingDataCleaner()
    summary = cleaner.process_all()

    elapsed = time.perf_counter() - start

    table = Table(title="Resultados de Transformación Staging")
    table.add_column("Entidad Staging", style="cyan")
    table.add_column("Registros Limpios", style="green", justify="right")
    table.add_column("Destino Parquet", style="magenta")

    table.add_row("stg_repositories", str(summary["repos"]), str(settings.data_staging_dir / "stg_repositories.parquet"))
    table.add_row("stg_issues", str(summary["issues"]), str(settings.data_staging_dir / "stg_issues.parquet"))
    table.add_row("stg_commits", str(summary["commits"]), str(settings.data_staging_dir / "stg_commits.parquet"))

    console.print(table)
    console.print(f"\n[bold green]✓ Transformación completada en {elapsed:.2f} segundos.[/bold green]")

if __name__ == "__main__":
    main()