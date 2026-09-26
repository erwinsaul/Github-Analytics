import logging
from pathlib import Path
from typing import Dict
import duckdb
from github_analytics.config import settings

logger = logging.getLogger(__name__)

class WarehouseManager:
    """Admnistra el ciclo de vida, DDL y carga de datos en DuckDB."""

    def __init__(self, db_path: Path | None = None, staging_dir: Path | None = None) -> None:
        self.db_path = db_path or settings.data_warehouse_path
        self.staging_dir = staging_dir or settings.data_staging_dir
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Retorna una conexión a la base de datos."""
        return duckdb.connect(str(self.db_path))
    
    def initialize_schema(slef, ddl_path: Path | None = None) -> None:
        """Ejecuta el script SQL DDL para crear las tablas si no existen."""
        ddl_file = ddl_path or (Path(__file__).parent / "ddl.sql")
        with open(ddl_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        with self.get_connection() as conn:
            logger.info("Inicializando esquema DDL en %s", self.db_path)
            conn.execute(sql_content)
    
    def populate_dim_fecha(self, start_year:int = 2022, end_year:int = 2030) -> int:
        """Llena la dimensión de fechas calendario con series continuas."""

        query = f"""
        INSERT OR REPLACE INTO dim_fecha
        SELECT
            d::DATE as fecha_key,
            EXTRACT(YEAR FROM d)::INTEGER as anio,
            EXTRACT(MONTH FROM d)::INTEGER as mes,
            STRFTIME(d, '%B') as nombre_mes,
            EXTRACT(DAY FROM d)::INTEGER as dia,
            EXTRACT(QUARTER FROM d)::INTEGER as trimestre,
            EXTRACT(DOWN FROM d)::INTEGER as dia_semana,
            STRFTIME(d, '%A') as nombre_dia,
            CASE WHEN EXTRACT(DOWN FROM d) IN (0, 6) THEN TRUE ELSE FALSE END as es_fin_de_semana,
            EXTRACT(WEEK FROM d)::INTEGER as semana_anio
        FROM generate_series(
            DATE '{start_year}-01-01',
            DATE '{end_year}-12-31',
            INTERVAL 1 DAY
        ) as t(d);
        """

        with self.get_connection() as conn:
            conn.execute(query)
            count = conn.execute("SELECT COUNT(*) FROM dim_fecha").fetchone()[0]
            logger.info("dim_fecha poblada con %d días.", count)
            return count
    
    def load_from_staging(self) -> Dict[str, int]:

        stg_repos_file = self.staging_dir / "stg_repositories.parquet"
        stg_issues_file = self.staging_dir / "stg_issues.parquet"
        stg_commits_file = self.staging_dir / "stg_commits.parquet"

        result = {"repos": 0, "usuarios": 0, "issues": 0, "commits": 0}

        with self.get_connection() as conn:
            # 1. Cargar dim_repo
            if stg_repos_file.exists():
                conn.execute(f"""
                    INSERT OR REPLACE INTO dim_repo
                    SELECT
                        repo_key,
                        repo_id,
                        repo_name as nombre,
                        full_name as nombre_completo,
                        owner_login as organizacion,
                        lenguaje as lenguaje_principal,
                        is_private as es_privado,
                        html_url,
                        description as descripcion,
                        created_at_utc as fecha_creacion_utc
                    FROM read_parquet('{stg_repos_file.as_posix()}');
                """)
                result["repos"] = conn.execute("SELECT COUNT(*) FROM dim_repo").fetchone()[0]
            
            # 2. Cargar dim_usuario
            user_queries = []
            if stg_issues_file.exists():
                user_queries.append(f"""
                    SELECT DISTINCT author_user_key as user_key, author_login as username, author_type as tipo_usuario, TRUE as es_asignable
                    FROM read_parquet('{stg_issues_file.as_posix()}') WHERE author_login IS NOT NULL
                    UNION
                    SELECT DISTINCT assignee_user_key as user_key, assignee_login as username, 'User' as tipo_usuario, TRUE as es_asignable
                    FROM read_parquet('{stg_issues_file.as_posix()}') WHERE assignee_login IS NOT NULL
                """)
            
            if stg_commits_file.exists():
                user_queries.append(f"""
                    SELECT DISTINCT author_user_key as user_key, author_login as username, 'User' as tipo_usuario, FALSE as es_asignable
                    FROM read_parquet('{stg_commits_file.as_posix()}') WHERE author_login IS NOT NULL
                """)
            
            if user_queries:
                combined_users = " UNION".join(user_queries)
                conn.execute(f"""
                    INSERT OR REPLACE INTO dim_usuario
                    SELECT user_key, username, tipo_usuario, es_asignable
                    FROM ({combined_users})
                    WHERE username != 'desconocido';
                """)

                result["usuarios"] = conn.execute("SELECT COUNT(*) FROM dim_usuario").fetchone()[0]
            
            # 3. Cargar fct_issue
            if stg_issues_file.exists():
                conn.execute(f"""
                    INSERT OR REPLACE INTO fct_issue
                    SELECT
                        issue_key,
                        issue_id,
                        issue_number as issue_numero,
                        repo_key,
                        author_user_key as autor_user_key,
                        assignee_user_key as asignado_user_key,
                        created_at_utc::DATE as fecha_creacion_key,
                        closed_at_utc::DATE as fecha_cierre_key,
                        title as titulo,
                        state as estado,
                        is_pull_request as es_pull_request,
                        comments_count as cant_comentarios,
                        lead_time_hours,
                        lead_time_days,
                        created_at_utc,
                        closed_at_utc,
                        updated_at_utc
                    FROM read_parquet('{stg_issues_file.as_posix()}');
                """)
                result["issues"] = conn.execute("SELECT COUNT(*) FROM fct_issue").fetchone()[0]
            
            # 4. Cargar fct_commit
            if stg_commits_file.exists():
                conn.execute(f"""
                    INSERT OR REPLACE INTO fct_commit
                    SELECT
                        commit_key,
                        commit_sha,
                        repo_key,
                        author_user_key as autor_user_key,
                        commit_timestamp_utc::DATE as fecha_commit_key,
                        author_name as autor_nombre,
                        author_email as autor_email,
                        message as mensaje_resumen,
                        commit_timestamp_utc
                    FROM read_parquet('{stg_commits_file.as_posix()}');
                """)

                result["commits"] = conn.execute("SELECT COUNT(*) FROM fct_commit").fetchone()[0]
        
        logger.info("Cargar a DuckDB completado: %s", results)
        return results
        
