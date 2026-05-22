---
title: "Cloudflare Learning: From DNS to Full-Stack Serverless"
date: 2026-02-13
comments: true
---

**Cloudflare Learning**: A hands-on TypeScript journey through Cloudflare's platform — Workers, Durable Objects, KV, R2, D1, and Zero Trust — built by actually shipping things, not just reading documentation.

## Learning by Building

Cloudflare's documentation is extensive and well-written. It still doesn't replace the experience of hitting a 1 MB worker limit at midnight, watching your Durable Object state disappear because you stored it wrong, or realizing that KV's eventual consistency matters for your specific use case and not just as an abstract concept.

This repository is structured as a series of increasingly complex projects, each one building on the previous. The goal is not a reference implementation — it's a learning path with working code at every step.

## The Stack

Cloudflare's platform is wider than most developers realize:

| Service | What It Does |
|---------|-------------|
| Workers | Serverless JavaScript/TypeScript at the edge |
| Durable Objects | Stateful singletons with strong consistency |
| KV | Globally distributed key-value store |
| R2 | S3-compatible object storage, no egress fees |
| D1 | Distributed SQLite at the edge |
| Pages | Static site and full-stack deployment |
| Zero Trust | Access control without a VPN |
| Queues | Durable message queues for async workflows |

The learning path moves through them roughly in order of complexity.

## Workers: The Foundation

A Cloudflare Worker is a JavaScript module that handles HTTP requests. The runtime is V8, not Node.js — which matters when you reach for `fs`, `crypto`, or `http` from Node's standard library and find they don't exist.

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === '/api/hello') {
      return Response.json({ message: 'Hello from the edge' });
    }

    return new Response('Not Found', { status: 404 });
  }
};
```

The `env` parameter is where bindings live — KV namespaces, D1 databases, R2 buckets. Cloudflare injects them at runtime; you declare them in `wrangler.toml`.

## Durable Objects: Distributed State Done Right

KV is eventually consistent. When you need strong consistency — a counter that doesn't double-count, a session that doesn't split-brain — Durable Objects are the answer.

```typescript
export class Counter implements DurableObject {
  private value = 0;

  constructor(private state: DurableObjectState) {}

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === '/increment') {
      this.value++;
      await this.state.storage.put('value', this.value);
      return Response.json({ value: this.value });
    }

    const stored = await this.state.storage.get<number>('value') ?? 0;
    return Response.json({ value: stored });
  }
}
```

The key insight: every Durable Object instance is a singleton. All requests to the same object ID are serialized through the same instance, globally. That's how you get consistency without a traditional database.

## D1: SQLite at the Edge

D1 is the most interesting part of Cloudflare's stack for application developers. It's SQLite — the most widely deployed database in history — replicated to Cloudflare's edge network.

```typescript
const result = await env.DB.prepare(
  'SELECT * FROM posts WHERE published = 1 ORDER BY created_at DESC LIMIT ?'
).bind(10).all();

return Response.json(result.results);
```

The gotchas worth knowing:
- D1 is SQLite, not MySQL or Postgres. `AUTOINCREMENT` behavior differs from MySQL's `AUTO_INCREMENT`.
- Reads are served from the nearest replica; writes go to the primary and replicate outward.
- The query syntax is standard SQL but the dialect is SQLite 3.

## Zero Trust: Access Without a VPN

Zero Trust replaces the "inside the network = trusted" model with "verify every request regardless of origin." For developer tools and internal applications, this means you can deploy a private application on Cloudflare's network and control access with your existing identity provider.

The setup that took an afternoon to understand but five minutes to configure: Access policies that chain to GitHub OAuth, allowing specific GitHub organizations or teams to reach a protected route — with no VPN, no static IPs, and no credential management.

## What This Teaches

The deeper lesson from this project isn't any specific Cloudflare service. It's that the serverless edge model has genuinely different constraints than traditional server deployments:

- **Cold starts are measured in milliseconds**, not seconds. This changes how you think about initialization.
- **No persistent filesystem.** State goes in KV, R2, D1, or Durable Objects — not `/tmp`.
- **Execution time is bounded.** Workers have a CPU time limit. Long-running tasks need Queues and background processing.
- **Global by default.** Your code runs in 300+ data centers simultaneously. Consistency requires explicit thought.

These aren't limitations to work around. They're a different programming model that rewards thinking about locality, consistency boundaries, and state lifecycle from the start.

## Links

- **GitHub**: [lucianofedericopereira/cloudflare-learning](https://github.com/lucianofedericopereira/cloudflare-learning)

## License

MIT
