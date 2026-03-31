# AgentForge TypeScript SDK

TypeScript SDK for AgentForge API.

## Installation

```bash
npm install @agentforge/sdk
```

## Usage

```typescript
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
```

## API Reference

- `login(username, password)` - User login
- `healthCheck()` - Health check
- `getOrders(params)` - Get orders
- `getOrder(orderId)` - Get order by ID
- `chat(message, agent)` - Send chat message
- `syncKnowledge(source, target)` - Sync knowledge
- `searchKnowledge(query, limit)` - Search knowledge
- `getMetrics()` - Get system metrics

## License

MIT
