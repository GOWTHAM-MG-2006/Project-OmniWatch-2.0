"""
OmniWatch 2.0 — NexusStore
Component: Object Store (MinIO/S3)
Layer: 4
Phase: 1
Purpose: S3-compatible object storage for runbooks, ML datasets, compliance evidence
Inputs: Generated reports, archived telemetry, ML training data
Outputs: Stored objects, retrieval API
"""

import os
import json
import logging
from io import BytesIO
from typing import Any

from minio import Minio
from minio.error import S3Error

from config import config

logger = logging.getLogger(__name__)


class ObjectStore:
    """MinIO/S3-compatible object storage client."""

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool = False,
    ):
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.environ.get("MINIO_ACCESS_KEY")
        self.secret_key = secret_key or os.environ.get("MINIO_SECRET_KEY")
        if not self.access_key or not self.secret_key:
            raise ValueError("MINIO_ACCESS_KEY and MINIO_SECRET_KEY environment variables are required")
        self.secure = secure or os.getenv("MINIO_SECURE", "false").lower() == "true"
        self._client = None

    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
        return self._client

    def upload(
        self,
        bucket: str,
        object_name: str,
        data: bytes | str,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """Upload data to a bucket."""
        if isinstance(data, str):
            data = data.encode("utf-8")

        try:
            self.client.put_object(
                bucket,
                object_name,
                BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            logger.info("Uploaded %s/%s (%d bytes)", bucket, object_name, len(data))
            return True
        except S3Error as e:
            logger.error("Failed to upload %s/%s: %s", bucket, object_name, e)
            return False

    def upload_json(self, bucket: str, object_name: str, data: Any) -> bool:
        """Upload JSON data to a bucket."""
        json_data = json.dumps(data, indent=2, default=str)
        return self.upload(bucket, object_name, json_data, "application/json")

    def download(self, bucket: str, object_name: str) -> bytes | None:
        """Download data from a bucket."""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info("Downloaded %s/%s (%d bytes)", bucket, object_name, len(data))
            return data
        except S3Error as e:
            logger.error("Failed to download %s/%s: %s", bucket, object_name, e)
            return None

    def download_json(self, bucket: str, object_name: str) -> Any | None:
        """Download and parse JSON from a bucket."""
        data = self.download(bucket, object_name)
        if data:
            return json.loads(data)
        return None

    def list_objects(self, bucket: str, prefix: str = "") -> list[dict[str, str]]:
        """List objects in a bucket with optional prefix."""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            result = []
            for obj in objects:
                result.append({
                    "name": obj.object_name,
                    "size": str(obj.size),
                    "last_modified": str(obj.last_modified),
                    "etag": obj.etag,
                })
            return result
        except S3Error as e:
            logger.error("Failed to list objects in %s: %s", bucket, e)
            return []

    def delete(self, bucket: str, object_name: str) -> bool:
        """Delete an object from a bucket."""
        try:
            self.client.remove_object(bucket, object_name)
            logger.info("Deleted %s/%s", bucket, object_name)
            return True
        except S3Error as e:
            logger.error("Failed to delete %s/%s: %s", bucket, object_name, e)
            return False

    def bucket_exists(self, bucket: str) -> bool:
        """Check if a bucket exists."""
        try:
            return self.client.bucket_exists(bucket)
        except S3Error:
            return False

    def create_bucket(self, bucket: str) -> bool:
        """Create a bucket if it doesn't exist."""
        try:
            if not self.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                logger.info("Created bucket: %s", bucket)
            return True
        except S3Error as e:
            logger.error("Failed to create bucket %s: %s", bucket, e)
            return False

    def health_check(self) -> bool:
        """Verify MinIO connectivity."""
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            logger.error("Object store health check failed: %s", e)
            return False
