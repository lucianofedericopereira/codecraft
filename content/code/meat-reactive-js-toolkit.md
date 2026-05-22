---
title: "MEAT: Reactive State Without the Framework"
date: 2025-12-18
comments: true
---

**MEAT** (Mitt Enhanced Application Toolkit): A reactive developer toolkit for clean state control and plugin-powered architecture — Vue composables, DOM binding, a local storage adapter, and an event bus, all in a framework-agnostic package.

## The Framework Tax

Modern front-end development often involves choosing a framework before choosing anything else. React, Vue, Svelte, Angular — each brings a reactivity model, a component system, a build pipeline, and opinions about everything from file naming to state management.

Sometimes the application is small enough that the framework tax — the bundle size, the learning curve, the breaking changes between versions — isn't worth paying. You need reactivity. You need state. You don't need a full framework.

MEAT is for those cases.

## Core: Vue Composables

The reactive core is built around Vue 3's Composition API — specifically the parts that work without Vue's component system:

```javascript
import { ref, computed, watch } from '@vue/reactivity'

// State that triggers updates when it changes
const count = ref(0)
const doubled = computed(() => count.value * 2)

watch(count, (newVal, oldVal) => {
  console.log(`Count changed from ${oldVal} to ${newVal}`)
})

count.value++  // triggers watch, recalculates doubled
```

`@vue/reactivity` is publishable as a standalone package — it doesn't require the Vue runtime. MEAT bundles it as the reactive foundation.

## DOM Binding

The DOM binding layer connects reactive state to the DOM without a virtual DOM or template compilation:

```javascript
import { bind, bindList, bindAttr } from 'meat'

const username = ref('')
const items    = ref([])

// Two-way binding for input
bind('#username-input', username)

// One-way binding for display
bind('#username-display', computed(() => `Hello, ${username.value}`))

// List rendering
bindList('#product-list', items, (item) => `
  <li data-id="${item.id}">
    <span class="name">${item.name}</span>
    <span class="price">$${item.price}</span>
  </li>
`)

// Attribute binding
bindAttr('#submit-btn', 'disabled', computed(() => username.value.length === 0))
```

Changes to the reactive state automatically update the DOM. DOM input events automatically update the reactive state. No templating language, no JSX, no compilation step.

## Event Bus

The event bus is Mitt — a 200-byte event emitter — extended with:

- Type-safe event definitions
- Middleware support for cross-cutting concerns
- Request/response pattern for async operations

```javascript
import { createBus } from 'meat'

const bus = createBus()

// Define events with types
bus.on('user:login', (user) => {
  session.set('user', user)
  analytics.track('login', { userId: user.id })
})

bus.emit('user:login', { id: 1, email: 'test@example.com' })

// Middleware
bus.use((event, payload, next) => {
  console.log(`[${new Date().toISOString()}] ${event}`)
  next()
})
```

## LocalStorage Adapter

The persistence layer syncs reactive state to localStorage with debouncing:

```javascript
import { persist } from 'meat'

const cart = persist('cart', ref([]))
// cart is a reactive ref that reads from localStorage on init
// and writes to localStorage on change (debounced 300ms)

// Changes persist across page reloads
cart.value.push({ id: 'SKU-001', qty: 1 })
```

The debouncing prevents write storms when state changes rapidly — form typing, drag operations, slider values.

## Plugin System

MEAT's plugin system lets you extend or replace any part of the toolkit:

```javascript
import { createApp } from 'meat'

const app = createApp({
  plugins: [
    devTools(),              // Vue DevTools integration
    router(routes),          // Hash-based routing
    i18n({ locale: 'es' }), // Internationalization
    analytics(trackingId),   // Event tracking
  ],
})
```

Each plugin receives the reactive state, event bus, and DOM binding utilities. Plugins compose rather than conflict.

## When MEAT Fits

MEAT is right when:

- You're building a small-to-medium web application that doesn't justify a full framework
- You need reactivity in an existing PHP, Django, or Rails application without replacing the templating
- You're adding interactivity to a static site or a server-rendered page
- You want Vue's reactivity model without Vue's component system

It's the wrong tool when you're building a large SPA where Vue, React, or Svelte's ecosystem — DevTools, routing, SSR, component libraries — becomes an asset rather than overhead.

## Links

- **GitHub**: [lucianofedericopereira/meat](https://github.com/lucianofedericopereira/meat)
- **MEAT Handbook**: [lucianofedericopereira/the-meat-handbook](https://github.com/lucianofedericopereira/the-meat-handbook)

## License

MIT
