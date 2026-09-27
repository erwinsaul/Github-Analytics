"""Fixtures compartidas para pruebas unitarias y de integracion"""

import json
from pathlib import Path
from typing import Any, Dict, List
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



