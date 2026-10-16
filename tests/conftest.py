"""Fixtures compartidas para pruebas unitarias y de integracion"""

import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone
import duckdb
import pandas as pd
import pytest
from github_analytics.warehouse.db_manager import WarehouseManager

@pytest.fixture
def sample_raw_repository_json() -> Dict[str, Any]:
    """Genera el payload simulado de un repositorio de GitHub."""
    return {
        "id": 12345678,
        "name": "proyecto-backend",
        "full_name": "mi-organizacion/proyecto-backend",
        "private": False,
        "html_url": "https://github.com/mi-organizacion/proyecto-backend",
        "description": "Núcleo de servicios backend",
        "language": "Python",
        "created_at": "2026-01-15T08:00:00Z",
        "updated_at": "2026-03-01T12:00:00Z",
        "owner": {"login": "mi-organizacion", "id": 999},
    }

@pytest.fixture
def sample_raw_issues_json() -> List[Dict[str, Any]]:
    """Genera lista de issues simulados para testing de transformaciones."""
    return [
        {
            "id": 101,
            "number": 1,
            "title": "Configurar base de datos",
            "state": "closed",
            "comments": 3,
            "created_at": "2026-02-01T10:00:00Z",
            "closed_at": "2026-02-03T10:00:00Z",  # Lead time exacto: 48 horas (2 días)
            "updated_at": "2026-02-03T10:00:00Z",
            "user": {"id": 201, "login": "colaborador1", "type": "User"},
            "assignee": {"id": 202, "login": "colaborador2"},
        },
        {
            "id": 102,
            "number": 2,
            "title": "Bug en login de usuarios",
            "state": "open",
            "comments": 0,
            "created_at": "2026-02-05T14:00:00Z",
            "closed_at": None,
            "updated_at": "2026-02-05T14:00:00Z",
            "user": {"id": 202, "login": "colaborador2", "type": "User"},
            "assignee": None,
        },
    ]

@pytest.fixture
def in_memory_warehouse(tmp_path: Path) -> WarehouseManager:
    """Crea una base de datos DuckDB temporal en disco aislada para pruebas."""
    db_file = tmp_path / "test_warehouse.duckdb"
    stg_dir = tmp_path / "staging"
    stg_dir.mkdir(parents=True, exist_ok=True)

    manager = WarehouseManager(db_path=db_file, staging_dir=stg_dir)
    manager.initialize_schema()
    manager.populate_dim_fecha(start_year=2026, end_year=2026)
    return manager

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

