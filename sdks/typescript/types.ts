/**
 * Type definitions
 */

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Order {
  order_id: string;
  title: string;
  description: string;
  status: string;
  price: number;
  created_at: string;
  updated_at?: string;
}

export interface ChatResponse {
  message: string;
  conversation_id?: string;
  tokens_used?: number;
}

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  source: string;
  created_at: string;
  score?: number;
}

export interface Metrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  requests_per_second: number;
}
