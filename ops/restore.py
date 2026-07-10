"""
OmniWatch 2.0 — Operations
Component: Restore
Phase: 5
Purpose: Restore OmniWatch from backup
Inputs: Backup directory (from backup.py)
Outputs: Restored system state
Technology: Python, subprocess
"""

import json
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RestoreManager:
    """Restores OmniWatch from a backup."""

    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)

    def list_backups(self) -> list[dict[str, Any]]:
        """List available backups."""
        backups = []
        for d in sorted(self.backup_dir.iterdir()):
            if d.is_dir():
                manifest_path = d / "manifest.json"
                if manifest_path.exists():
                    manifest = json.loads(manifest_path.read_text())
                    backups.append(manifest)
        return backups

    def restore(self, timestamp: str) -> dict[str, Any]:
        """Restore from a specific backup.

        Args:
            timestamp: Backup timestamp (from manifest).

        Returns:
            Dict with restore results.
        """
        backup_path = self.backup_dir / timestamp
        if not backup_path.exists():
            return {"success": False, "error": f"Backup not found: {timestamp}"}

        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            return {"success": False, "error": "Invalid backup — no manifest"}

        manifest = json.loads(manifest_path.read_text())
        results = {}

        # 1. Restore ClickHouse schema
        results["clickhouse"] = self._restore_clickhouse_schema(backup_path)

        # 2. Restore Kuzu graph
        results["kuzu"] = self._restore_kuzu(backup_path)

        # 3. Restore OPA policies
        results["opa"] = self._restore_opa_policies(backup_path)

        # 4. Restore configuration
        results["config"] = self._restore_config(backup_path)

        success = all(r.get("success", False) for r in results.values())

        return {
            "success": success,
            "timestamp": timestamp,
            "restored_at": datetime.now(timezone.utc).isoformat(),
            "components": results,
        }

    def _restore_clickhouse_schema(self, backup_path: Path) -> dict[str, Any]:
        """Restore ClickHouse schema."""
        schema_src = backup_path / "clickhouse_schema.sql"
        schema_dst = Path("storage/schema.sql")
        if schema_src.exists():
            shutil.copy2(schema_src, schema_dst)
            return {"success": True, "file": str(schema_dst)}
        return {"success": False, "error": "No schema in backup"}

    def _restore_kuzu(self, backup_path: Path) -> dict[str, Any]:
        """Restore Kuzu graph database."""
        kuzu_src = backup_path / "kuzu_graph"
        kuzu_dst = Path("data/omniwatch-graph")
        if kuzu_src.exists():
            if kuzu_dst.exists():
                shutil.rmtree(kuzu_dst)
            shutil.copytree(kuzu_src, kuzu_dst)
            return {"success": True, "path": str(kuzu_dst)}
        return {"success": False, "error": "No Kuzu data in backup"}

    def _restore_opa_policies(self, backup_path: Path) -> dict[str, Any]:
        """Restore OPA policies."""
        policies_src = backup_path / "opa_policies"
        policies_dst = Path("remediation/policies")
        if policies_src.exists():
            if policies_dst.exists():
                shutil.rmtree(policies_dst)
            shutil.copytree(policies_src, policies_dst)
            return {"success": True, "path": str(policies_dst)}
        return {"success": False, "error": "No OPA policies in backup"}

    def _restore_config(self, backup_path: Path) -> dict[str, Any]:
        """Restore configuration files."""
        config_src = backup_path / "config"
        restored = []
        if config_src.exists():
            for f in config_src.iterdir():
                if f.is_file():
                    shutil.copy2(f, Path(f.name))
                    restored.append(f.name)
            return {"success": True, "files": restored}
        return {"success": False, "error": "No config in backup"}
