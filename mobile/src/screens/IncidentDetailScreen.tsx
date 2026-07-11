/**
 * OmniWatch 2.0 — Mobile (Incident Detail Screen)
 * Component: IncidentDetailScreen
 * Layer: Mobile
 * Phase: 7
 * Purpose: Incident detail view with evidence chain, blast radius, and approval actions
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

interface Evidence {
  step: number;
  observation: string;
  timestamp: string;
  signal_type: string;
  evidence_id?: string;
}

interface BlastRadius {
  entity: string;
  impact: string;
  affected_users: number;
}

interface IncidentDetail {
  incident_id: string;
  severity: string;
  status: string;
  created_at: string;
  confidence: number;
  root_cause: {
    entity: string;
    entity_type: string;
    metric: string;
    deviation: string;
    causal_score: number;
  };
  evidence_chain: Evidence[];
  blast_radius: BlastRadius[];
  business_impact: {
    affected_users: number;
    estimated_revenue_at_risk_usd_per_hour: number;
    slo_breach?: string;
  };
}

export default function IncidentDetailScreen({ route, navigation }: any) {
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const incidentId = route?.params?.incidentId;

  useEffect(() => {
    if (incidentId) {
      loadIncident(incidentId);
    }
  }, [incidentId]);

  const loadIncident = async (id: string) => {
    try {
      const data = await api.getIncidentById(id);
      setIncident(data);
    } catch (error) {
      console.error('Failed to load incident:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    Alert.alert(
      'Approve Remediation',
      'Are you sure you want to approve the auto-remediation?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Approve',
          onPress: async () => {
            try {
              await api.approveIncident(incident!.incident_id);
              Alert.alert('Success', 'Remediation approved');
              loadIncident(incident!.incident_id);
            } catch (error) {
              Alert.alert('Error', 'Failed to approve remediation');
            }
          },
        },
      ]
    );
  };

  const handleReject = async () => {
    Alert.alert(
      'Reject Remediation',
      'Enter reason for rejection:',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reject',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.rejectIncident(incident!.incident_id, 'Manual rejection');
              Alert.alert('Success', 'Remediation rejected');
              loadIncident(incident!.incident_id);
            } catch (error) {
              Alert.alert('Error', 'Failed to reject remediation');
            }
          },
        },
      ]
    );
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'P1':
        return '#ef4444';
      case 'P2':
        return '#f97316';
      case 'P3':
        return '#eab308';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  if (!incident) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Ionicons name="arrow-back" size={24} color="#ffffff" />
          </TouchableOpacity>
          <Text style={styles.title}>Incident Details</Text>
        </View>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No incident selected</Text>
          <Text style={styles.emptySubtext}>Go to Dashboard to select an incident</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>
        <Text style={styles.title}>Incident Details</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Incident Summary */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <View style={[styles.severityBadge, { backgroundColor: getSeverityColor(incident.severity) }]}>
              <Text style={styles.severityText}>{incident.severity}</Text>
            </View>
            <Text style={styles.incidentId}>{incident.incident_id}</Text>
          </View>
          <Text style={styles.entity}>{incident.root_cause.entity}</Text>
          <Text style={styles.metric}>{incident.root_cause.metric}</Text>
          <Text style={styles.deviation}>{incident.root_cause.deviation}</Text>
          <View style={styles.confidenceContainer}>
            <Text style={styles.confidenceLabel}>Confidence:</Text>
            <Text style={styles.confidenceValue}>{(incident.confidence * 100).toFixed(1)}%</Text>
          </View>
        </View>

        {/* Evidence Chain */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Evidence Chain</Text>
          {incident.evidence_chain.map((evidence, index) => (
            <View key={index} style={styles.evidenceItem}>
              <View style={styles.evidenceStep}>
                <Text style={styles.stepNumber}>{evidence.step}</Text>
              </View>
              <View style={styles.evidenceContent}>
                <Text style={styles.evidenceText}>{evidence.observation}</Text>
                <Text style={styles.evidenceMeta}>
                  {evidence.signal_type} • {new Date(evidence.timestamp).toLocaleTimeString()}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* Blast Radius */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Blast Radius</Text>
          {incident.blast_radius.map((item, index) => (
            <View key={index} style={styles.blastItem}>
              <Ionicons name="alert-circle" size={20} color="#f97316" />
              <View style={styles.blastContent}>
                <Text style={styles.blastEntity}>{item.entity}</Text>
                <Text style={styles.blastImpact}>{item.impact}</Text>
                <Text style={styles.blastUsers}>{item.affected_users.toLocaleString()} users affected</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Business Impact */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Business Impact</Text>
          <View style={styles.impactRow}>
            <Text style={styles.impactLabel}>Affected Users:</Text>
            <Text style={styles.impactValue}>{incident.business_impact.affected_users.toLocaleString()}</Text>
          </View>
          <View style={styles.impactRow}>
            <Text style={styles.impactLabel}>Revenue at Risk:</Text>
            <Text style={[styles.impactValue, { color: '#ef4444' }]}>
              ${incident.business_impact.estimated_revenue_at_risk_usd_per_hour.toLocaleString()}/hr
            </Text>
          </View>
          {incident.business_impact.slo_breach && (
            <View style={styles.impactRow}>
              <Text style={styles.impactLabel}>SLO Breach:</Text>
              <Text style={styles.impactValue}>{incident.business_impact.slo_breach}</Text>
            </View>
          )}
        </View>

        {/* Action Buttons */}
        {incident.status === 'OPEN' && (
          <View style={styles.actionsContainer}>
            <TouchableOpacity style={styles.approveButton} onPress={handleApprove}>
              <Ionicons name="checkmark-circle" size={20} color="#ffffff" />
              <Text style={styles.buttonText}>Approve Remediation</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.rejectButton} onPress={handleReject}>
              <Ionicons name="close-circle" size={20} color="#ffffff" />
              <Text style={styles.buttonText}>Reject</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#1e40af',
    padding: 20,
    paddingTop: 60,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  content: {
    padding: 16,
    paddingBottom: 100,
  },
  summaryCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  severityText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  incidentId: {
    fontSize: 12,
    color: '#6b7280',
  },
  entity: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  metric: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  deviation: {
    fontSize: 14,
    color: '#ef4444',
    marginBottom: 8,
  },
  confidenceContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  confidenceLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  confidenceValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#22c55e',
  },
  sectionCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  evidenceItem: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  evidenceStep: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#3b82f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepNumber: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  evidenceContent: {
    flex: 1,
  },
  evidenceText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  evidenceMeta: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
  blastItem: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  blastContent: {
    flex: 1,
  },
  blastEntity: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  blastImpact: {
    fontSize: 14,
    color: '#6b7280',
  },
  blastUsers: {
    fontSize: 12,
    color: '#ef4444',
    marginTop: 2,
  },
  impactRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  impactLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  impactValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  approveButton: {
    flex: 1,
    backgroundColor: '#22c55e',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  rejectButton: {
    flex: 1,
    backgroundColor: '#ef4444',
    borderRadius: 8,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#6b7280',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 8,
  },
});
