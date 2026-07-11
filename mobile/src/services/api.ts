/**
 * OmniWatch 2.0 — Mobile (API Client)
 * Component: api
 * Layer: Mobile
 * Phase: 7
 * Purpose: API client with JWT authentication, REST calls, and WebSocket support
 */
import * as SecureStore from 'expo-secure-store';

const BASE_URL_KEY = 'omniwatch_server_url';
const JWT_TOKEN_KEY = 'omniwatch_jwt_token';

interface ApiOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

class ApiClient {
  private baseUrl: string = '';
  private token: string | null = null;

  async initialize(): Promise<void> {
    this.baseUrl = (await SecureStore.getItemAsync(BASE_URL_KEY)) || 'http://localhost:8000';
    this.token = await SecureStore.getItemAsync(JWT_TOKEN_KEY);
  }

  async setServerUrl(url: string): Promise<void> {
    this.baseUrl = url;
    await SecureStore.setItemAsync(BASE_URL_KEY, url);
  }

  async getServerUrl(): Promise<string> {
    return this.baseUrl;
  }

  async login(username: string, password: string): Promise<boolean> {
    try {
      const response = await this.request('/auth/login', {
        method: 'POST',
        body: { username, password },
      });

      if (response.token) {
        this.token = response.token;
        await SecureStore.setItemAsync(JWT_TOKEN_KEY, response.token);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  async logout(): Promise<void> {
    this.token = null;
    await SecureStore.deleteItemAsync(JWT_TOKEN_KEY);
  }

  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint: string, options: ApiOptions = {}): Promise<any> {
    const { method = 'GET', body, headers = {} } = options;
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      method,
      headers: {
        ...this.getAuthHeaders(),
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  }

  // Dashboard
  async getIncidents(): Promise<any[]> {
    return this.request('/api/v1/incidents');
  }

  async getIncidentStats(): Promise<any> {
    return this.request('/api/v1/incidents/stats');
  }

  // Incidents
  async getIncidentById(id: string): Promise<any> {
    return this.request(`/api/v1/incidents/${id}`);
  }

  async approveIncident(id: string): Promise<void> {
    await this.request(`/api/v1/incidents/${id}/approve`, { method: 'POST' });
  }

  async rejectIncident(id: string, reason: string): Promise<void> {
    await this.request(`/api/v1/incidents/${id}/reject`, {
      method: 'POST',
      body: { reason },
    });
  }

  // Topology
  async getTopologyNodes(): Promise<any[]> {
    return this.request('/api/v1/topology/nodes');
  }

  async getTopologyEdges(): Promise<any[]> {
    return this.request('/api/v1/topology/edges');
  }

  // Settings
  async getSettings(): Promise<any> {
    return this.request('/api/v1/settings');
  }

  async updateSettings(settings: any): Promise<void> {
    await this.request('/api/v1/settings', {
      method: 'PUT',
      body: settings,
    });
  }

  // WebSocket for real-time updates
  createWebSocket(onMessage: (data: any) => void): WebSocket {
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws/events';
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }
}

export const api = new ApiClient();
export default api;
