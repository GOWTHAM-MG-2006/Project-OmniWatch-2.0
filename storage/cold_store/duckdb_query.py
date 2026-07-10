"""
OmniWatch 2.0 — NexusStore
Component: DuckDB Query Engine
Layer: 4
Phase: 2
Purpose: Query Parquet files using DuckDB in-memory engine
Inputs: Parquet file paths and SQL queries
Outputs: Query result rows as list of dicts
"""

import os
import logging
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


class DuckDBQueryEngine:
    """In-memory DuckDB engine for querying Parquet files."""

    def __init__(self):
        self._conn = duckdb.connect(database=":memory:")

    def register_parquet(self, view_name: str, path: str) -> None:
        """Register a Parquet file (or directory) as a DuckDB view."""
        p = Path(path)
        if p.is_dir():
            self._conn.execute(
                f"CREATE OR REPLACE VIEW {view_name} AS "
                f"SELECT * FROM read_parquet('{p}/**/*.parquet', hive_partitioning=true)"
            )
        else:
            self._conn.execute(
                f"CREATE OR REPLACE VIEW {view_name} AS "
                f"SELECT * FROM read_parquet('{p}')"
            )
        logger.info("Registered view '%s' from %s", view_name, path)

    def query_parquet(self, path: str, sql: str, view_name: str = "data") -> list[dict[str, Any]]:
        """Register a Parquet source and execute SQL against it."""
        self.register_parquet(view_name, path)
        result = self._conn.execute(sql).fetchall()
        columns = [desc[0] for desc in self._conn.description]
        return [dict(zip(columns, row)) for row in result]

    def query_multiple(self, sources: dict[str, str], sql: str) -> list[dict[str, Any]]:
        """Register multiple Parquet sources and execute a cross-source SQL query.

        Args:
            sources: mapping of view_name -> parquet path
            sql: SQL query referencing the view names
        """
        for view_name, path in sources.items():
            self.register_parquet(view_name, path)
        result = self._conn.execute(sql).fetchall()
        columns = [desc[0] for desc in self._conn.description]
        return [dict(zip(columns, row)) for row in result]

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
