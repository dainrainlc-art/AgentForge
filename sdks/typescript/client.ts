/**
 * AgentForge TypeScript SDK
 */

import axios, { AxiosInstance } from 'axios';

export interface AgentForgeClientConfig {
  baseURL?: string;
  apiKey?: string;
  timeout?: number;
}

export class AgentForgeClient {
  private client: AxiosInstance;

  constructor(config: AgentForgeClientConfig = {}) {
    const {
      baseURL = 'http://localhost:8000',
      apiKey,
      timeout = 30000,
    } = config;

    this.client = axios.create({
      baseURL: baseURL.replace(/\/$/, ''),
      timeout,
    });

    if (apiKey) {
      this.client.defaults.headers.common['Authorization'] = 'Bearer ' + apiKey;
    }
  }

  async login(username: string, password: string): Promise<any> {
    const response = await this.client.post('/api/auth/login', { username, password });
    return response.data;
  }

  async healthCheck(): Promise<any> {
    const response = await this.client.get('/api/health');
    return response.data;
  }

  async getOrders(params?: any): Promise<any> {
    const response = await this.client.get('/api/orders', { params });
    return response.data;
  }

  async getOrder(orderId: string): Promise<any> {
    const response = await this.client.get('/api/orders/' + orderId);
    return response.data;
  }

  async chat(message: string, agent?: string): Promise<any> {
    const response = await this.client.post('/api/chat', { message, agent: agent || 'default' });
    return response.data;
  }

  async syncKnowledge(source: string, target: string): Promise<any> {
    const response = await this.client.post('/api/knowledge/sync', { source, target });
    return response.data;
  }

  async searchKnowledge(query: string, limit?: number): Promise<any> {
    const response = await this.client.get('/api/knowledge/search', { params: { query, limit } });
    return response.data;
  }

  async getMetrics(): Promise<any> {
    const response = await this.client.get('/api/metrics');
    return response.data;
  }
}

export default AgentForgeClient;
