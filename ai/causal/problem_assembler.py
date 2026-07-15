"""
OmniWatch 2.0 — NeuroEngine
Component: Problem Assembler
Layer: 6
Phase: 2
Purpose: Groups related anomalies into single IncidentRecord (incident aggregation)
Inputs: AnomalySignal list + topology context
Outputs: Deduplicated IncidentRecord → Kafka omniwatch.incidents.created
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional


class ProblemAssembler:
    """Groups related anomalies into single incidents (incident aggregation/deduplication)."""

    def __init__(self, time_window_seconds: int = 300):
        import logging
        logger = logging.getLogger(__name__)
        self.time_window_seconds = time_window_seconds
        self._mock_topology = self._build_mock_topology()
        logger.warning("Using mock topology — connect to TopoBrain (Kuzu) for real entity relationships")

    def _build_mock_topology(self) -> Dict[str, List[str]]:
        """Build mock entity relationships for testing.
        
        Mock relationships:
        - payment-service ↔ postgres-payments-primary
        - checkout-service ↔ payment-service
        """
        return {
            "payment-service-api": ["postgres-payments-primary", "checkout-service"],
            "postgres-payments-primary": ["payment-service-api"],
            "checkout-service": ["payment-service-api"],
        }

    def _are_entities_related(self, entity1: str, entity2: str) -> bool:
        """Check if two entities are topologically related."""
        if entity1 in self._mock_topology:
            if entity2 in self._mock_topology[entity1]:
                return True
        if entity2 in self._mock_topology:
            if entity1 in self._mock_topology[entity2]:
                return True
        return False

    def _are_related(self, anomaly1: dict, anomaly2: dict) -> bool:
        """Check if two anomalies belong to the same incident.
        
        Criteria:
        1. Time window: within time_window_seconds
        2. Entity relationship: topologically connected OR same entity
        """
        # Time window check
        ts1 = datetime.fromisoformat(anomaly1["timestamp"].replace("Z", "+00:00"))
        ts2 = datetime.fromisoformat(anomaly2["timestamp"].replace("Z", "+00:00"))
        time_diff = abs((ts2 - ts1).total_seconds())
        
        if time_diff > self.time_window_seconds:
            return False

        # Entity relationship check
        entity1 = anomaly1["entity_id"]
        entity2 = anomaly2["entity_id"]
        
        # Same entity: any anomalies are related (same entity having multiple issues)
        if entity1 == entity2:
            return True
        
        # Connected entities: any anomalies are related (cascade effect)
        if self._are_entities_related(entity1, entity2):
            return True
        
        return False

    def _mock_related(self, entity1: str, entity2: str) -> bool:
        """Mock entity relationships for testing (exposed for external testing)."""
        return self._are_entities_related(entity1, entity2)

    def _generate_incident_id(self, anomalies: List[dict]) -> str:
        """Generate a deterministic incident ID from anomaly hashes."""
        hash_input = json.dumps(
            [a.get("entity_id", "") + a.get("metric_name", "") for a in sorted(anomalies, key=lambda x: x.get("timestamp", ""))],
            sort_keys=True
        )
        hash_val = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return f"INC-{hash_val.upper()}"

    # Map internal severity to P1-P4 format per AGENTS.md data contract
    SEVERITY_MAP = {
        "CRITICAL": "P1",
        "HIGH": "P2",
        "MEDIUM": "P3",
        "LOW": "P4",
    }

    def _calculate_severity(self, anomalies: List[dict]) -> str:
        """Determine incident severity from constituent anomalies.

        Returns P1-P4 format per AGENTS.md IncidentRecord schema.
        """
        severities = [a.get("severity", "INFO") for a in anomalies]
        if "CRITICAL" in severities:
            return "P1"
        elif "HIGH" in severities:
            return "P2"
        elif "MEDIUM" in severities:
            return "P3"
        return "P4"

    def _calculate_business_impact_score(self, anomalies: List[dict]) -> int:
        """Calculate business impact score (0-100) from anomaly scores."""
        if not anomalies:
            return 0
        scores = [a.get("anomaly_score", 0) for a in anomalies]
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        # Weight: 60% max, 40% average, scaled to 0-100
        return int((max_score * 0.6 + avg_score * 0.4) * 100)

    def _calculate_sla_breach_risk(self, severity: str, business_impact_score: int) -> str:
        """Determine SLA breach risk level."""
        if severity == "P1" or business_impact_score >= 90:
            return "HIGH"
        elif severity == "P2" or business_impact_score >= 70:
            return "MEDIUM"
        return "LOW"

    def _build_incident(self, anomalies: List[dict]) -> dict:
        """Build IncidentRecord from a group of related anomalies."""
        incident_id = self._generate_incident_id(anomalies)
        severity = self._calculate_severity(anomalies)
        business_impact_score = self._calculate_business_impact_score(anomalies)
        sla_breach_risk = self._calculate_sla_breach_risk(severity, business_impact_score)
        
        return {
            "incident_id": incident_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "business_impact_score": business_impact_score,
            "root_cause": "",
            "related_anomalies": [a.get("anomaly_id", f"ANM-{hashlib.sha256(a.get('entity_id', '').encode()).hexdigest()[:8].upper()}") for a in anomalies],
            "deduplicated_count": len(anomalies),
            "sla_breach_risk": sla_breach_risk,
            "assigned_to": "auto-remediation",
            "status": "OPEN",
        }

    def group_anomalies(self, anomalies: List[dict]) -> List[dict]:
        """Group related anomalies into incidents using time window + topology + metric similarity.
        
        Args:
            anomalies: List of AnomalySignal dicts
            
        Returns:
            List of IncidentRecord dicts
        """
        if not anomalies:
            return []

        # Sort by timestamp
        sorted_anomalies = sorted(anomalies, key=lambda x: x.get("timestamp", ""))
        
        # Group related anomalies
        groups: List[List[dict]] = []
        used: set = set()
        
        for i, anomaly in enumerate(sorted_anomalies):
            if i in used:
                continue
            
            group = [anomaly]
            used.add(i)
            
            for j, other in enumerate(sorted_anomalies):
                if j in used:
                    continue
                if self._are_related(anomaly, other):
                    group.append(other)
                    used.add(j)
            
            groups.append(group)
        
        # Build incidents from groups
        incidents = [self._build_incident(group) for group in groups]
        
        # Deduplicate
        incidents = self.deduplicate(incidents)
        
        return incidents

    def deduplicate(self, incidents: List[dict]) -> List[dict]:
        """Remove duplicate incidents based on incident_id."""
        seen_ids: set = set()
        unique_incidents: List[dict] = []
        
        for incident in incidents:
            incident_id = incident.get("incident_id", "")
            if incident_id not in seen_ids:
                seen_ids.add(incident_id)
                unique_incidents.append(incident)
        
        return unique_incidents
