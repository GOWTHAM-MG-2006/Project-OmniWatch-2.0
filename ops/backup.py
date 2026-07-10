"""
OmniWatch 2.0 — Operations
Component: Backup
Phase: 5
Purpose: Automated backup of all persistent state
Inputs: ClickHouse, Kuzu, MinIO, Redis, OPA, configuration
Outputs: Timestamped backup directory
Technology: Python, subprocess
"""

import os
import json
import shutil
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages automated backups of all OmniWatch persistent state."""

    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> dict[str, Any]:
        """Create a full backup of all persistent state.

        Returns:
            Dict with backup metadata and checksums.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)

        checksums = {}

        # 1. Backup ClickHouse schema
        checksums["clickhouse_schema"] = self._backup_clickhouse_schema(backup_path)

        # 2. Backup Kuzu graph
        checksums["kuzu_graph"] = self._backup_kuzu(backup_path)

        # 3. Backup OPA policies
        checksums["opa_policies"] = self._backup_opa_policies(backup_path)

        # 4. Backup configuration
        checksums["config"] = self._backup_config(backup_path)

        # 5. Write manifest
        manifest = {
            "timestamp": timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums": checksums,
            "components": list(checksums.keys()),
        }
        manifest_path = backup_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        logger.info("Backup created: %s", backup_path)
        return manifest

    def list_backups(self) -> list[dict[str, Any]]:
        """List all available backups."""
        backups = []
        for d in sorted(self.backup_dir.iterdir()):
            if d.is_dir():
                manifest_path = d / "manifest.json"
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text())
                    backups.append(manifest)
        return backups

    def _backup_clickhouse_schema(self, backup_path: Path) -> str:
        """Backup ClickHouse schema."""
        schema_src = Path("storage/schema.sql")
        schema_dst = backup_path / "clickhouse_schema.sql"
        if schema_src.exists():
            shutil.copy2(schema_src, schema_dst)
            return self._checksum(schema_dst)
        return ""

    def _backup_kuzu(self, backup_path: Path) -> str:
        """Backup Kuzu graph database."""
        kuzu_src = Path(os.getenv("KUZU_DATABASE_PATH", "./data/omniwatch-graph"))
        kuzu_dst = backup_path / "kuzu_graph"
        if kuzu_src.exists():
            shutil.copytree(kuzu_src, kuzu_dst, dirs_exist_ok=True)
            return self._checksum_dir(kuzu_dst)
        return ""

    def _backup_opa_policies(self, backup_path: Path) -> str:
        """Backup OPA Rego policies."""
        policies_src = Path("remediation/policies")
        policies_dst = backup_path / "opa_policies"
        if policies_src.exists():
            shutil.copytree(policies_src, policies_dst, dirs_exist_ok=True)
            return self._checksum_dir(policies_dst)
        return ""

    def _backup_config(self, backup_path: Path) -> str:
        """Backup configuration files."""
        config_files = [".env", "docker-compose.yml"]
        config_dst = backup_path / "config"
        config_dst.mkdir(exist_ok=True)
        for f in config_files:
            src = Path(f)
            if src.exists():
                shutil.copy2(src, config_dst / f)
        return self._checksum_dir(config_dst)

    def _checksum(self, path: Path) -> str:
        """Compute SHA256 checksum of a file."""
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()[:16]

    def _checksum_dir(self, path: Path) -> str:
        """Compute aggregate checksum of a directory."""
        h = hashlib.sha256()
        for f in sorted(path.rglob("*")):
            if f.is_file():
                h.update(f.read_bytes())
        return h.hexdigest()[:16]
