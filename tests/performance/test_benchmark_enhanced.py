import pytest
from performance.benchmark_enhanced import EnhancedBenchmarkSuite


class TestEnhancedBenchmarkSuite:
    def test_run_benchmarks(self):
        suite = EnhancedBenchmarkSuite()
        result = suite.run_benchmarks()
        assert "timestamp" in result

    def test_detect_regressions(self):
        suite = EnhancedBenchmarkSuite()
        result = suite.detect_regressions()
        assert isinstance(result, list)

    def test_profile_resources(self):
        suite = EnhancedBenchmarkSuite()
        result = suite.profile_resources()
        assert "cpu_percent" in result
