/**
 * OmniWatch 2.0 — Mobile (Dashboard Screen)
 * Component: DashboardScreen
 * Layer: Mobile
 * Phase: 7
 * Purpose: Main dashboard showing incident list with stats cards and pull-to-refresh
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import { scheduleIncidentNotification } from '../services/notifications';

interface Incident {
  incident_id: string;
  severity: string;
  status: string;
  created_at: string;
  root_cause?: {
    entity: string;
    metric: string;
  };
  business_impact?: {
    affected_users: number;
  };
}

export default function DashboardScreen({ navigation }: any) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [incidentsData, statsData] = await Promise.all([
        api.getIncidents(),
        api.getIncidentStats(),
      ]);
      setIncidents(incidentsData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    api.initialize().then(fetchData);
  }, [fetchData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchData();
  }, [fetchData]);

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

  const renderStatCard = (title: string, value: number | string, icon: keyof typeof Ionicons.glyphMap, color: string) => (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Ionicons name={icon} size={24} color={color} />
      <View style={styles.statContent}>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={styles.statTitle}>{title}</Text>
      </View>
    </View>
  );

  const renderIncident = ({ item }: { item: Incident }) => (
    <TouchableOpacity
      style={styles.incidentCard}
      onPress={() => navigation.navigate('Incidents', { incidentId: item.incident_id })}
    >
      <View style={styles.incidentHeader}>
        <View style={[styles.severityBadge, { backgroundColor: getSeverityColor(item.severity) }]}>
          <Text style={styles.severityText}>{item.severity}</Text>
        </View>
        <Text style={styles.incidentId}>{item.incident_id}</Text>
        <Text style={styles.timestamp}>
          {new Date(item.created_at).toLocaleTimeString()}
        </Text>
      </View>
      <Text style={styles.incidentEntity}>
        {item.root_cause?.entity || 'Unknown entity'}
      </Text>
      <View style={styles.incidentFooter}>
        <Text style={styles.metric}>{item.root_cause?.metric}</Text>
        <Text style={styles.affectedUsers}>
          {item.business_impact?.affected_users?.toLocaleString() || 0} affected
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>OmniWatch</Text>
        <Text style={styles.subtitle}>Dashboard</Text>
      </View>

      <FlatList
        data={incidents}
        keyExtractor={(item) => item.incident_id}
        renderItem={renderIncident}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListHeaderComponent={
          <View style={styles.statsContainer}>
            {renderStatCard('Active', stats?.active || 0, 'alert-circle', '#ef4444')}
            {renderStatCard('P1 Incidents', stats?.p1 || 0, 'warning', '#f97316')}
            {renderStatCard('Resolved Today', stats?.resolved || 0, 'checkmark-circle', '#22c55e')}
            {renderStatCard('Services', stats?.services || 0, 'server', '#3b82f6')}
          </View>
        }
        contentContainerStyle={styles.listContent}
      />
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
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  subtitle: {
    fontSize: 16,
    color: '#93c5fd',
    marginTop: 4,
  },
  statsContainer: {
    padding: 16,
    gap: 12,
  },
  statCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  statContent: {
    flex: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  statTitle: {
    fontSize: 14,
    color: '#6b7280',
  },
  listContent: {
    paddingBottom: 20,
  },
  incidentCard: {
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginVertical: 6,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  incidentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
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
    flex: 1,
  },
  timestamp: {
    fontSize: 12,
    color: '#9ca3af',
  },
  incidentEntity: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  incidentFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    fontSize: 14,
    color: '#6b7280',
  },
  affectedUsers: {
    fontSize: 14,
    color: '#ef4444',
    fontWeight: '500',
  },
});
