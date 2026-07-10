"""
OmniWatch 2.0 — NexusStore
Component: Bucket Setup (MinIO)
Layer: 4
Phase: 1
Purpose: Creates all required MinIO buckets for OmniWatch
Inputs: MinIO connection configuration
Outputs: 7 initialized buckets
"""

import logging

from storage.object_store import ObjectStore

logger = logging.getLogger(__name__)

# All required buckets from AGENTS.md
REQUIRED_BUCKETS = [
    ("omniwatch-telemetry-archive", "Aged telemetry > 90 days (Parquet)"),
    ("omniwatch-incidents", "Full incident JSON records"),
    ("omniwatch-audit-logs", "All remediation + drift action logs"),
    ("omniwatch-ml-datasets", "Historical data for model training"),
    ("omniwatch-runbooks", "Generated runbooks and playbooks"),
    ("omniwatch-compliance", "SOC2/ISO27001 evidence packages"),
    ("omniwatch-simulations", "SimulaX simulation results archive"),
]


def setup_buckets(store: ObjectStore | None = None) -> dict[str, bool]:
    """Create all required MinIO buckets. Returns status of each."""
    if store is None:
        store = ObjectStore()

    results = {}
    for bucket_name, description in REQUIRED_BUCKETS:
        success = store.create_bucket(bucket_name)
        results[bucket_name] = success
        if success:
            logger.info("Bucket ready: %s — %s", bucket_name, description)
        else:
            logger.error("Failed to create bucket: %s", bucket_name)

    created = sum(1 for v in results.values() if v)
    total = len(REQUIRED_BUCKETS)
    logger.info("Bucket setup complete: %d/%d created", created, total)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = setup_buckets()
    for bucket, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {bucket}")
