import pytest

from integrations.library.cloud.aws_ec2 import AWSEC2Integration
from integrations.library.cloud.aws_eks import AWSEKSIntegration
from integrations.library.cloud.aws_rds import AWSRDSIntegration
from integrations.library.cloud.aws_lambda import AWSLambdaIntegration
from integrations.library.cloud.azure_vms import AzureVMsIntegration
from integrations.library.cloud.azure_aks import AzureAKSIntegration
from integrations.library.cloud.gcp_gke import GCPGKEIntegration
from integrations.library.cloud.gcp_compute import GCPComputeIntegration


class TestAWSEC2:
    def test_collect_metrics(self):
        integration = AWSEC2Integration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert "name" in metrics[0]
        assert "value" in metrics[0]
        assert "timestamp" in metrics[0]
        assert "labels" in metrics[0]

    def test_health_check(self):
        integration = AWSEC2Integration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test"})
        assert integration.health_check() is True

    def test_health_check_missing_credentials(self):
        integration = AWSEC2Integration(config={})
        assert integration.health_check() is False


class TestAWSEKS:
    def test_collect_metrics(self):
        integration = AWSEKSIntegration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test", "AWS_EKS_CLUSTER": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_health_check(self):
        integration = AWSEKSIntegration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test", "AWS_EKS_CLUSTER": "test"})
        assert integration.health_check() is True


class TestAWSRDS:
    def test_collect_metrics(self):
        integration = AWSRDSIntegration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_health_check(self):
        integration = AWSRDSIntegration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test"})
        assert integration.health_check() is True


class TestAWSLambda:
    def test_collect_metrics(self):
        integration = AWSLambdaIntegration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_health_check(self):
        integration = AWSLambdaIntegration(config={"AWS_ACCESS_KEY": "test", "AWS_SECRET_KEY": "test"})
        assert integration.health_check() is True


class TestAzureVMs:
    def test_collect_metrics(self):
        integration = AzureVMsIntegration(config={"AZURE_TENANT_ID": "test", "AZURE_CLIENT_ID": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_health_check(self):
        integration = AzureVMsIntegration(config={"AZURE_TENANT_ID": "test", "AZURE_CLIENT_ID": "test"})
        assert integration.health_check() is True

    def test_health_check_missing_credentials(self):
        integration = AzureVMsIntegration(config={})
        assert integration.health_check() is False


class TestAzureAKS:
    def test_collect_metrics(self):
        integration = AzureAKSIntegration(config={"AZURE_TENANT_ID": "test", "AZURE_CLIENT_ID": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_health_check(self):
        integration = AzureAKSIntegration(config={"AZURE_TENANT_ID": "test", "AZURE_CLIENT_ID": "test"})
        assert integration.health_check() is True


class TestGCPGKE:
    def test_collect_metrics(self):
        integration = GCPGKEIntegration(config={"GCP_PROJECT_ID": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_health_check(self):
        integration = GCPGKEIntegration(config={"GCP_PROJECT_ID": "test"})
        assert integration.health_check() is True

    def test_health_check_missing_project(self):
        integration = GCPGKEIntegration(config={})
        assert integration.health_check() is False


class TestGCPCompute:
    def test_collect_metrics(self):
        integration = GCPComputeIntegration(config={"GCP_PROJECT_ID": "test"})
        metrics = integration.collect_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0

    def test_health_check(self):
        integration = GCPComputeIntegration(config={"GCP_PROJECT_ID": "test"})
        assert integration.health_check() is True
