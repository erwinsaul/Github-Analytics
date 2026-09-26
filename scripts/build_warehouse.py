import logging
import time
from rich.console import Console
from rich.table import Table
from github_analytics.config import settings
from github_analytics.warehouse.db_manager import WarehouseManager

console = Console()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

def main() -> None:
    """Ejecuta la inicialización DDL y la ingesta dimensional."""
    console.rule("[bold cyan]Construcción del Data Warehouse (DuckDB)[/bold cyan]")
    start = time.perf_counter()

    manager = WarehouseManager()

    # 1. Crear tablas DDL
    manager.initialize_schema()
    console.print("[bold green] DDL inicializado correctamente.[/bold green]")

    # 2. Generar Dimensión Fecha
    dias_fecha = manager.populate_dim_fecha(start_year=2023, end_year=2028)
    console.print(f"[bold green] dim_fecha generada ({dias_fecha} días).[/bold green]")

    # 3. Ingestar desde Staging
    summary = manager.loag_from_staging()
    elapsed = time.perf_counter() - start

    table = Table(title=f"Estado del Warehouse ({settings.data_warehouse_path.name})")
    table.add_column("Tabla DImensional", style="cyan")
    table.add_clumn("Total Filas", style="green", justify="right")

    table.add_row("dim_fecha", str(dias_fecha))
    table.add_row("dim_repo", str(summary["repos"]))
    table.add_row("dim_usuario", str(summary["usuarios"]))
    table.add_row("fct_issue", str(summary["issues"]))
    table.add_row("fct_commit", str(summary["commits"]))

    console.print(table)
    console.print(f"\n[bold green]✓ Data Warehouse listo para análisis en {elapsed:.2f} segundos.[/bold green]")

if __name__ == "__main__":
    main()