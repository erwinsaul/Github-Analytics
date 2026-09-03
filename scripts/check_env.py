""" Verificación del entorno, dependencias y credenciales de GitHub."""

import sys
from rich.console import Console
from rich.table import Table
import httpx
from github_analytics.config import settings

console = Console()

def check_python_version() -> bool:
    major, minor = sys.version_info.major, sys.version_info.minor
    is_valid = (major, minor) >= (3, 11)
    status = "[bold green]OK[/bold green]" if is_valid else "[bold red]FALLÓ[/bold red]"
    console.print(f"Versión de Python: {major}.{minor}.{sys.version_info.micro} -> {status}")
    return is_valid

def check_github_auth() -> bool:
    """Prueba la conectividad y validez del token de GitHub."""

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-analytics/0.1.0",
    }

    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    
    try:
        with httpx.Client(timeout=settings.api_timeout_seconds) as client:
            response = client.get(f"{settings.api_base_url}/rate_limit", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            core_limit = data.get("resources", {}).get("core", {})
            limit = core_limit.get("limit", 0)
            remaining = core_limit.get("remaining", 0)

            console.print(
                f"[bold green]Conexión a GitHub API exitosa.[/bold green] "
                f"Rate Limit: {remaining}/{limit} consultas restantes."
            )

            return True
        
        else:
            console.print(
                f"[bold red]Error al autenticar en GitHub API.[/bold red] "
                f"Código: {response.status_code} - {response.text}"
            )
            return False
    
    except Exception as e:
        console.print(f"[bold red]Excepción al conectar con GitHub:[/bold red] {e}")
        return False

def main() -> None:
    """Realizar la Verificación"""
    console.rule("[bold cyan]Diagnóstico de Entorno - github-analytics[/bold cyan]")

    table = Table(title="Configuraciones Cargadas")
    table.add_column("Parámetro", style="cyan")
    table.add_column("Valor", style="magenta")

    table.add_row("Organización GitHub", settings.github_org)
    table.add_row("Repositorios a Auditar", ", ".join(settings.github_repos))
    table.add_row("Token Presente", "Sí" if bool(settings.github_token) else "No (Modo Anónimo)")
    table.add_row("Ruta Raw Data", str(settings.data_raw_dir))
    table.add_row("Ruta Warehouse", str(settings.data_warehouse_path))

    console.print(table)
    console.print()

    py_ok = check_python_version()
    gh_ok = check_github_auth()

    if py_ok and gh_ok:
        console.print("\n[bold green]✓ Entorno configurado correctamente.[/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]✗ Existen errores en la configuración del entorno.[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
