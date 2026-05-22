---
title: "My Wedding: A Handcrafted Digital Invitation"
date: 2026-01-21
comments: true
---

**My Wedding**: A wedding e-card built with HTML, CSS, and vanilla JavaScript — falling petals animation, responsive layout, smooth interactivity, no external libraries. One hundred percent handcrafted.

## Why Build It Yourself

You could use a wedding invitation service. Upload a photo, pick a template, get a link. Done in twenty minutes.

Building it takes longer. But it's yours — every pixel, every animation parameter, every transition timing. When you share a link to something you built, there's a different feeling to it than sharing a link to something a platform generated for you.

For a wedding invitation, that feeling matters.

## The Falling Petals

The animation is the visual centerpiece — white and pink petals falling from the top of the screen at slightly different speeds, sizes, and trajectories, with a gentle sway.

```javascript
function createPetal() {
  const petal = document.createElement('div');
  petal.classList.add('petal');

  // Randomize each petal
  const size     = 8 + Math.random() * 16;    // 8–24px
  const startX   = Math.random() * 100;        // 0–100vw
  const duration = 4 + Math.random() * 6;      // 4–10s
  const delay    = Math.random() * 5;          // 0–5s stagger
  const sway     = (Math.random() - 0.5) * 60; // horizontal drift

  petal.style.cssText = `
    width:  ${size}px;
    height: ${size}px;
    left:   ${startX}vw;
    animation-duration:  ${duration}s;
    animation-delay:    -${delay}s;
    --sway: ${sway}px;
  `;

  document.querySelector('.petals-container').appendChild(petal);

  // Remove after animation completes
  petal.addEventListener('animationend', () => petal.remove());
}

// Continuously create petals
setInterval(createPetal, 300);
```

The CSS handles the falling and swaying via `@keyframes`:

```css
@keyframes fall {
  0% {
    transform: translateY(-20px) translateX(0) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(110vh) translateX(var(--sway)) rotate(720deg);
    opacity: 0;
  }
}

.petal {
  position: fixed;
  top: 0;
  border-radius: 50% 0 50% 0;
  background: linear-gradient(135deg, #fce4ec, #f8bbd0);
  animation: fall linear infinite;
  pointer-events: none;
}
```

The `--sway` CSS custom property is set per-petal from JavaScript, allowing each petal to have its own horizontal drift direction and magnitude without needing separate keyframe definitions.

## Responsive Layout

The card is fully responsive — it reads correctly on a phone opened while eating dinner, on a tablet, and on the desktop where it was first shared.

```css
.card {
  max-width: 600px;
  margin: 0 auto;
  padding: clamp(1.5rem, 5vw, 3rem);
  text-align: center;
}

.date {
  font-size: clamp(1.2rem, 4vw, 2rem);
  font-weight: 300;
  letter-spacing: 0.15em;
}

.names {
  font-size: clamp(2rem, 8vw, 4rem);
  font-family: 'Cormorant Garamond', Georgia, serif;
}
```

`clamp()` handles the responsive typography without media queries — the font size smoothly scales between the minimum and maximum values based on viewport width. One declaration, infinite screen sizes.

## The Interactivity

Subtle details make the card feel alive rather than static:

- The ceremony details appear with a fade-in on scroll
- The RSVP section expands when clicked, with a smooth height transition
- The venue name links to Google Maps with a gentle pulse on hover
- The countdown to the ceremony date updates in real time

```javascript
// Live countdown
function updateCountdown() {
  const ceremony = new Date('2026-04-12T17:00:00');
  const now      = new Date();
  const diff     = ceremony - now;

  if (diff <= 0) {
    document.querySelector('.countdown').textContent = 'Today! 🌸';
    return;
  }

  const days    = Math.floor(diff / 86400000);
  const hours   = Math.floor((diff % 86400000) / 3600000);
  const minutes = Math.floor((diff % 3600000)  / 60000);

  document.querySelector('.days').textContent    = days;
  document.querySelector('.hours').textContent   = hours;
  document.querySelector('.minutes').textContent = minutes;
}

setInterval(updateCountdown, 60000);
updateCountdown();
```

## No Libraries

The entire card — animations, layout, interactivity, countdown — is built with HTML, CSS, and vanilla JavaScript. No jQuery, no React, no animation library, no utility framework.

This is a deliberate choice. The card needs to work in any browser, including on phones that might have outdated software. It needs to load fast on a cellular connection. And it needs to be maintainable by someone who knows the web platform but may not know any particular library.

Zero dependencies means zero dependency problems. The card that worked on the day it was first shared will still work years later, because it relies only on standards that don't change.

## Links

- **GitHub**: [lucianofedericopereira/my-wedding](https://github.com/lucianofedericopereira/my-wedding)

## License

MIT
