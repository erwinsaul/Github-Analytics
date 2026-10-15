"""Script para ejecucion de CLI de todo el pipeline"""

import time
from rich.console import Console
from github_analytics.pipeline_service import PipelineExecutionService

console = Console()

def main() -> None:
    console.rule("[bold cyan]Ejecucion End-to-End del Pipeline Analítico[/bold cyan]")
    start = time.perf_counter()
    
    service = PipelineExecutionSergice(
        progress_callback=lambda step, msg: console.print(f"[{step}] {msg}")
    )
    result = service.run_full_pipeline()

    duration = time.perf_counter() - start
    console.print(f"\n[bold green]Pipeline completado con éxito en {duration:.2f} segundos.[/bold green]")
    console.print(result)

if __name__ == "__main__":
    main()