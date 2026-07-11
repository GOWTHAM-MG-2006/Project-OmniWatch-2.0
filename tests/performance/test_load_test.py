import pytest
from performance.load_test_full import LoadTestSuite


class TestLoadTestSuite:
    def test_init(self):
        suite = LoadTestSuite()
        assert suite is not None

    def test_generate_report(self):
        suite = LoadTestSuite()
        suite.results = {"throughput": 10000, "latency_p99": 45}
        report = suite.generate_report()
        assert "Load Test Report" in report
