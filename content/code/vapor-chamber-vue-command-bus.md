---
title: "Vapor Chamber: A Command Bus for Vue Vapor"
date: 2026-05-16
comments: true
---

**Vapor Chamber**: A 6.7KB command bus designed for Vue 3.6+ Vapor mode — one handler per action, a composable plugin pipeline, and signal-native reactive state. Replaces scattered event listeners and prop-drilling with one predictable, testable flow.

## What Vue Vapor Is

Vue Vapor is Vue's compilation strategy that eliminates the Virtual DOM. Instead of diffing virtual trees, Vapor compiles templates to direct DOM operations using signals — reactive primitives that update only what changed.

As of Vue 3.6, Vapor mode is feature-complete for stable APIs. The reactivity engine has been rewritten atop alien-signals, delivering ~14% less memory and faster dependency tracking. `ref()` is now a signal internally.

The implication for architecture: if your framework is moving toward direct, signal-native updates, your event handling should too.

## The Problem Vapor Chamber Solves

The standard Vue event pattern — `emit` / event buses / `v-model` prop chains — works well for simple components. It struggles when:

- Multiple components respond to the same user action
- You need cross-cutting concerns (logging, validation, analytics) on every action
- Testing requires mocking the event propagation chain
- Actions need to be retried, debounced, or queued

The traditional solution is to scatter this logic across components, lifecycle hooks, and store mutations. Vapor Chamber centralizes it.

## The Command Bus Pattern

A command bus maps user actions to handlers. One action, one handler. Cross-cutting concerns attach as plugins.

```typescript
import { createCommandBus, useCommand } from 'vapor-chamber';

const bus = createCommandBus();

// Register handlers
bus.register('cart:add', async (cmd) => {
  await cartService.add(cmd.payload.productId, cmd.payload.quantity);
});

bus.register('cart:remove', async (cmd) => {
  await cartService.remove(cmd.payload.productId);
});

// Add plugins
bus.use(logger());
bus.use(validator({
  'cart:add': (cmd) => cmd.payload.quantity > 0 ? null : 'Quantity must be positive',
}));
bus.use(retry({ maxAttempts: 3, delay: 1000 }));
```

In a component:

```typescript
const { dispatch, loading, lastError } = useCommand('cart:add');

// dispatch returns a Promise
const handleAddToCart = () => dispatch({ productId: product.id, quantity: 1 });
```

`loading` and `lastError` are signals — they update reactively when the command state changes, without any additional wiring.

## Migrating from Vue 3 Emitters

The before and after for a common pattern:

```typescript
// Before — Vue 3 emitter, scattered logic
// ProductCard.vue
emit('cart:add', product);

// App.vue — listening and coordinating
bus.on('cart:add', (product) => {
  cart.items.push(product);
  analytics.track('add_to_cart', product);
  // Validation here? Or in the component? Or both?
});

// CartBadge.vue — also listening?
bus.on('cart:add', () => badgeCount.value++);
```

```typescript
// After — Vapor Chamber
bus.register('cart:add', async (cmd) => {
  await cartService.add(cmd.payload);
  analytics.track('add_to_cart', cmd.payload);
  // One place. One handler. Cross-cutting via plugins.
});

bus.use(analyticsPlugin());  // analytics for all commands
bus.use(optimisticUpdate(cartStore));  // updates UI before network response
```

## Plugin Pipeline

Plugins wrap the command lifecycle:

```typescript
function retry({ maxAttempts = 3, delay = 1000 } = {}) {
  return {
    async execute(cmd, next) {
      let attempts = 0;
      while (attempts < maxAttempts) {
        try {
          return await next(cmd);
        } catch (err) {
          attempts++;
          if (attempts >= maxAttempts) throw err;
          await sleep(delay * attempts);
        }
      }
    }
  };
}
```

Available plugins: `logger`, `validator`, `debounce`, `throttle`, `retry`, `persist` (localStorage), `sync` (cross-tab via BroadcastChannel), plus transport bridges for HTTP, WebSocket, and SSE.

## Size and Dependencies

The core is ~6.7KB brotli-compressed (full IIFE) / ~5.7KB tree-shaken ESM. Zero runtime dependencies. The bus itself has no Vue import — the framework-agnostic core can be used in plain JavaScript or other frameworks.

Vue integration is an adapter layer:

```typescript
// Vue plugin
app.use(VaporChamber, { bus });

// SSR isolation — per-request bus, no shared singletons
export function createApp() {
  const bus = createCommandBus();
  // ... register handlers
  return { app, bus };
}
```

The SSR isolation is non-negotiable for any server-rendered application — shared global event buses are a common source of request bleed-through bugs.

## Links

- **GitHub**: [lucianofedericopereira/vapor-chamber](https://github.com/lucianofedericopereira/vapor-chamber)
- **Vue Vapor**: [vuejs/vue-vapor](https://github.com/vuejs/vue-vapor)

## License

MIT
