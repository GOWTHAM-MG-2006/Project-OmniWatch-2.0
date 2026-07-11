/**
 * OmniWatch 2.0 — Mobile (Topology Screen)
 * Component: TopologyScreen
 * Layer: Mobile
 * Phase: 7
 * Purpose: Service topology list with health status and anomaly scores
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

interface TopologyNode {
  id: string;
  name: string;
  type: string;
  layer: number;
  status: string;
  anomaly_score: number;
  dependencies: string[];
  dependents: string[];
}

export default function TopologyScreen() {
  const [nodes, setNodes] = useState<TopologyNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);

  const fetchNodes = useCallback(async () => {
    try {
      const data = await api.getTopologyNodes();
      setNodes(data);
    } catch (error) {
      console.error('Failed to fetch topology nodes:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    api.initialize().then(fetchNodes);
  }, [fetchNodes]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchNodes();
  }, [fetchNodes]);

  const getStatusColor = (status: string): string => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return '#22c55e';
      case 'degraded':
        return '#eab308';
      case 'unhealthy':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getAnomalyColor = (score: number): string => {
    if (score >= 0.8) return '#ef4444';
    if (score >= 0.5) return '#f97316';
    if (score >= 0.3) return '#eab308';
    return '#22c55e';
  };

  const getLayerIcon = (layer: number): keyof typeof Ionicons.glyphMap => {
    switch (layer) {
      case 2:
        return 'radio';
      case 3:
        return 'swap-horizontal';
      case 4:
        return 'server';
      case 5:
        return 'git-network';
      case 6:
        return 'brain';
      case 7:
        return 'medkit';
      case 8:
        return 'flask';
      case 9:
        return 'shield-checkmark';
      case 10:
        return 'school';
      case 11:
        return 'desktop';
      default:
        return 'cube';
    }
  };

  const renderNode = ({ item }: { item: TopologyNode }) => (
    <TouchableOpacity
      style={[
        styles.nodeCard,
        selectedNode?.id === item.id && styles.nodeCardSelected,
      ]}
      onPress={() => setSelectedNode(selectedNode?.id === item.id ? null : item)}
    >
      <View style={styles.nodeHeader}>
        <View style={[styles.statusDot, { backgroundColor: getStatusColor(item.status) }]} />
        <Ionicons name={getLayerIcon(item.layer)} size={20} color="#6b7280" />
        <View style={styles.nodeInfo}>
          <Text style={styles.nodeName}>{item.name}</Text>
          <Text style={styles.nodeType}>{item.type} • Layer {item.layer}</Text>
        </View>
        <View style={styles.anomalyBadge}>
          <Text style={[styles.anomalyScore, { color: getAnomalyColor(item.anomaly_score) }]}>
            {(item.anomaly_score * 100).toFixed(0)}%
          </Text>
        </View>
      </View>

      {selectedNode?.id === item.id && (
        <View style={styles.nodeDetails}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Status:</Text>
            <Text style={[styles.detailValue, { color: getStatusColor(item.status) }]}>
              {item.status}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Anomaly Score:</Text>
            <Text style={[styles.detailValue, { color: getAnomalyColor(item.anomaly_score) }]}>
              {item.anomaly_score.toFixed(3)}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Dependencies:</Text>
            <Text style={styles.detailValue}>{item.dependencies.length}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Dependents:</Text>
            <Text style={styles.detailValue}>{item.dependents.length}</Text>
          </View>
          {item.dependencies.length > 0 && (
            <View style={styles.dependsContainer}>
              <Text style={styles.dependsLabel}>Depends on:</Text>
              {item.dependencies.map((dep, idx) => (
                <Text key={idx} style={styles.dependsItem}>• {dep}</Text>
              ))}
            </View>
          )}
        </View>
      )}
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
        <Text style={styles.subtitle}>Service Topology</Text>
      </View>

      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#22c55e' }]} />
          <Text style={styles.legendText}>Healthy</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#eab308' }]} />
          <Text style={styles.legendText}>Degraded</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#ef4444' }]} />
          <Text style={styles.legendText}>Unhealthy</Text>
        </View>
      </View>

      <FlatList
        data={nodes}
        keyExtractor={(item) => item.id}
        renderItem={renderNode}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
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
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    fontSize: 12,
    color: '#6b7280',
  },
  listContent: {
    padding: 16,
    paddingBottom: 100,
  },
  nodeCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  nodeCardSelected: {
    borderColor: '#3b82f6',
    borderWidth: 2,
  },
  nodeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  nodeInfo: {
    flex: 1,
  },
  nodeName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  nodeType: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  anomalyBadge: {
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  anomalyScore: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  nodeDetails: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  dependsContainer: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
  dependsLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  dependsItem: {
    fontSize: 12,
    color: '#374151',
    marginBottom: 2,
  },
});
