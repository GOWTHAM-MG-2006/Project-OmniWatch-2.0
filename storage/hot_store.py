"""
OmniWatch 2.0 — NexusStore
Component: Hot Store (Apache Arrow In-Memory)
Layer: 4
Phase: 1
Purpose: In-memory columnar store for real-time telemetry queries
Inputs: Raw telemetry streams from StreamForge
Outputs: Queryable in-memory tables, flush to warm tier
"""

import time
from typing import Any
from datetime import datetime

import pyarrow as pa
import pyarrow.compute as pc


class HotStore:
    """Apache Arrow in-memory columnar store for real-time queries."""

    def __init__(self):
        self._tables: dict[str, pa.Table] = {}
        self._schemas: dict[str, pa.Schema] = {
            "metrics": pa.schema([
                pa.field("entity_id", pa.string()),
                pa.field("entity_type", pa.string()),
                pa.field("metric_name", pa.string()),
                pa.field("metric_value", pa.float64()),
                pa.field("timestamp", pa.timestamp("ms", tz="UTC")),
            ]),
            "logs": pa.schema([
                pa.field("entity_id", pa.string()),
                pa.field("service_name", pa.string()),
                pa.field("log_level", pa.string()),
                pa.field("message", pa.string()),
                pa.field("timestamp", pa.timestamp("ms", tz="UTC")),
            ]),
            "traces": pa.schema([
                pa.field("trace_id", pa.string()),
                pa.field("service_name", pa.string()),
                pa.field("operation_name", pa.string()),
                pa.field("duration_ms", pa.float64()),
                pa.field("start_time", pa.timestamp("ms", tz="UTC")),
            ]),
        }
        for name, schema in self._schemas.items():
            self._tables[name] = pa.table({field.name: pa.array([], type=field.type) for field in schema})

    def ingest_batch(self, table_name: str, records: list[dict[str, Any]]) -> int:
        """Ingest a batch of records into a hot table. Returns count ingested."""
        if table_name not in self._schemas:
            raise ValueError(f"Unknown table: {table_name}")

        schema = self._schemas[table_name]
        new_table = pa.table(
            {field.name: [r.get(field.name) for r in records] for field in schema},
            schema=schema,
        )
        self._tables[table_name] = pa.concat_tables([self._tables[table_name], new_table])
        return len(records)

    def query(self, table_name: str, filters: list | None = None, limit: int = 1000) -> pa.Table:
        """Query the hot store with optional filters."""
        if table_name not in self._tables:
            raise ValueError(f"Unknown table: {table_name}")

        table = self._tables[table_name]
        if filters:
            mask = pc.and_(*filters)
            table = table.filter(mask)
        return table.slice(0, limit)

    def flush_to_warm(self, table_name: str) -> pa.Table:
        """Flush hot data and return it for writing to warm tier."""
        if table_name not in self._tables:
            raise ValueError(f"Unknown table: {table_name}")

        table = self._tables[table_name]
        self._tables[table_name] = pa.table(
            {field.name: pa.array([], type=field.type) for field in self._schemas[table_name]}
        )
        return table

    def row_count(self, table_name: str) -> int:
        """Get current row count for a table."""
        if table_name not in self._tables:
            return 0
        return len(self._tables[table_name])

    def clear(self, table_name: str | None = None):
        """Clear one or all tables."""
        targets = [table_name] if table_name else list(self._tables.keys())
        for name in targets:
            if name in self._tables:
                self._tables[name] = pa.table(
                    {field.name: pa.array([], type=field.type) for field in self._schemas[name]}
                )
