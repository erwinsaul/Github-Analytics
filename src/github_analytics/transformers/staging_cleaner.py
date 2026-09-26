"""Transoformadores de datos a tablas con pandas"""

import hashlib
import json
import logging
form pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import numpy as np
from github_analytics.config import settings

logger = logging.getLogger(__name__)

def _stable_hash(value: str) -> str:
    
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _safe_json_loads(payload_str: str) -> Dict[str, Any]:

    try:
        return json.loads(payload_str)
    except Exception:
        return {}

def clean_repositories_staging(df_raw_repos: pd.DataFrame) -> pd.DataFrame:
    """Procesa los metadatos de repositorios""".
    if df_raw_repos.empty:
        return pd.DataFrame()
    
def clean_repositories_staging(df_raw_repos: pd.DataFrame) -> pd.DataFrame:
    """Procesa los metadatos de repositorios"""

    payloads = df_raw_repos["raw_payload"].tolist()
    parsed_records = [_safe_json_loads(p) for p in payloads]

    clean_records = []

    for r in parsed_records:
        if not r or "id" not in r:
            continue
        
        clean_records.append({
            "repo_id": int(r["id"]),
            "repo_name": str(r.get("name", "")).strip(),
            "full_name": str(r.get("full_name", "")).strip().lower(),
            "owner_login": str(r.get("owner", {}).get("login", "")).strip().lower(),
            "is_private": bool(r.get("private", False)),
            "html_url": str(r.get("html_url", "")),
            "description": r.get("description"),
            "language": r.get("language") or "Unknown",
            "created_at_raw": r.get("created_at"),
            "updated_at_raw": r.get("updated_at"),
        })

    def_clean = pd.DataFrame(clean_records)
    if df_clean.empty:
        return pd.DataFrame()
    
    df_clean = df_clean.drop_duplicates(subset=["repo_id"], keep="last")

    df_clean["created_at_utc"] = pd.to_datetime(
        df_clean["created_at_raw"], format="%Y-%m-%dT%H:%M:%SZ", utc=True, errors="coerce"
    )

    df_clean["repo_key"] = (df_clean["owner_login"] + "/" + df_clean["repo_name"]).apply(_stable_hash)

    return df_clean.drop(columns=["created_at_raw", "updated_at_raw"])

def clean_issues_staging(df_raw_issues: pd.DataFrame) -> pd.DataFrame:
    """Procesa issues y PRs"""
    
    if df_raw_issues.empty:
        return pd.DataFrame()
    
    payloads = df_raw_issues["raw_payload"].tolist()
    repos = df_raw_issues["repository"].tolist()
    orgs = df_raw_issues["organization"].tolist()

    clean_records = []

    for payload_str, repo_name, org_name in zip(payloads, repos, orgs, strict=False):
        r = _safejson_loads(payload_str)
        if not r or "id" not in r:
            continue
        
        # Identificar si es Pull Request
        is_pr = "pull_request" in r

        user_info = r.get("user") or {}
        assignee_info = r.get("assignee") or {}

        clean_records.append({
            "issue_id": int(r["id"]),
            "issue_number": int(r.get("number", 0)),
            "organization": str(org_name).strip().lower(),
            "repository": str(repo_name).strip().lower(),
            "title": str(r.get("title", "")).strip(),
            "state": str(r.get("state", "open")).strip().lower(),
            "is_pull_request": is_pr,
            "comments_count": int(r.get("comments", 0)),
            "author_id": int(user_info.get("id", 0)) if user_info.get("id") else None,
            "author_login": str(user_info.get("login", "desconocido")).strip().lower(),
            "author_type": str(user_info.get("type", "User")),
            "assignee_id": int(assignee_info.get("id", 0)) if assignee_info.get("id") else None,
            "assignee_login": str(assignee_info.get("login", "sin_asignar")).strip().lower(),
            "created_at_raw": r.get("created_at"),
            "closed_at_raw": r.get("closed_at"),
            "updated_at_raw": r.get("updated_at"),
        })
    
    df_clean = pd.DataFrame(clean_records)
    if df_clean.empty:
        return pd.DataFrame()
    
    # Deduplicar por issue_id
    df_clean = df_clean.drop_duplicates(subset=["issue_id"], keep="last")

    for col in ["created_at_raw", "closed_at_raw", "updated_at_raw"]:
        df_clean[f"{col[:-4]}_utc"] = pd.to_datetime(
            df_clean[col], format="%Y-%m-%dT%H:%M:%SZ", utc=True, errors="coerce"
        )
    df_clean = df_clean.drop(columns=["created_at_raw", "closed_at_raw", "updated_at_raw"])

    mask_closed = df_clean["closed_at_utc"].notna()
    df_clean["lead_time_hours"] = np.where(
        mask_closed,
        (df_clean["closed_at_utc"] - df_clean["created_at_utc"]).dt.total_seconds() / 3600.0,
        np.nan
    )

    df_clean["repo_key"] = (df_clean["organization"] + "/" + df_clean["repository"]).apply(_stable_hash)
    df_clean["author_user_key"] = df_clean["author_login"].apply(_stable_hash)
    df_clean["assignee_user_key"] = df_clean["assignee_login"].apply(_stable_hash)
    df_clean["issue_key"] = df_clean["issue_id"].astype(str)

    df_clean["lead_time_dias"] = df_clean["lead_time_hours"] / 24.0

    return df_clean

def clean_commits_staging(df_raw_commits: pd.DataFrame) -> pd.DataFrame:
    """Procesa registros de commits a esquemas normalizados"""
    if df_raw_commits.empty:
        return pd.DataFrame()
    
    payloads = df_raw_commits["raw_payload"].tolist()
    repos = df_raw_commits["repository"].tolist()
    orgs = df_raw_commits["organization"].tolist()

    clean_records = []

    for payload_str, repo_name, org_name in zip(payloads, repos, orgs, strict=False):
        c = _safe_json_loads(payload_str)
        if not c or "sha" not in c:
            continue
        
        sha = str(c.get("sha", "")).strip()
        commit_data = c.get("commit", {})
        author_data = commit_data.get("author", {})
        committer_data = commit_data.get("committer", {})
        github_author = c.get("author") or {}

        # Determinar login de usuario preferido
        user_login = github_author.get("login") or author_data.get("name") or "desconocido"

        clean_records.append({
            "commit_sha": sha,
            "organization": str(org_name).strip().lower(),
            "repository": str(repo_name).strip().lower(),
            "author_login": str(user_login).strip().lower(),
            "author_name": str(author_data.get("name", "")).strip(),
            "author_email": str(author_data.get("email", "")).strip().lower(),
            "message": str(commit_data.get("message", "")).split("\n")[0][:255],  # Primer línea del mensaje
            "commit_timestamp_raw": author_data.get("date") or committer_data.get("date"),
        })
    
    df_clean = pd.DataFrame(clean_records)
    if df_clean.empty:
        return pd.DataFrame()
    
    df_clean = df_clean.drop_duplicates(subset=["commit_sha"], keep="last")

    df_clean["commit_timestamp_utc"] = pd.to_datetime(
        df_clean["commit_timestamp_raw"], format="%Y-%m-%dT%H:%M:%SZ", utc=True, errors="coerce"
    )

    df_clean["repo_key"] = (df_clean["organization"] + "/" + df_clean["repository"]).apply(_stable_hash)
    df_clean["author_user_key"] = df_clean["author_login"].apply(_stable_hash)
    df_clean["commit_key"] = df_clean["commit_sha"]

    return df_clean.drop(columns=["commit_timestamp_raw"])

class StagingDataCleaner:
    """Transformar todos los datos crudos a staging"""

    def __init__(self, raw_dir: Path | None = None, staging_dir: Path | None = None) -> None:
        self.raw_dir = raw_dir or settings.data_raw_dir
        self.staging_dir = staging_dir or settings.data_staging_dir
        self.staging_dir.mkdir(parents=True, exist_ok=True)
    
    def process_all(self) -> Dict[str, int]:

        results = {"repos": 0, "issues":0, "commits": 0}

        repo_files = list(self.raw_dir.glob("entity=repository/**/*.parquet"))
        if repo_files:
            df_raw = pd.read_parquet(repo_files)
            df_stg_repos = clean_repositories_staging(df_raw)
            if not df_stg_repos.empty:
                out_path = self.staging_dir / "stg_repositories.parquet"
                df_stg_repos.to_parquet(out_path, compression="snappy", index=False)
                results["repos"] = len(df_stg_repos)
                logger.info("Staging Repositorios guardado: %d filas en %s", len(df_stg_repos), out_path)
        
        issue_files = list(self.raw_dir.glob("entity=issues/**/*.parquet"))
        if issue_files:
            df_raw = pd.read_parquet(issue_files)
            df_stg_issues = clean_issues_staging(df_raw)
            if not df_stg_issues.empty:
                out_path = self.staging_dir / "stg_issues.parquet"
                df_stg_issues.to_parquet(out_path, compression="snappy", index=False)
                results["issues"] = len(df_stg_issues)
                logger.info("Staging Issues guardado: %d filas en %s", len(df_stg_issues), out_path)
        
        commit_files = list(self.raw_dir.glob("entity=commits/**/*.parquet"))
        if commit_files:
            df_raw = pd.read_parquet(commit_files)
            df_stg_commits = clean_commits_staging(df_raw)
            if not df_stg_commits.empty:
                out_path = self.staging_dir / "stg_commits.parquet"
                df_stg_commits.to_parquet(out_path, compression="snappy", index=False)
                results["commits"] = len(df_stg_commits)
                logger.info("Staging Commits guardado: %d filas en %s", len(df_stg_commits), out_path)
        
        return results
    

    
