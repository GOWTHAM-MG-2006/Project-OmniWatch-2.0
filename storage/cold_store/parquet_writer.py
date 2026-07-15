"""
OmniWatch 2.0 — NexusStore
Component: Parquet Writer
Layer: 4
Phase: 2
Purpose: Write metrics/logs to Parquet files with MinIO upload and local fallback
Inputs: Metric and log record dicts
Outputs: Parquet file paths (local or MinIO)
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from config import config

logger = logging.getLogger(__name__)

COLD_DIR = Path("/tmp/omniwatch-cold")


class ParquetWriter:
    """Writes telemetry data to Parquet files with optional MinIO upload."""

    def __init__(self, base_dir: str | None = None, minio_endpoint: str | None = None,
                 minio_access_key: str | None = None, minio_secret_key: str | None = None):
        self.base_dir = Path(base_dir or os.getenv("OMNIWATCH_COLD_DIR", str(COLD_DIR)))
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.minio_endpoint = minio_endpoint or config.MINIO_ENDPOINT
        self.minio_access_key = minio_access_key or os.environ.get("MINIO_ACCESS_KEY")
        self.minio_secret_key = minio_secret_key or os.environ.get("MINIO_SECRET_KEY")
        if not self.minio_access_key or not self.minio_secret_key:
            logger.warning("MINIO_ACCESS_KEY/MINIO_SECRET_KEY not set; MinIO upload disabled")
        self._minio_client = None

    @property
    def minio_client(self):
        if self._minio_client is None:
            try:
                from minio import Minio
                self._minio_client = Minio(
                    self.minio_endpoint,
                    access_key=self.minio_access_key,
                    secret_key=self.minio_secret_key,
                    secure=False,
                )
            except Exception as e:
                logger.warning("MinIO unavailable, using local fallback: %s", e)
                self._minio_client = False
        return self._minio_client

    def _records_to_table(self, records: list[dict[str, Any]]) -> pa.Table:
        """Convert list of dicts to PyArrow Table."""
        if not records:
            return pa.table({})
        return pa.Table.from_pylist(records)

    def _write_parquet(self, table: pa.Table, subdir: str, filename: str) -> Path:
        """Write table to Parquet file locally."""
        out_dir = self.base_dir / subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / filename
        pq.write_table(table, path)
        logger.info("Wrote %d rows to %s", len(table), path)
        return path

    def _upload_to_minio(self, local_path: Path, bucket: str, object_name: str) -> bool:
        """Upload Parquet file to MinIO bucket."""
        if not self.minio_client:
            return False
        try:
            if not self.minio_client.bucket_exists(bucket):
                self.minio_client.make_bucket(bucket)
            self.minio_client.fput_object(bucket, object_name, str(local_path))
            logger.info("Uploaded %s to minio://%s/%s", local_path, bucket, object_name)
            return True
        except Exception as e:
            logger.warning("MinIO upload failed: %s", e)
            return False

    def write_metrics(self, records: list[dict[str, Any]], partition_date: str | None = None) -> str:
        """Write metric records to Parquet under metrics/ subdirectory."""
        table = self._records_to_table(records)
        date_str = partition_date or datetime.utcnow().strftime("%Y-%m-%d")
        filename = f"metrics_{datetime.utcnow().strftime('%H%M%S')}.parquet"
        path = self._write_parquet(table, f"metrics/{date_str}", filename)

        self._upload_to_minio(path, "omniwatch-telemetry-archive",
                              f"metrics/{date_str}/{filename}")
        return str(path)

    def write_logs(self, records: list[dict[str, Any]], partition_date: str | None = None) -> str:
        """Write log records to Parquet under logs/ subdirectory."""
        table = self._records_to_table(records)
        date_str = partition_date or datetime.utcnow().strftime("%Y-%m-%d")
        filename = f"logs_{datetime.utcnow().strftime('%H%M%S')}.parquet"
        path = self._write_parquet(table, f"logs/{date_str}", filename)

        self._upload_to_minio(path, "omniwatch-telemetry-archive",
                              f"logs/{date_str}/{filename}")
        return str(path)

    def read_parquet(self, path: str) -> pa.Table:
        """Read a Parquet file and return as PyArrow Table."""
        return pq.read_table(path)
