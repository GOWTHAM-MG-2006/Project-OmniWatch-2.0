import pytest
from performance.load_test_full import LoadTestRunner


class TestLoadTestRunner:
    def test_init(self):
        runner = LoadTestRunner()
        assert runner is not None

    def test_init_with_url(self):
        runner = LoadTestRunner(base_url="http://localhost:8000")
        assert runner.base_url == "http://localhost:8000"
