"""Pruebas de calidad de datos sobre el Data Warehouse en DuckDB"""

from github_analytics.warehouse.db_manager import WarehouseManager

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

