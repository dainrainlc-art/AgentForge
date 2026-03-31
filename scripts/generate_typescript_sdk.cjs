#!/usr/bin/env node
/**
 * TypeScript SDK Generator for AgentForge API
 */

const fs = require('fs');
const path = require('path');

const openapiPath = path.join(__dirname, '../docs/api/openapi.json');
const outputDir = path.join(__dirname, '../sdks/typescript');

// 读取 OpenAPI 规范
const spec = JSON.parse(fs.readFileSync(openapiPath, 'utf-8'));

// 创建输出目录
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

console.log('Generating TypeScript SDK...');

// 生成 client.ts
const clientCode = String.raw`/**
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
`;

fs.writeFileSync(path.join(outputDir, 'client.ts'), clientCode);

// 生成 index.ts
const indexCode = String.raw`/**
 * AgentForge TypeScript SDK
 */

export { AgentForgeClient } from './client';
export * from './types';

export const VERSION = '1.0.0';
`;

fs.writeFileSync(path.join(outputDir, 'index.ts'), indexCode);

// 生成 types.ts
const typesCode = String.raw`/**
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
`;

fs.writeFileSync(path.join(outputDir, 'types.ts'), typesCode);

// 生成 package.json
const packageJson = {
    name: '@agentforge/sdk',
    version: '1.0.0',
    description: 'TypeScript SDK for AgentForge API',
    main: 'dist/index.js',
    types: 'dist/index.d.ts',
    files: ['dist'],
    scripts: {
        build: 'tsc',
        clean: 'rm -rf dist',
        test: 'jest',
    },
    keywords: ['agentforge', 'sdk', 'api', 'typescript'],
    author: 'AgentForge Team',
    license: 'MIT',
    dependencies: {
        axios: '^1.6.0',
    },
    devDependencies: {
        '@types/node': '^20.0.0',
        typescript: '^5.0.0',
    },
};

fs.writeFileSync(
    path.join(outputDir, 'package.json'),
    JSON.stringify(packageJson, null, 2)
);

// 生成 README.md
const readme = `# AgentForge TypeScript SDK

TypeScript SDK for AgentForge API.

## Installation

\`\`\`bash
npm install @agentforge/sdk
\`\`\`

## Usage

\`\`\`typescript
import { AgentForgeClient } from '@agentforge/sdk';

const client = new AgentForgeClient({
  baseURL: 'http://localhost:8000',
  apiKey: 'your-api-key',
});

// Health check
const health = await client.healthCheck();

// Login
const tokens = await client.login('username', 'password');

// Get orders
const orders = await client.getOrders({ status: 'active' });

// Chat
const response = await client.chat('Hello');
\`\`\`

## API Reference

- \`login(username, password)\` - User login
- \`healthCheck()\` - Health check
- \`getOrders(params)\` - Get orders
- \`getOrder(orderId)\` - Get order by ID
- \`chat(message, agent)\` - Send chat message
- \`syncKnowledge(source, target)\` - Sync knowledge
- \`searchKnowledge(query, limit)\` - Search knowledge
- \`getMetrics()\` - Get system metrics

## License

MIT
`;

fs.writeFileSync(path.join(outputDir, 'README.md'), readme);

// 生成 tsconfig.json
const tsConfig = {
    compilerOptions: {
        target: 'ES2020',
        module: 'commonjs',
        declaration: true,
        outDir: './dist',
        strict: true,
        esModuleInterop: true,
        skipLibCheck: true,
    },
    include: ['*.ts'],
    exclude: ['node_modules', 'dist'],
};

fs.writeFileSync(
    path.join(outputDir, 'tsconfig.json'),
    JSON.stringify(tsConfig, null, 2)
);

console.log('✅ TypeScript SDK generated at', outputDir);
