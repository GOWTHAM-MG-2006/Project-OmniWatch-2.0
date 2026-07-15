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

from config import config

logger = logging.getLogger(__name__)

try:
    from confluent_kafka import Producer
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False


class CloudAPIPoller:
    """Polls cloud provider APIs for metrics and cost data."""

    def __init__(self, kafka_bootstrap: str | None = None):
        self.kafka_bootstrap = kafka_bootstrap or config.KAFKA_BOOTSTRAP_SERVERS
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
            subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID", "")
            resource_group = os.getenv("AZURE_RESOURCE_GROUP", "default")
            client = MonitorClient(credential, subscription_id)

            resource_uri = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines"
            metric_names = ["Percentage CPU", "Available Memory Bytes"]

            for metric_name in metric_names:
                try:
                    metrics_data = client.metrics.list(
                        resource_uri=resource_uri,
                        metric_names=[metric_name],
                        aggregation="Average",
                        interval="PT5M"
                    )
                    for m in metrics_data:
                        if m.timeseries and len(m.timeseries) > 0 and m.timeseries[0].data:
                            latest = m.timeseries[0].data[-1]
                            metrics.append({
                                "source": "azure",
                                "metric": m.name,
                                "value": latest.average,
                                "timestamp": str(latest.time_stamp),
                            })
                except Exception as e:
                    logger.warning("Azure metric %s failed: %s", metric_name, e)

        except ImportError:
            logger.warning("azure-identity not installed — pip install azure-identity azure-monitor")
        except Exception as e:
            logger.warning("Azure Monitor polling failed: %s", e)

        return metrics

    def poll_gcp_monitoring(self) -> list[dict[str, Any]]:
        """Poll GCP Cloud Monitoring for GCE, GKE metrics."""
        metrics = []
        try:
            from google.cloud import monitoring_v3
            client = monitoring_v3.MetricServiceClient()
            project_id = os.getenv("GCP_PROJECT_ID", "")
            project_name = f"projects/{project_id}"

            interval = monitoring_v3.TimeInterval()
            results = client.list_time_series(
                request={
                    "name": project_name,
                    "filter": 'metric.type="compute.googleapis.com/instance/cpu/utilization"',
                    "interval": interval,
                }
            )
            for ts in results:
                if ts.points:
                    latest = ts.points[0]
                    metrics.append({
                        "source": "gcp",
                        "metric": ts.metric.type,
                        "value": latest.value.double_value,
                        "resource": ts.resource.labels.get("instance_id", "unknown"),
                        "timestamp": str(latest.interval.end_time),
                    })

        except ImportError:
            logger.warning("google-cloud-monitoring not installed — pip install google-cloud-monitoring")
        except Exception as e:
            logger.warning("GCP Monitoring polling failed: %s", e)

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
