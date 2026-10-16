"""Pruebas unitarias de limpieza y transformación en Pandas."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
import pandas as pd
import pytest
from github_analytics.transformers.staging_cleaner import (
    clean_issues_staging,
    clean_repositories_staging,
)

def test_clean_repositories_staging(sample_raw_repository_json: Dict[str, Any]) -> None:
    """Valida el proceso de limpieza de datos de repositorios en staging."""
    df_raw = pd.DataFrame({
        "raw_payload": [json.dumps(sample_raw_repository_json)],
        "organization": ["mi-organizacion"],
        "repository": ["proyecto-backend"],
    })

    df_clean = clean_repositories_staging(df_raw)

    assert len(df_clean) == 1
    assert df_clean["repo_name"][0] == "proyecto-backend"
    assert df_clean["language"][0] == "Python"
    assert "repo_key" in df_clean.columns
    assert df_clean["created_at_utc"][0] == datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)

def test_clean_issues_staging_lead_time_calculation(sample_raw_issues_json: list) -> None:
    """Valida el cómputo exacto de Lead Time y manejo de nulos en issues."""
    df_raw = pd.DataFrame({
        "raw_payload": [json.dumps(i) for i in sample_raw_issues_json],
        "organization": ["mi-organizacion", "mi-organizacion"],
        "repository": ["proyecto-backend", "proyecto-backend"],
    })

    df_clean = clean_issues_staging(df_raw)

    assert len(df_clean) == 2

    # Issue 101 cerrado: lead_time debe ser exactamente 48 horas (2.0 días)
    row_closed = df_clean[df_clean["issue_id"] == 101].to_dict("records")[0]
    assert row_closed["state"] == "closed"
    assert pytest.approx(row_closed["lead_time_hours"], 0.01) == 48.0
    assert pytest.approx(row_closed["lead_time_dias"], 0.01) == 2.0
    assert row_closed["assignee_login"] == "colaborador2"

    # Issue 102 abierto: lead_time debe ser nulo (NaN) al no haberse resuelto
    row_open = df_clean[df_clean["issue_id"] == 102].to_dict("records")[0]
    assert row_open["state"] == "open"
    assert pd.isna(row_open["lead_time_hours"])
    assert row_open["assignee_login"] == "sin_asignar"