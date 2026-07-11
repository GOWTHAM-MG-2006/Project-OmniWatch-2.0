import pytest
from performance.async_processor import AsyncProcessor


class TestAsyncProcessor:
    def test_queue_task(self):
        processor = AsyncProcessor()
        result = processor.queue_task("test_task", {"data": "value"})
        assert result is not None
        assert isinstance(result, str)

    def test_get_task_status(self):
        processor = AsyncProcessor()
        task_id = processor.queue_task("task1", {"data": "value"})
        status = processor.get_task_status(task_id)
        assert status is not None
        assert status["type"] == "task1"
        assert status["status"] in ("pending", "running", "completed", "failed")

    def test_get_queue_stats(self):
        processor = AsyncProcessor()
        stats = processor.get_queue_stats()
        assert "total" in stats
