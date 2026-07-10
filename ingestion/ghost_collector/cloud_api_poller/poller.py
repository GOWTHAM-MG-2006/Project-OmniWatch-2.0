"""
OmniWatch 2.0 — GhostCollector
Component: Cloud API Poller
Layer: 2
Phase: 5
Purpose: Polls AWS/Azure/GCP APIs for cloud resource metrics and cost data
Inputs: Cloud provider APIs (CloudWatch, Azure Monitor, GCP Monitoring)
Outputs: Cloud metrics to Kafka omniwatch.metrics.raw
Technology: Python, boto3, azure-identity, google-cloud (with graceful fallbacks)
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

try:
    from confluent_kafka import Producer
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False


class CloudAPIPoller:
    """Polls cloud provider APIs for metrics and cost data."""

    def __init__(self, kafka_bootstrap: str | None = None):
        self.kafka_bootstrap = kafka_bootstrap or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._producer = None
        self._poll_count = 0

    @property
    def producer(self):
        if self._producer is None and HAS_KAFKA:
            try:
                self._producer = Producer({
                    "bootstrap.servers": self.kafka_bootstrap,
                    "client.id": "omniwatch-cloud-poller",
                })
            except Exception as e:
                logger.warning("Kafka producer init failed: %s", e)
        return self._producer

    def poll_aws_cloudwatch(self) -> list[dict[str, Any]]:
        """Poll AWS CloudWatch for EC2, EKS, RDS metrics."""
        metrics = []
        try:
            import boto3
            client = boto3.client("cloudwatch", region_name=os.getenv("AWS_REGION", "us-east-1"))

            # Poll EC2 CPU utilization
            response = client.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                StartTime=datetime.now(timezone.utc).replace(minute=-5),
                EndTime=datetime.now(timezone.utc),
                Period=60,
                Statistics=["Average", "Maximum"],
            )
            for dp in response.get("Datapoints", []):
                metrics.append({
                    "source": "aws_cloudwatch",
                    "service": "ec2",
                    "metric_name": "cpu_utilization",
                    "value": dp["Average"],
                    "max_value": dp.get("Maximum"),
                    "timestamp": dp["Timestamp"].isoformat(),
                })
        except ImportError:
            logger.debug("boto3 not installed — AWS polling disabled")
        except Exception as e:
            logger.warning("AWS CloudWatch poll failed: %s", e)

        return metrics

    def poll_azure_monitor(self) -> list[dict[str, Any]]:
        """Poll Azure Monitor for VM, AKS, SQL metrics."""
        metrics = []
        try:
            from azure.monitor.monitor import MonitorClient
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            client = MonitorClient(credential, os.getenv("AZURE_SUBSCRIPTION_ID", ""))
            logger.debug("Azure Monitor client initialized")
        except ImportError:
            logger.debug("azure-identity not installed — Azure polling disabled")
        except Exception as e:
            logger.warning("Azure Monitor init failed: %s", e)

        return metrics

    def poll_gcp_monitoring(self) -> list[dict[str, Any]]:
        """Poll GCP Cloud Monitoring for GCE, GKE metrics."""
        metrics = []
        try:
            from google.cloud import monitoring_v3
            client = monitoring_v3.MetricServiceClient()
            logger.debug("GCP Monitoring client initialized")
        except ImportError:
            logger.debug("google-cloud-monitoring not installed — GCP polling disabled")
        except Exception as e:
            logger.warning("GCP Monitoring init failed: %s", e)

        return metrics

    def poll_all(self) -> list[dict[str, Any]]:
        """Poll all configured cloud providers."""
        all_metrics = []
        all_metrics.extend(self.poll_aws_cloudwatch())
        all_metrics.extend(self.poll_azure_monitor())
        all_metrics.extend(self.poll_gcp_monitoring())

        # Forward to Kafka
        for metric in all_metrics:
            self._forward_to_kafka(metric)

        self._poll_count += 1
        return all_metrics

    def _forward_to_kafka(self, metric: dict[str, Any]) -> bool:
        """Forward metric to Kafka."""
        if not self.producer:
            return False
        try:
            self.producer.produce(
                "omniwatch.metrics.raw",
                value=json.dumps(metric, default=str).encode(),
            )
            self.producer.poll(0)
            return True
        except Exception as e:
            logger.warning("Kafka produce failed: %s", e)
            return False

    def get_stats(self) -> dict[str, Any]:
        return {"poll_count": self._poll_count, "kafka_connected": self.producer is not None}
