"""
OmniWatch 2.0 — Continuous Learning
Component: Feedback Loop Processor
Layer: 10
Phase: 4
Purpose: Evaluates remediation outcomes and writes learning records to knowledge base
Input: ActionResult from AutoHeal + IncidentRecord
Output: Learning record in knowledge_base
Technology: Python
"""

import logging
from datetime import datetime, timezone
from typing import Any

from learning.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """Evaluates remediation outcomes and feeds results to the knowledge base."""

    def __init__(self, kb: KnowledgeBase | None = None):
        self.kb = kb or KnowledgeBase()

    def process_outcome(
        self,
        incident: dict[str, Any],
        action_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a remediation outcome and store it in the knowledge base.

        Args:
            incident: IncidentRecord dict.
            action_result: ActionResult dict from remediation_engine.

        Returns:
            Learning record dict with evaluation metrics.
        """
        success = action_result.get("success", False)
        action_type = action_result.get("action_type", "unknown")
        execution_time = action_result.get("execution_time_seconds", 0)
        severity = incident.get("severity", "P4")

        # Evaluate outcome quality
        evaluation = self._evaluate_outcome(incident, action_result)

        # Store in knowledge base
        entry_id = self.kb.store_incident_outcome(
            incident=incident,
            action_result=action_result,
            resolution_notes=evaluation.get("notes", ""),
        )

        learning_record = {
            "entry_id": entry_id,
            "incident_id": incident.get("incident_id", ""),
            "action_type": action_type,
            "success": success,
            "severity": severity,
            "execution_time_seconds": execution_time,
            "evaluation": evaluation,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "Feedback processed: incident=%s action=%s success=%s",
            incident.get("incident_id", "?"), action_type, success,
        )
        return learning_record

    def _evaluate_outcome(
        self, incident: dict[str, Any], action_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate the quality of a remediation outcome.

        Returns:
            Dict with score (0-1), grade (A-F), and notes.
        """
        success = action_result.get("success", False)
        execution_time = action_result.get("execution_time_seconds", 0)
        severity = incident.get("severity", "P4")

        score = 0.5  # baseline
        notes = []

        if success:
            score += 0.3
            notes.append("Action executed successfully")
        else:
            score -= 0.3
            notes.append(f"Action failed: {action_result.get('error', 'unknown')}")

        # Fast execution is better
        if execution_time < 30:
            score += 0.1
            notes.append("Fast execution (< 30s)")
        elif execution_time > 300:
            score -= 0.1
            notes.append("Slow execution (> 5min)")

        # P1/P2 success is more valuable
        if severity in ("P1", "P2") and success:
            score += 0.1
            notes.append(f"High-severity ({severity}) resolved")

        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            grade = "A"
        elif score >= 0.6:
            grade = "B"
        elif score >= 0.4:
            grade = "C"
        elif score >= 0.2:
            grade = "D"
        else:
            grade = "F"

        return {"score": round(score, 2), "grade": grade, "notes": "; ".join(notes)}
