"""Script ejecutable para mostrar un reporte ejecutivo de métricas en consola"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from github_analytics.metrics.calculator import MetricsCalculator

console = Console()

def main() -> None:
    """Imprime el resumen de KPIs y actividad analítica"""
    console.rule("[bold cyan]Reporte Analítico Ejecutivo - GitHub Analytics[/bold cyan]")
    calc = MetricsCalculator()

    repos = calc.get_available_repositories()
    console.print(f"Repositorios auditados: [bold yellow]{', '.join(repos) if repos else 'Todos'}[/bold yellow]\n")

    # 1. KPIs Globales
    kpis = calc.get_executive_kpis()
    kpi_table = Table(title="Indicadores Clave de Desempeño (KPIs)", show_header=True)
    kpi_table.add_column("Métrica de Rendimiento", style="cyan")
    kpi_table.add_column("Valor Calculado", style="bold green", justify="right")

    kpi_table.add_row("Total Issues Creados", str(kpis["total_creados"]))
    kpi_table.add_row("Total Issues Resueltos", str(kpis["total_cerrados"]))
    kpi_table.add_row("Issues Abiertos (WIP)", str(kpis["total_abiertos"]))
    kpi_table.add_row("Tasa de Cierre (Close Rate)", f"{kpis['tasa_cierre_pct']}%")
    kpi_table.add_row("Lead Time Promedio", f"{kpis['lead_time_promedio_dias']} días")
    kpi_table.add_row("Lead Time P85 (Percentil 85)", f"{kpis['lead_time_p85_dias']} días")
    kpi_table.add_row("Promedio Comentarios/Ticket", str(kpis["promedio_comentarios"]))

    console.print(kpi_table)
    console.print()

    # 2. Histograma
    df_hist = calc.get_lead_time_histogram()
    hist_table = Table(title="Distribución de Lead Time (Resolución de Trabajo)")
    hist_table.add_column("Rango de Tiempo", style="magenta")
    hist_table.add_column("Cantidad Tickets", justify="right", style="cyan")
    for row in df_hist.to_dict("records"):
        hist_table.add_row(row["rango_resolucion"], str(row["cantidad_issues"]))
    console.print(hist_table)
    console.print()

    # 3. Top Colaboradores
    df_students = calc.get_student_contributions().head(5)
    stu_table = Table(title="Top 5 Colaboradores")
    stu_table.add_column("Colaborador / Usuario", style="yellow")
    stu_table.add_column("Commits", justify="right", style="green")
    stu_table.add_column("Issues Creados", justify="right")
    stu_table.add_column("Issues Resueltos", justify="right", style="cyan")
    stu_table.add_column("Lead Time Promedio (días)", justify="right")
    for row in df_students.to_dict("records"):
        stu_table.add_row(
            row["username"],
            str(row["total_commits"]),
            str(row["issues_cerrados"]),
            str(row["issues_resueltos"]),
            str(row["lead_time_promedio_dias"]),
        )
    console.print(stu_table)

if __name__ == "__main__":
    main()