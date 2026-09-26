"""Calculo de metricas analiticas"""

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
import duckdb
import pandas as pd
from github_analytics.config import settings
from github_analytics.warehouse.db_manager import WarehouseManager

class MetricsCalculator:
    """Calculador de KPIs y agregaciones analíticas."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.manager = WarehouseManager(db_path=db_path or settings.data_warehouse_path)
    
    def _get_conn(self) -> duckdb.DuckDBPyConnection:
        return self.manager.get_connection()
    
    def get_executive_kpis(
        self,
        repo_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Opctional[date] = None,
    ) -> Dict[str, Any]:
        """Calcula los indicadores macro de flujo y eficiencia"""
        s_date = start_date or date(2020, 1, 1)
        e_date = end_date or date(2030, 12, 31)

        query = """
        WITH issue_scoped AS(
            SELECT
                 i.*,
                 r.nombre as repo_name,
            FROM fct_issue i
            JOIN dim_repo r ON i.repo_key = r.repo_key
            WHERE (? IS NULL OR r.nombre = ?)
              AND i.fecha_creacion_key BETWEEN ? AND ?
        )
        SELECT
            COUNT(*)::BIGINT as total_creados,
            COUNT(CASE WHEN estado = 'closed' THEN 1 END)::BIGINT as total_cerrados,
            COUNT(CASE WHEN estado = 'open' THEN 1 END)::BIGINT as total_abiertos,
            COALESCE(ROUND((COUNT(CASE WHEN estado = 'closed' THEN 1 END)::DOUBLE / NULLIF(COUNT(*), 0)) * 100.0, 2), 0.0) as tasa_cierre_pct,
            COALESCE(ROUND(AVG(CASE WHEN estado = 'closed' THEN lead_time_dias END), 2), 0.0) as lead_time_promedio_dias,
            COALESCE(ROUND(PERCENTILE_COUNT(0.85) WITHIN GROUP (ORDERY BY lead_times_dias), 2), 0.0) as lead_time_p85_dias,
            COALESCE(ROUND(AVG(cant_comentarios),2), 0.0) as promedio_comentarios
        FROM issue_scoped;
        """

        with self._get_conn() as conn:
            row = conn.execute(query, [repo_name, repo_name, s_date, e_date]).fetchone()
        
        return {
            "total_creados": int(row[0]),
            "total_cerrados": int(row[1]),
            "total_abiertos": int(row[2]),
            "tasa_cierre_pct": float(row[3]),
            "lead_time_promedio_dias": float(row[4]),
            "lead_time_p85_dias": float(row[5]),
            "promedio_comentarios": float(row[6]),
        }
    
    def get_weekly_throughput(
        self,
        repo_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Obtiene la serie temporal semanal de tickets cerrados"""
        s_date = start_date or date(2020, 1, 1)
        e_date = end_date or date(2030, 12, 31)

        query = """
        SELECT
            df.anio,
            df.semana_anio,
            MIN(df.fecha_key) as inicio_semana,
            COUNT(i.issue_key) as issues_cerrados
        FROM fct_issue i
        JOIN dim_fecha df ON i.fecha_cierre_key = df.fecha_key
        JOIN dim_repo r ON i.repo_key = r.repo_key
        WHERE i.estado = 'closed'
          AND (? IS NULL OR r.nombre = ?)
          AND df.fecha_key BETWEEN ? AND ?
        GROUP BY df.anio, df.semana_anio
        ODER BY df.anio, df.semana_anio;
        """

        withself._get_conn() as conn:
            return conn.execute(query, [repo_name, repo_name, s_date, e_date]).df()
    
    def get_lead_time_histogram(
        self,
        repo_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Obtiene la distribucion por rangos de tiempo de resolucion"""
        s_date = start_date or date(2020, 1, 1)
        e_date = end_date or date(2030, 12, 31)

        query = """
        SELECT
            CASE
                WHEN lead_time_dias < 1.0 THEN '1. Menos de 24h'
                WHEN lead_time_dias < 3.0 THEN '2. 1-3 días'
                WHEN lead_time_dias < 7.0 THEN '3. 3-7 días'
                WHEN lead_time_dias < 14.0 THEN '4. 1-2 semanas'
                ELSE '5. > 2 semanas'
            END as rango_resolucion,
            COUNT(*)::INTEGER as cantidad_issues
        FROM fct_issue i
        JOIN dim_repo r ON i.repo_key = r.repo_key
        WHERE i.estado = 'closed'
          AND (? IS NULL OR r.nombre = ?)
          AND i.fecha_creacion_key BETWEEN ? AND ?
        GROUP BY 1
        ORDER BY 1;
        """

        with self._get_conn() as conn:
            return conn.execute(query, [repo_name, repo_name, s_date, e_date]).df()
    
    def get_student_contributions(self) -> pd.DataFrame:
        """Calcula métricas de esfuerzo y resolución agrupados por colaborador"""

        query = """
        WITH issues_cerrados_autor AS(
            SELECT
                autor_user_key,
                COUNT(*) as issues_cerrados,
                COUNT( CASE WHEN estado = 'closed' THEN 1 END) as issues_resueltos,
                AVG(CASE WHEN estado = 'closed' THEN lead_time_dias END) as lead_time_avg
            FROM fct_issue
            GROUP BY autor_user_key
        ),
        commits_autor AS(
            SELECT
                autor_user_key,
                COUNT(*) as total_commits,
            FROM fct_commit
            GROUP BY autor_user_key
        )
        SELECT
            u.username,
            COALESCE(ca.total_commits, 0)::INTEGER as total_commits,
            COALESCE(ica.issues_cerrados, 0)::INTEGER as issues_cerrados,
            COALESCE(ica.issues_resueltos, 0)::INTEGER as issues_resueltos,
            ROUND(COALESCE(ica.lead_time_avg, 0.0), 2) as lead_time_promedio_dias
        FROM dim_usuario u
        LEFT JOIN commits_autor ca ON u.user_key = ca.autor_user_key
        LEFT JOIN issues_cerrados_autor ica ON u.user_key = ica.autor_user_key
        WHERE COALESCE(ca.total_commits, 0) > 0 OR COALESCE(ica.issues_cerrados, 0) > 0
        ORDER BY total_commits DESC, issues_resueltos DESC;
        """
        with self._get_conn() as conn:
            return conn.execute(query).df()
    
    def get_available_repositories(self) -> List[str]:
        """Retorna la lista de repositorios presentes en el warehouse"""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT nombre FROM dim_repo ORDER BY nombre").fetchall()
        return [r[0] for r in rows]