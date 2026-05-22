---
title: "Splice: High-Performance Signal Dispatch for JavaScript"
date: 2026-01-29
comments: true
---

**Splice**: A modular JavaScript framework for in-process signal dispatch — immutable messages, circular context pools, bitmask-encoded headers, and a plugin-driven lifecycle. Designed for predictable, low-latency event processing without the GC pressure of traditional event buses.

## The Event Bus Problem

Event-driven JavaScript is everywhere. Redux, RxJS, EventEmitter, custom pub/sub implementations. They work. Under enough load, they develop problems:

- Dynamic allocations per dispatch add GC pressure
- Sprawling handler maps make trace debugging hard
- Unpredictable performance under load is acceptable until it isn't

These are not catastrophic failures — they're friction that accumulates. Splice addresses the friction at the architecture level.

## Core Concepts

### Immutable Messages

Every signal in Splice is a frozen object. Once created, it cannot be modified. This eliminates a class of bugs where handlers mutate shared state and create implicit ordering dependencies.

```javascript
const signal = splice.createSignal('cart:add', {
  productId: 'SKU-001',
  quantity:   1,
});
// signal is frozen — any mutation attempt throws in strict mode
```

### Circular Context Pool

Traditional event dispatchers allocate a new context object for each event. Under high-frequency dispatch, this creates GC pressure. Splice uses a fixed-size pool of reusable context frames:

```javascript
const pool = new ContextPool({ size: 64 });

// Dispatch borrows a frame from the pool
const ctx = pool.acquire();
ctx.signal  = signal;
ctx.handler = handler;

// After dispatch, the frame returns to the pool
pool.release(ctx);
```

The pool size is tuned at construction time. For UI applications, 16–32 frames is usually enough. For server-side event processing under sustained load, 64–128.

### Bitmask Header Encoding

Signal metadata — type, phase, flags — is encoded in a 3-byte bitmask header rather than a JavaScript object with string keys:

```javascript
// Traditional: { type: 'SET', phase: 'BEFORE', debug: true }
// Splice:
const header = BITMASK.SET | PHASE.BEFORE | FLAGS.DEBUG;
// → 0b001_01_1 packed into 3 bytes
```

Bitmask operations are faster than property lookups and comparisons. The encoding is deterministic and compact — useful for logging and debugging where you're processing thousands of events per second.

## Usage

```javascript
import { createSplice } from 'splice';

const splice = createSplice({ poolSize: 32 });

// Register a handler
splice.onSignal('cart:add', (ctx) => {
  const { productId, quantity } = ctx.signal.payload;
  cart.add(productId, quantity);
});

// Add middleware
splice.use(logger({ level: 'debug' }));
splice.use(validator({
  'cart:add': (signal) => signal.payload.quantity > 0 || 'quantity must be positive'
}));

// Dispatch
splice.dispatchSignal('cart:add', { productId: 'SKU-001', quantity: 1 });

// Cleanup
splice.dispose();
```

## The Plugin System

Plugins attach to the signal lifecycle:

```javascript
function auditPlugin() {
  return {
    beforeDispatch(ctx) {
      ctx.meta.startTime = performance.now();
    },
    afterDispatch(ctx) {
      const duration = performance.now() - ctx.meta.startTime;
      audit.record(ctx.signal.type, duration);
    },
    onError(ctx, error) {
      errorTracker.capture(error, { signal: ctx.signal.type });
    }
  };
}

splice.use(auditPlugin());
```

The lifecycle hooks run in registration order. Error in a plugin does not propagate to other plugins — errors are isolated to the lifecycle stage where they occur.

## Architecture

```
SpliceAPI
├── dispatchSignal()  — public entry point
├── onSignal()        — handler registration
└── use(plugin)       — plugin registration
        ↓
SignalRuntime
├── processFrame()    — lifecycle execution
├── beforeDispatch    — plugin hooks
├── handler call      — registered handler
└── afterDispatch     — plugin hooks
        ↓
ContextPool
├── acquire()         — borrow a frame
└── release()         — return a frame
```

The three-layer separation keeps each concern isolated. You can swap the runtime without changing the API. You can change the pool implementation without changing how handlers are registered.

## When to Use It

Splice is worth the architecture investment when:

- Dispatch frequency is high enough that per-event allocation shows up in profiling
- You need structured middleware (logging, validation, retry) across all signal types
- You want a clear audit trail of what signals were dispatched and when
- You're building a plugin-based system where cross-cutting concerns should compose

For a simple "emit event, handle it" use case with low frequency, an EventEmitter is simpler and Splice would be overengineering.

## Links

- **GitHub**: [lucianofedericopereira/splice](https://github.com/lucianofedericopereira/splice)

## License

MIT
