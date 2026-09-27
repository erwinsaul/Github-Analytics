"""Pruebas unitarias para el módulo de configuración."""

from github_analytics.config import Settings

def test_settings_default_values() -> None:
    """Verifica que los valores por defecto del sistema son válidos."""
    s = Settings(github_token="test_token")
    assert s.github_org == "mi-organizacion"
    assert s.api_max_retries == 5
    assert s.api_timeout_seconds == 30.0
    assert len(s.github_repos) > 0

def test_parse_github_repos_from_csv_string() -> None:
    """Valida el parsing de repositorios delimitados por comas."""
    s = Settings(github_repos="repo-a, repo-b , repo-c ")  # type: ignore
    assert s.github_repos == ["repo-a", "repo-b", "repo-c"]

