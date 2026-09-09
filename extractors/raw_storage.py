"""Almacenamiento y particionamiento de datos""""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import pyarrow as pa
import pyarrow.parquet as pq
from github_analytics.config import settings

logger = logging.getLogger(__name__)

class RawDataLakeWriter:
    """Escribe payloads"""
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.data_raw_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _compute_hash(data: Any) -> str:
        """Calcula el hash SHA-256"""
        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
    
    def save_raw_batch(
        self,
        entity_name: str,
        org: str,
        repo: str,
        records: List[Dict[str, Any]],
        extraction_timestamp: datetime | None = None,
    ) -> Path:
        """Guarda una lista de diccionarios
        Esquema de columnas:
        - raw_payload (string JSON)
        - entity_type (string)
        - organization (string)
        - repository (string)
        - payload_sha256 (string)
        - extracted_at_utc (timestamp[us])
        - year (int32)
        - month (int32)
        """

        if not records:
            logger.info("No hay registros que guardar para %s/%s entidad '%s'", org, repo, entity_name)
            return self.base_dir
        
        ts = extraction_timestamp or datetime.now(timezone.utc)
        year_val = ts.year
        moth_val = ts.month

        # Construir listas de columnas 
        raw_payloads = [json.dumps(r, default=str) for r in records]
        hashes = [self._compute_hash(r) for r in records]
        entities = [entity_name] * len(records)
        orgs = [org] * len(records)
        repos = [repo] * len(records)
        timestamps = [ts] * len(records)
        years = [year_val] * len(records)
        months = [moth_val] * len(records)

        table = pa.Table.from_arrays(
            [
                pa.array(raw_payloads, type=pa.string()),
                pa.array(entities, type=pa.string()),
                pa.array(orgs, type=pa.string()),
                pa.array(repos, type=pa.string()),
                pa.array(hashes, type=pa.string()),
                pa.array(timestamps, type=pa.timestamp("us", tz="UTC")),
                pa.array(years, type=pa.int32()),
                pa.array(months, type=pa.int32()),
            ],
            names=[
                "raw_payload",
                "entity_type",
                "organization",
                "repository",
                "payload_sha256",
                "extracted_at_utc",
                "year",
                "month",
            ],
        )

        partition_path = (
            self.base_dir
            / f"entity={entity_name}"
            / f"organization={org}"
            / f"repository={repo}"
            / f"year={year_val}"
            / f"month={moth_val:02d}"
        )
        partition_path.mkdir(parents=True, exist_ok=True)

        batch_id = ts.strftime("%Y%m%d_%H%M%S")
        file_path = partition_path / f"part_{batch_id}_{len(records)}_records.parquet"

        pq.write_table(
            table,
            file_path,
            compression="SNAPPY",
            use_dictionary=True,
        )
        logger.info("Guardados %d registros en: %s", len(records), file_path)
        return file_path