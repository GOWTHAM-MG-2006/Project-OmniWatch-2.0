"""
OmniWatch 2.0 — Performance Testing
Component: Async Processor
Phase: 7
Purpose: Thread-pool based async processing with task queue,
         status tracking, PII sanitisation, and audit logging
Inputs: Background tasks, task configuration
Outputs: Task results, queue statistics
Technology: Python, concurrent.futures, threading
"""

import hashlib
import logging
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from typing import Any, Callable

from config import config

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class _TaskRecord:
    __slots__ = ("id", "type", "payload", "status", "result", "error",
                 "created_at", "started_at", "completed_at", "future")

    def __init__(self, task_id: str, task_type: str, payload: dict):
        self.id = task_id
        self.type = task_type
        self.payload = payload
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: str | None = None
        self.created_at = time.monotonic()
        self.started_at: float | None = None
        self.completed_at: float | None = None
        self.future: Future | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": (
                round((self.completed_at - self.started_at) * 1000, 2)
                if self.completed_at and self.started_at else None
            ),
        }


class AsyncProcessor:
    """ThreadPoolExecutor-based async processor with status tracking."""

    def __init__(self, max_workers: int = config.ASYNC_MAX_WORKERS):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="omniwatch-bg",
        )
        self._tasks: dict[str, _TaskRecord] = {}
        self._lock = __import__("threading").Lock()
        self._max_history = config.ASYNC_MAX_HISTORY

    def _track_result(self, task_id: str, future: Future) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return
            record.completed_at = time.monotonic()
            if future.exception():
                record.status = TaskStatus.FAILED
                record.error = str(future.exception())
                logger.error("Task %s (%s) failed: %s", task_id, record.type, record.error)
            else:
                record.status = TaskStatus.COMPLETED
                record.result = future.result()
                logger.debug("Task %s (%s) completed", task_id, record.type)
            self._trim_history()

    def _trim_history(self) -> None:
        if len(self._tasks) > self._max_history:
            terminal = [
                tid for tid, t in self._tasks.items()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            ]
            for tid in terminal[: len(terminal) - self._max_history // 2]:
                del self._tasks[tid]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def queue_task(self, task_type: str, payload: dict,
                   func: Callable | None = None) -> str:
        """Queue a background task. Returns the task ID."""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        record = _TaskRecord(task_id, task_type, payload)

        def _wrapper() -> Any:
            record.status = TaskStatus.RUNNING
            record.started_at = time.monotonic()
            if func is not None:
                return func(payload)
            # Default: echo payload (placeholder for real task logic)
            return {"processed": True, "task_type": task_type}

        future = self._executor.submit(_wrapper)
        record.future = future
        future.add_done_callback(lambda f: self._track_result(task_id, f))

        with self._lock:
            self._tasks[task_id] = record
        logger.debug("Queued task %s (%s)", task_id, task_type)
        return task_id

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get status and result of a task."""
        record = self._tasks.get(task_id)
        return record.to_dict() if record else None

    def get_queue_stats(self) -> dict[str, Any]:
        """Return aggregate queue statistics."""
        with self._lock:
            counts = {s: 0 for s in TaskStatus}
            for t in self._tasks.values():
                counts[t.status] += 1
        return {
            "total": len(self._tasks),
            "pending": counts[TaskStatus.PENDING],
            "running": counts[TaskStatus.RUNNING],
            "completed": counts[TaskStatus.COMPLETED],
            "failed": counts[TaskStatus.FAILED],
            "max_workers": self._executor._max_workers,
        }

    def process_queue(self) -> int:
        """Force-wait on all pending futures and return count of newly completed."""
        count = 0
        with self._lock:
            pending_ids = [
                tid for tid, t in self._tasks.items()
                if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING) and t.future
            ]
        for tid in pending_ids:
            record = self._tasks.get(tid)
            if record and record.future:
                try:
                    record.future.result(timeout=config.TASK_FUTURE_TIMEOUT)
                    count += 1
                except Exception:
                    count += 1
        return count

    def shutdown(self, wait: bool = True, timeout: float = 30) -> None:
        """Shut down the executor gracefully."""
        self._executor.shutdown(wait=wait, cancel_futures=not wait)
        logger.info("AsyncProcessor executor shut down")

    # ------------------------------------------------------------------
    # Convenience task helpers
    # ------------------------------------------------------------------

    def pii_async(self, text: str) -> str:
        """Synchronous PII masking helper (used inside queued tasks)."""
        import re
        masked = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", "[EMAIL]", text)
        masked = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE]", masked)
        masked = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", masked)
        return masked

    def queue_pii_async(self, text: str) -> str:
        """Queue a PII sanitisation task in the background."""
        def _mask(payload: dict) -> dict:
            return {"masked_text": self.pii_async(payload["text"])}
        return self.queue_task("pii_sanitise", {"text": text}, func=_mask)

    def queue_audit_async(self, action: str, entity: str,
                          details: dict | None = None) -> str:
        """Queue an audit log write in the background."""
        def _log(payload: dict) -> dict:
            entry = {
                "action": payload["action"],
                "entity": payload["entity"],
                "details": payload.get("details", {}),
                "logged_at": time.time(),
            }
            logger.info("AUDIT: %s", entry)
            return entry
        return self.queue_task("audit_log", {"action": action, "entity": entity, "details": details}, func=_log)
