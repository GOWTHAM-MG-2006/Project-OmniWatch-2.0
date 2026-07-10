"""
OmniWatch 2.0 — NexusStore
Component: Iceberg Table Manager
Layer: 4
Phase: 2
Purpose: Manages Apache Iceberg tables for time-travel queries and schema evolution
Inputs: Parquet files from parquet_writer
Outputs: Iceberg table metadata and query results
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try importing pyiceberg; fall back to mock if unavailable
try:
    from pyiceberg.catalog import Catalog
    from pyiceberg.schema import Schema
    from pyiceberg.types import (
        NestedField, StringType, LongType, DoubleType,
        BooleanType, TimestampType, MapType, ListType,
    )
    from pyiceberg.partitioning import PartitionSpec
    from pyiceberg.manifest import ManifestFile
    HAS_PYICEBERG = True
except ImportError:
    HAS_PYICEBERG = False
    logger.info("pyiceberg not installed — using MockIcebergManager")

import pyarrow as pa
import pyarrow.parquet as pq


# ---------------------------------------------------------------------------
# Iceberg type mapping (PyArrow → Iceberg)
# ---------------------------------------------------------------------------

_PYARROW_TO_ICEBERG: dict[pa.DataType, Any] = {
    pa.string(): StringType() if HAS_PYICEBERG else "string",
    pa.int64(): LongType() if HAS_PYICEBERG else "long",
    pa.int32(): LongType() if HAS_PYICEBERG else "long",
    pa.float64(): DoubleType() if HAS_PYICEBERG else "double",
    pa.float32(): DoubleType() if HAS_PYICEBERG else "double",
    pa.bool_(): BooleanType() if HAS_PYICEBERG else "boolean",
    pa.timestamp("us"): TimestampType() if HAS_PYICEBERG else "timestamp",
}


def _pyarrow_to_iceberg_schema(table: pa.Table) -> "Schema | dict[str, str]":
    """Convert a PyArrow table schema to an Iceberg schema."""
    if not HAS_PYICEBERG:
        return {field.name: str(field.type) for field in table.schema}

    fields = []
    for i, field in enumerate(table.schema):
        iceberg_type = _PYARROW_TO_ICEBERG.get(field.type, StringType())
        fields.append(NestedField(
            field_id=i + 1,
            name=field.name,
            field_type=iceberg_type,
            required=not field.nullable,
        ))
    return Schema(*fields)


# ---------------------------------------------------------------------------
# MockIcebergManager — filesystem-based fallback
# ---------------------------------------------------------------------------


class MockIcebergManager:
    """Filesystem-based fallback when pyiceberg is not installed.

    Stores Parquet files and metadata JSON to simulate Iceberg tables.
    Supports basic snapshot tracking for time-travel queries.
    """

    def __init__(self, warehouse_dir: str | None = None):
        self.warehouse = Path(warehouse_dir or os.getenv(
            "ICEBERG_WAREHOUSE", "/tmp/omniwatch-iceberg"
        ))
        self.warehouse.mkdir(parents=True, exist_ok=True)
        self._tables: dict[str, dict[str, Any]] = {}
        self._load_metadata()

    def _metadata_path(self, table_name: str) -> Path:
        return self.warehouse / table_name / "metadata.json"

    def _data_dir(self, table_name: str) -> Path:
        d = self.warehouse / table_name / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _load_metadata(self) -> None:
        """Load table metadata from filesystem."""
        for table_dir in self.warehouse.iterdir():
            if table_dir.is_dir():
                meta_path = table_dir / "metadata.json"
                if meta_path.exists():
                    with open(meta_path) as f:
                        self._tables[table_dir.name] = json.load(f)

    def _save_metadata(self, table_name: str) -> None:
        """Persist table metadata to filesystem."""
        meta_path = self._metadata_path(table_name)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, "w") as f:
            json.dump(self._tables[table_name], f, indent=2, default=str)

    def create_table(self, table_name: str, schema: pa.Schema | dict[str, str]) -> dict[str, Any]:
        """Create a new Iceberg table (mock: creates directory + metadata)."""
        if table_name in self._tables:
            raise ValueError(f"Table '{table_name}' already exists")

        if isinstance(schema, pa.Schema):
            columns = {field.name: str(field.type) for field in schema}
        else:
            columns = dict(schema)

        snapshot_id = int(datetime.utcnow().timestamp() * 1000)
        self._tables[table_name] = {
            "table_name": table_name,
            "columns": columns,
            "snapshots": [{
                "snapshot_id": snapshot_id,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {"operation": "create"},
                "manifest_list": [],
            }],
            "current_snapshot_id": snapshot_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._save_metadata(table_name)
        logger.info("Created table '%s' with %d columns", table_name, len(columns))
        return self._tables[table_name]

    def write_data(self, table_name: str, data: pa.Table | list[dict[str, Any]]) -> dict[str, Any]:
        """Write Parquet data to an Iceberg table (mock: writes Parquet + updates metadata)."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' does not exist")

        if isinstance(data, list):
            table = pa.Table.from_pylist(data)
        else:
            table = data

        snapshot_id = int(datetime.utcnow().timestamp() * 1000)
        filename = f"snap_{snapshot_id}.parquet"
        parquet_path = self._data_dir(table_name) / filename
        pq.write_table(table, parquet_path)

        meta = self._tables[table_name]
        meta["snapshots"].append({
            "snapshot_id": snapshot_id,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "operation": "append",
                "added-rows": str(len(table)),
            },
            "manifest_list": [filename],
        })
        meta["current_snapshot_id"] = snapshot_id
        self._save_metadata(table_name)
        logger.info("Wrote %d rows to table '%s' (snapshot %d)", len(table), table_name, snapshot_id)
        return {"snapshot_id": snapshot_id, "rows_written": len(table)}

    def read_data(
        self, table_name: str, snapshot_id: int | None = None
    ) -> pa.Table | None:
        """Read data from an Iceberg table. Supports time-travel by snapshot_id."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' does not exist")

        meta = self._tables[table_name]
        if snapshot_id is None:
            snapshot_id = meta["current_snapshot_id"]

        target = None
        for snap in meta["snapshots"]:
            if snap["snapshot_id"] == snapshot_id:
                target = snap
                break

        if target is None:
            logger.warning("Snapshot %d not found for table '%s'", snapshot_id, table_name)
            return None

        parquet_files = target.get("manifest_list", [])
        if not parquet_files:
            return pa.table({})

        tables = []
        data_dir = self._data_dir(table_name)
        for fname in parquet_files:
            p = data_dir / fname
            if p.exists():
                tables.append(pq.read_table(p))

        if not tables:
            return pa.table({})
        return pa.concat_tables(tables)

    def list_snapshots(self, table_name: str) -> list[dict[str, Any]]:
        """List all snapshots for a table."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        return self._tables[table_name]["snapshots"]

    def get_table_schema(self, table_name: str) -> dict[str, str]:
        """Return the column-name → type mapping for a table."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        return self._tables[table_name]["columns"]

    def drop_table(self, table_name: str) -> bool:
        """Drop a table and remove its data."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' does not exist")

        import shutil
        table_dir = self.warehouse / table_name
        if table_dir.exists():
            shutil.rmtree(table_dir)
        del self._tables[table_name]
        logger.info("Dropped table '%s'", table_name)
        return True

    def list_tables(self) -> list[str]:
        """List all table names."""
        return list(self._tables.keys())


# ---------------------------------------------------------------------------
# IcebergManager — real pyiceberg implementation
# ---------------------------------------------------------------------------


class IcebergManager:
    """Apache Iceberg table manager for cold storage tier.

    Provides time-travel queries, schema evolution, and snapshot management.
    Falls back to MockIcebergManager when pyiceberg is not installed.
    """

    def __init__(self, warehouse_dir: str | None = None, catalog_uri: str | None = None):
        self.warehouse = warehouse_dir or os.getenv(
            "ICEBERG_WAREHOUSE", "/tmp/omniwatch-iceberg"
        )
        self.catalog_uri = catalog_uri or os.getenv("ICEBERG_CATALOG_URI", "")
        self._catalog: Catalog | None = None
        self._mock: MockIcebergManager | None = None

        if not HAS_PYICEBERG:
            logger.warning("pyiceberg unavailable — using MockIcebergManager")
            self._mock = MockIcebergManager(self.warehouse)
            return

        try:
            self._init_catalog()
        except Exception as e:
            logger.warning("Failed to initialize Iceberg catalog (%s), using mock", e)
            self._mock = MockIcebergManager(self.warehouse)

    def _init_catalog(self) -> None:
        """Initialize the Iceberg catalog (REST, Hive, or filesystem)."""
        from pyiceberg.catalog import load_catalog

        if self.catalog_uri:
            self._catalog = load_catalog("rest", uri=self.catalog_uri)
        else:
            # Filesystem catalog — uses local warehouse directory
            config = {
                "catalog-type": "hive",
                "warehouse": self.warehouse,
            }
            self._catalog = load_catalog("hive", **config)

    def create_table(self, table_name: str, schema: pa.Schema | dict[str, str]) -> dict[str, Any]:
        """Create a new Iceberg table with the given schema.

        Args:
            table_name: Qualified table name (e.g. "omniwatch.metrics").
            schema: PyArrow schema or {column_name: type_string} dict.

        Returns:
            Dict with table metadata.
        """
        if self._mock:
            return self._mock.create_table(table_name, schema)

        iceberg_schema = _pyarrow_to_iceberg_schema(
            pa.schema([(k, pa.string()) for k, v in schema.items()]) if isinstance(schema, dict) else schema
        )

        try:
            table = self._catalog.create_table(
                identifier=table_name,
                schema=iceberg_schema,
            )
            logger.info("Created Iceberg table '%s'", table_name)
            return {"table_name": table_name, "location": str(table.location)}
        except Exception as e:
            logger.error("Failed to create table '%s': %s", table_name, e)
            raise

    def write_data(self, table_name: str, data: pa.Table | list[dict[str, Any]]) -> dict[str, Any]:
        """Write Parquet data to an Iceberg table.

        Args:
            table_name: Table to write to.
            data: PyArrow Table or list of dicts.

        Returns:
            Dict with snapshot_id and rows_written.
        """
        if self._mock:
            return self._mock.write_data(table_name, data)

        if isinstance(data, list):
            table = pa.Table.from_pylist(data)
        else:
            table = data

        try:
            iceberg_table = self._catalog.load_table(table_name)
            iceberg_table.append(table)
            snapshot_id = iceberg_table.current_snapshot().snapshot_id if iceberg_table.current_snapshot() else 0
            logger.info("Wrote %d rows to '%s' (snapshot %s)", len(table), table_name, snapshot_id)
            return {"snapshot_id": snapshot_id, "rows_written": len(table)}
        except Exception as e:
            logger.error("Failed to write to table '%s': %s", table_name, e)
            raise

    def read_data(
        self, table_name: str, snapshot_id: int | None = None
    ) -> pa.Table | None:
        """Read data from an Iceberg table with optional time-travel.

        Args:
            table_name: Table to read from.
            snapshot_id: If provided, read from this specific snapshot.

        Returns:
            PyArrow Table, or None if snapshot not found.
        """
        if self._mock:
            return self._mock.read_data(table_name, snapshot_id)

        try:
            iceberg_table = self._catalog.load_table(table_name)
            if snapshot_id:
                scan = iceberg_table.scan().use_ref(str(snapshot_id))
            else:
                scan = iceberg_table.scan()
            return scan.to_arrow()
        except Exception as e:
            logger.error("Failed to read from table '%s': %s", table_name, e)
            return None

    def list_snapshots(self, table_name: str) -> list[dict[str, Any]]:
        """List all snapshots for a table.

        Args:
            table_name: Table to inspect.

        Returns:
            List of snapshot metadata dicts.
        """
        if self._mock:
            return self._mock.list_snapshots(table_name)

        try:
            iceberg_table = self._catalog.load_table(table_name)
            snapshots = []
            for snap in iceberg_table.metadata.snapshots():
                snapshots.append({
                    "snapshot_id": snap.snapshot_id,
                    "timestamp": str(snap.manifest_list),
                    "summary": snap.summary or {},
                })
            return snapshots
        except Exception as e:
            logger.error("Failed to list snapshots for '%s': %s", table_name, e)
            return []

    def get_table_schema(self, table_name: str) -> dict[str, str]:
        """Return the current schema for a table.

        Args:
            table_name: Table to inspect.

        Returns:
            Dict mapping column names to type strings.
        """
        if self._mock:
            return self._mock.get_table_schema(table_name)

        try:
            iceberg_table = self._catalog.load_table(table_name)
            schema = iceberg_table.schema()
            return {field.name: str(field.field_type) for field in schema.fields}
        except Exception as e:
            logger.error("Failed to get schema for '%s': %s", table_name, e)
            return {}

    def drop_table(self, table_name: str) -> bool:
        """Drop a table and all its data.

        Args:
            table_name: Table to drop.

        Returns:
            True on success.
        """
        if self._mock:
            return self._mock.drop_table(table_name)

        try:
            self._catalog.drop_table(table_name)
            logger.info("Dropped Iceberg table '%s'", table_name)
            return True
        except Exception as e:
            logger.error("Failed to drop table '%s': %s", table_name, e)
            return False

    def list_tables(self) -> list[str]:
        """List all table names in the catalog.

        Returns:
            List of table identifier strings.
        """
        if self._mock:
            return self._mock.list_tables()

        try:
            return self._catalog.list_tables("omniwatch")
        except Exception as e:
            logger.error("Failed to list tables: %s", e)
            return []
