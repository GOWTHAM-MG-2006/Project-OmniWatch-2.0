import pytest
from performance.async_processor import AsyncProcessor


class TestAsyncProcessor:
    def test_queue_task(self):
        processor = AsyncProcessor()
        result = processor.queue_task("test_task", {"data": "value"})
        assert result is True

    def test_get_task_status(self):
        processor = AsyncProcessor()
        # We queue a task and then retrieve it using its generated ID.
        # Since queue_task returns True but doesn't expose the ID,
        # we'll access the internal queue to get the ID.
        processor.queue_task("task1", {"data": "value"})
        task_id = processor._queue[0]["id"]
        status = processor.get_task_status(task_id)
        assert status is not None
        assert status["type"] == "task1"
        assert status["status"] == "pending"

    def test_get_queue_stats(self):
        processor = AsyncProcessor()
        stats = processor.get_queue_stats()
        assert "pending" in stats
