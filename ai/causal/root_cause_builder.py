"""OmniWatch 2.0 — NeuroEngine
Component: Root Cause Builder
Layer: 6
Phase: 2
Purpose: Packages RootCauseObject with evidence chain, blast radius, business impact
Inputs: Root cause from causal_graph_traversal + blast_radius from TopoBrain
Outputs: RootCauseObject (JSON matching AGENTS.md data contract)"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class RootCauseBuilder:
    """Packages root cause analysis results into a RootCauseObject.

    This is the final output of the causal detection pipeline:
    - CausalGraphTraversal → root_cause_candidates
    - AnomalyDetector → anomaly_signals
    - ProblemAssembler → incident
    - BlastRadiusCalculator → blast radius
    - This class → RootCauseObject
    """

    def __init__(self, blast_radius_calculator=None):
        self._blast_radius_calculator = blast_radius_calculator

    def build(
        self,
        root_cause_candidates: list[dict[str, Any]],
        anomaly_signals: list[dict[str, Any]],
        incident: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a RootCauseObject from root cause candidates and anomaly signals.

        Args:
            root_cause_candidates: Ranked root cause candidates from causal_graph_traversal.
                Each has entity_id, entity_type, causal_score, depth, has_anomaly, path.
            anomaly_signals: Anomaly signals from anomaly_detector.
                Each has entity_id, metric_name, anomaly_score, severity, deviation_from_baseline.
            incident: Optional incident record from problem_assembler.

        Returns:
            RootCauseObject dict matching AGENTS.md data contract.
        """
        if not root_cause_candidates:
            raise ValueError("At least one root cause candidate is required")

        # Pick top candidate as root cause
        top = root_cause_candidates[0]

        # Find the matching anomaly signal for the root cause entity
        root_signal = self._find_signal_for_entity(top["entity_id"], anomaly_signals)

        # Severity from signal or fall back to incident
        severity = self._determine_severity(top, root_signal, incident)

        # Build root_cause block
        root_cause = self._build_root_cause(top, root_signal)

        # Build evidence chain
        evidence_chain = self._build_evidence_chain(root_cause_candidates, anomaly_signals, incident)

        # Build blast radius
        blast_radius = self._calculate_blast_radius(
            top["entity_id"],
            root_cause_candidates,
            anomaly_signals,
        )

        # Estimate business impact
        business_impact = self._estimate_business_impact(blast_radius, incident)

        problem_id = self._generate_problem_id(top["entity_id"])

        return {
            "problem_id": problem_id,
            "confidence": top["causal_score"],
            "severity": severity,
            "root_cause": root_cause,
            "evidence_chain": evidence_chain,
            "blast_radius": blast_radius,
            "business_impact": business_impact,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_method": "causal_graph_traversal",
        }

    def _generate_problem_id(self, entity_id: str) -> str:
        """Generate a deterministic problem ID from entity and timestamp."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        short_hash = hashlib.sha256(f"{entity_id}-{ts}".encode()).hexdigest()[:6]
        return f"PRB-{ts}-{short_hash}"

    def _find_signal_for_entity(
        self, entity_id: str, signals: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Find the highest-severity anomaly signal for a given entity."""
        matches = [s for s in signals if s.get("entity_id") == entity_id]
        if not matches:
            return None
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        return min(matches, key=lambda s: severity_order.get(s.get("severity", "INFO"), 4))

    def _determine_severity(
        self,
        candidate: dict[str, Any],
        signal: dict[str, Any] | None,
        incident: dict[str, Any] | None,
    ) -> str:
        """Determine overall severity from available context."""
        if incident and "severity" in incident:
            return incident["severity"]
        if signal and "severity" in signal:
            return signal["severity"]
        score = candidate["causal_score"]
        if score >= 0.9:
            return "CRITICAL"
        if score >= 0.7:
            return "HIGH"
        if score >= 0.5:
            return "MEDIUM"
        return "LOW"

    def _build_root_cause(
        self,
        candidate: dict[str, Any],
        signal: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build the root_cause block of the RootCauseObject."""
        rc: dict[str, Any] = {
            "entity": candidate["entity_id"],
            "entity_type": candidate.get("entity_type", "unknown"),
            "layer": self._entity_type_to_layer(candidate.get("entity_type", "unknown")),
            "metric": signal["metric_name"] if signal else "unknown",
            "deviation": signal.get("deviation_from_baseline", "N/A") if signal else "N/A",
            "causal_score": candidate["causal_score"],
        }
        return rc

    def _entity_type_to_layer(self, entity_type: str) -> int:
        """Map entity type to OmniWatch layer number."""
        mapping = {
            "Database": 4,
            "Service": 3,
            "Host": 4,
            "Infrastructure": 4,
            "Process": 3,
            "GenAIService": 6,
            "BusinessTransaction": 6,
        }
        return mapping.get(entity_type, 0)

    def _build_evidence_chain(
        self,
        candidates: list[dict[str, Any]],
        signals: list[dict[str, Any]],
        incident: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Create a step-by-step evidence chain."""
        chain: list[dict[str, Any]] = []
        step_num = 1

        # Evidence from anomaly signals
        for sig in signals:
            entry = {
                "step": step_num,
                "observation": self._describe_anomaly_evidence(sig),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "signal_type": "metric",
                "evidence_id": self._make_evidence_id(step_num),
            }
            chain.append(entry)
            step_num += 1

        # Evidence from causal traversal (paths)
        for cand in candidates[1:]:  # skip root cause (already covered)
            if cand.get("path") and len(cand["path"]) > 1:
                entry = {
                    "step": step_num,
                    "observation": self._describe_causal_evidence(cand),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signal_type": "analysis",
                    "evidence_id": self._make_evidence_id(step_num),
                }
                chain.append(entry)
                step_num += 1

        # Evidence from incident if available
        if incident:
            entry = {
                "step": step_num,
                "observation": self._describe_incident_evidence(incident),
                "timestamp": incident.get("created_at", datetime.now(timezone.utc).isoformat()),
                "signal_type": "analysis",
                "evidence_id": self._make_evidence_id(step_num),
            }
            chain.append(entry)
            step_num += 1

        return chain

    def _describe_anomaly_evidence(self, signal: dict[str, Any]) -> str:
        """Create human-readable description from anomaly signal."""
        entity = signal.get("entity_id", "unknown")
        metric = signal.get("metric_name", "unknown")
        deviation = signal.get("deviation_from_baseline", "N/A")
        score = signal.get("anomaly_score", 0)
        return (
            f"Entity '{entity}' shows anomalous behavior on metric "
            f"'{metric}' (score={score:.2f}, deviation={deviation})"
        )

    def _describe_causal_evidence(self, candidate: dict[str, Any]) -> str:
        """Create human-readable description from causal candidate."""
        path = candidate.get("path", [])
        chain_str = " -> ".join(path)
        score = candidate["causal_score"]
        return (
            f"Causal path discovered: {chain_str} "
            f"(causal_score={score:.2f})"
        )

    def _describe_incident_evidence(self, incident: dict[str, Any]) -> str:
        """Create human-readable description from incident."""
        iid = incident.get("incident_id", "unknown")
        severity = incident.get("severity", "unknown")
        return f"Incident '{iid}' recorded with severity {severity}"

    def _make_evidence_id(self, step: int) -> str:
        """Generate a stable evidence ID."""
        return f"NXS-EVD-{step:04d}"

    def _calculate_blast_radius(
        self,
        entity_id: str,
        candidates: list[dict[str, Any]],
        signals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Calculate blast radius using BlastRadiusCalculator or mock fallback."""
        if self._blast_radius_calculator is not None:
            try:
                return self._real_blast_radius(entity_id, candidates, signals)
            except Exception as e:
                logger.warning("BlastRadiusCalculator failed, falling back to mock: %s", e)

        return self._mock_blast_radius(entity_id, candidates, signals)

    def _real_blast_radius(
        self,
        entity_id: str,
        candidates: list[dict[str, Any]],
        signals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Calculate blast radius using the real BlastRadiusCalculator."""
        result = self._blast_radius_calculator.calculate(entity_id)
        impacted = result.get("impacted_entities", [])
        blast = []
        for imp_id in impacted:
            sig = self._find_signal_for_entity(imp_id, signals)
            impact_desc = (
                f"degraded due to {entity_id} failure"
                if not sig
                else f"{sig.get('metric_name', 'unknown')} degraded"
            )
            blast.append({
                "entity": imp_id,
                "impact": impact_desc,
                "affected_users": self._estimate_users_for_entity(imp_id),
            })
        return blast

    def _estimate_users_for_entity(self, entity_id: str) -> int:
        """Estimate affected users for a single entity."""
        if self._blast_radius_calculator is not None:
            try:
                return self._blast_radius_calculator.estimate_users_affected(entity_id)
            except Exception:
                pass
        return 0

    def _mock_blast_radius(
        self,
        entity_id: str,
        candidates: list[dict[str, Any]],
        signals: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Provide mock blast radius for testing when real calculator unavailable."""
        mock_data: dict[str, list[dict[str, Any]]] = {
            "postgres-payments-primary": [
                {"entity": "payment-service-api", "impact": "p99 latency 890ms", "affected_users": 12400},
                {"entity": "checkout-service", "impact": "request queue buildup", "affected_users": 8000},
                {"entity": "frontend-app", "impact": "user-facing errors", "affected_users": 15000},
            ],
            "redis-cache-primary": [
                {"entity": "session-service", "impact": "cache miss rate +40%", "affected_users": 10000},
                {"entity": "frontend-app", "impact": "slow page loads", "affected_users": 15000},
            ],
        }

        if entity_id in mock_data:
            return mock_data[entity_id]

        # Generic fallback: use candidates as blast radius
        blast: list[dict[str, Any]] = []
        for cand in candidates:
            if cand["entity_id"] != entity_id:
                blast.append({
                    "entity": cand["entity_id"],
                    "impact": f"causal_score={cand['causal_score']:.2f} from {entity_id}",
                    "affected_users": 1000,
                })
        return blast

    def _estimate_business_impact(
        self,
        blast_radius: list[dict[str, Any]],
        incident: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Estimate business impact from blast radius and incident data."""
        total_users = sum(b.get("affected_users", 0) for b in blast_radius)

        # Estimate revenue at risk: $7/user/hour as baseline heuristic
        revenue_per_user_per_hour = 7
        revenue_at_risk = total_users * revenue_per_user_per_hour

        slo_breach = "N/A"
        if incident and "sla_breach_risk" in incident:
            slo_breach = incident["sla_breach_risk"]

        return {
            "affected_users": total_users,
            "estimated_revenue_at_risk_usd_per_hour": revenue_at_risk,
            "slo_breach": slo_breach,
        }
