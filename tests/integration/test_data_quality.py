"""Pruebas de calidad de datos sobre el Data Warehouse en DuckDB"""

from datetime import datetime, timezone
import pandas as pd
import pytest
from github_analytics.warehouse.db_manager import WarehouseManager

@pytest.fixture
def populated_test_warehouse(in_memory_warehouse: WarehouseManager) -> WarehouseManager:
    """Puebla el warehouse temporal con datos sintéticos para validar calidad."""

    stg_dir = in_memory_warehouse.staging_dir

    # 1. Staging Repos
    df_repos = pd.DataFrame({
        "repo_key": ["rep_01", "rep_02"],
        "repo_id": [1, 2],
        "repo_name": ["repo-a", "repo-b"],
        "full_name": ["org/repo-a", "org/repo-b"],
        "owner_login": ["org", "org"],
        "language": ["Python", "TypeScript"],
        "is_private": [False, False],
        "html_url": ["https://github.com/org/repo-a", "https://github.com/org/repo-b"],
        "description": ["Desc A", "Desc B"],
        "created_at_utc": [
            datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
        ],
    })

    df_repos.to_parquet(stg_dir / "stg_repositories.parquet", index=False)

    # 2. Staging Issues
    df_issues = pd.DataFrame({
        "issue_key": ["iss_1", "iss_2", "iss_3"],
        "issue_id": [101, 102, 103],
        "issue_number": [1, 2, 3],
        "organization": ["org", "org", "org"],
        "repository": ["repo-a", "repo-a", "repo-b"],
        "repo_key": ["rep_01", "rep_01", "rep_02"],
        "author_login": ["user1", "user2", "user1"],
        "author_user_key": ["uk_1", "uk_2", "uk_1"],
        "author_type": ["User", "User", "User"],
        "assignee_login": ["user2", "sin_asignar", "user1"],
        "assignee_user_key": ["uk_2", "uk_none", "uk_1"],
        "title": ["Tarea 1", "Tarea 2", "Tarea 3"],
        "state": ["closed", "open", "closed"],
        "is_pull_request": [False, False, True],
        "comments_count": [2, 0, 5],
        "lead_time_hours": [24.0, None, 72.0],
        "lead_time_dias": [1.0, None, 3.0],
        "created_at_utc": [
            datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 12, 10, 0, tzinfo=timezone.utc),
        ],
        "closed_at_utc": [
            datetime(2026, 1, 13, 10, 0, tzinfo=timezone.utc),
            None,
            datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc), 
        ],
        "updated_at_utc": [
            datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc),
        ],
    })
    df_issues.to_parquet(stg_dir / "stg_issues.parquet", index=False)

    # Ingestar
    in_memory_warehouse.load_from_staging()
    return in_memory_warehouse

def test_primary_key_uniqueness_fct_issue(populated_test_warehouse: WarehouseManager) -> None:
    """Verifica que no existan issue_key duplicados en la tabla de hechos."""
    with populated_test_warehouse.get_connection() as conn:
        result = conn.execute("""
            SELECT issue_key, COUNT(*) as cant
            FROM fct_issue
            GROUP BY issue_key
            HAVING COUNT(*) > 1;
        """).fetchall()
    assert len(result) == 0, f"Existen llaves primarias duplicadas en fct_issue: {result}"

def test_non_null_critical_fields(populated_test_warehouse: WarehouseManager) -> None:
    """Valida la ausencia de nulos en columnas obligatorias de fct_issue y dim_repo."""
    with populated_test_warehouse.get_connection() as conn:
        null_issues = conn.execute("""
            SELECT COUNT(*) FROM fct_issue
            WHERE issue_key IS NULL 
               OR repo_key IS NULL 
               OR autor_user_key IS NULL 
               OR fecha_creacion_key IS NULL 
               OR estado IS NULL;
        """).fetchone()[0]
        assert null_issues == 0, "Se encontraron valores nulos en columnas obligatorias de fct_issue."

        null_repos = conn.execute("""
            SELECT COUNT(*) FROM dim_repo
            WHERE repo_key IS NULL OR nombre IS NULL OR html_url IS NULL;
        """).fetchone()[0]
        assert null_repos == 0, "Se encontraron valores nulos en columnas obligatorias de dim_repo."

def test_temporal_consistency_created_before_closed(populated_test_warehouse: WarehouseManager) -> None:
    """Valida que la fecha de creación sea siempre anterior o igual a la de cierre."""
    with populated_test_warehouse.get_connection() as conn:
        inconsistent_dates = conn.execute("""
            SELECT COUNT(*) FROM fct_issue
            WHERE closed_at_utc IS NOT NULL 
              AND closed_at_utc < created_at_utc;
        """).fetchone()[0]
    assert inconsistent_dates == 0, "Existen registros donde closed_at_utc es anterior a created_at_utc."

def test_lead_time_valid_range(populated_test_warehouse: WarehouseManager) -> None:
    """Valida que los lead times calculados sean estrictamente mayores o iguales a 0."""
    with populated_test_warehouse.get_connection() as conn:
        invalid_lead_times = conn.execute("""
            SELECT COUNT(*) FROM fct_issue
            WHERE lead_time_dias IS NOT NULL AND lead_time_dias < 0;
        """).fetchone()[0]
    assert invalid_lead_times == 0, "Se encontraron lead times negativos."

