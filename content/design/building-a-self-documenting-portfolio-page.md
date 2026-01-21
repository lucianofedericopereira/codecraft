---
title: "Building a Self-Documenting Portfolio Page"
date: 2026-01-21
comments: true
toc: true
---

Every project tells a story about how someone thinks. When I built my portfolio page, I wanted it to do more than list my experience—I wanted it to demonstrate the way I approach problems, make decisions, and deliver results.

What started as a simple CV page evolved into something that showcases the values I bring to every project: thoughtful architecture, attention to detail, inclusive design, and clear communication across languages and cultures.

## Choosing the Right Tool for the Job

One of the most important skills in software development isn't knowing the latest framework—it's knowing when *not* to use one.

For this project, I made a deliberate choice: a single HTML file with embedded CSS and JavaScript. No React, no build tools, no external dependencies beyond fonts.

This wasn't about avoiding complexity for its own sake. It was about matching the solution to the problem:

**Long-term maintainability.** This page needs to work reliably for years without constant updates. By eliminating external dependencies, I removed the risk of breaking changes, abandoned packages, and security vulnerabilities that plague projects with dozens of npm dependencies. The code I wrote today will work identically in 2030.

**Reduced operational overhead.** There's no build step to break, no CI/CD pipeline to maintain, no environment-specific configurations to debug. This translates directly to lower total cost of ownership—a consideration that matters in any organization managing multiple projects.

**Universal deployment.** The page can be hosted anywhere: Cloudflare Pages, AWS S3, a simple FTP server. This flexibility means the hosting decision can be made based on cost and convenience rather than technical constraints.

**Graceful degradation.** Even if JavaScript fails to load, the core content remains accessible. This resilience matters when serving users across varying network conditions and devices.

The tradeoff is a larger single file (~2,900 lines). But I'd argue that's easier to understand and maintain than a project scattered across dozens of files with hidden configuration. Sometimes the simplest solution is also the most professional one.

## Transparency Through Self-Documentation

I believe in showing your work. That's why the portfolio includes a built-in code viewer that lets anyone inspect exactly how the page was built—syntax-highlighted HTML, CSS, and JavaScript, all viewable without leaving the page.

This feature serves multiple purposes:

**Building trust.** When someone evaluates a developer, they want to see how they write code, not just what they claim to know. The code viewer puts my work on display, demonstrating clean structure, consistent naming, and thoughtful organization.

**Teaching by example.** Junior developers who visit the page can learn from real-world patterns. The code isn't hidden behind a GitHub link they might never click—it's right there, inviting exploration.

**Demonstrating problem-solving.** The viewer itself presented an interesting challenge: how do you display a page's own source code from within that page? The solution—serializing the live DOM and replacing embedded styles with navigable placeholders—shows creative thinking applied to a practical problem.

### Implementation Details

The syntax highlighter I built processes HTML, CSS, and JavaScript using pattern matching. Rather than pulling in a third-party library (which would contradict the "no dependencies" philosophy), I wrote a lightweight tokenizer that handles the common cases well:

```javascript
tokenizeLine(line, mode) {
  switch (mode) {
    case 'html': return this._tokenizeHTML(line);
    case 'css': return this._tokenizeCSS(line);
    case 'js': return this._tokenizeJS(line);
    default: return [{ type: 'plain', text: line }];
  }
}
```

The color scheme follows familiar conventions from popular code editors, making it immediately readable to developers:

| Element | Purpose | Color |
|---------|---------|-------|
| Tags | Structure | Muted blue |
| Attributes | Properties | Light blue |
| Values | Data | Warm gold |
| Comments | Documentation | Green |
| Keywords | Language constructs | Purple |

This attention to familiar patterns reduces cognitive load—visitors can focus on understanding the code rather than deciphering an unfamiliar color scheme.

## Communicating Across Cultures

Working with international teams has taught me that communication goes beyond language. It's about respecting how different cultures consume information and making people feel welcomed in their native context.

The portfolio supports three languages—English, Spanish, and Italian—with instant switching and no page reload. More importantly, the entire user experience adapts: dates, ARIA labels for screen readers, and even the downloadable PDF CV update to match the selected language.

### A Pragmatic Approach to Internationalization

Rather than implementing a complex i18n framework, I used a CSS-first approach where all translations exist in the HTML simultaneously:

```html
<span data-locale="en">Full-Stack Developer</span>
<span data-locale="es">Desarrollador Full-Stack</span>
<span data-locale="it">Sviluppatore Full-Stack</span>
```

CSS controls visibility based on the document's language attribute:

```css
[data-locale] { display: none; }

html[lang="en"] [data-locale="en"],
html[lang="es"] [data-locale="es"],
html[lang="it"] [data-locale="it"] {
  display: revert;
}
```

This approach offers several advantages:

- **No JavaScript required for content.** The page works even if scripts fail to load
- **Instant switching.** No network requests, no loading states
- **SEO-friendly.** All content is present in the initial HTML
- **Maintainable.** Translations live next to each other, making updates straightforward

The tradeoff (larger HTML file) is acceptable for a focused page with limited text content. Engineering is about choosing the right tradeoffs, not eliminating them.

### Accessibility Across Languages

One detail that's easy to overlook: screen reader users need ARIA labels to update when the language changes. I built custom web components that automatically regenerate their accessibility labels based on the current locale:

```javascript
class ExperienceEntry extends CVEntry {
  static labelTemplates = {
    en: '{0} at {1}',
    es: '{0} en {1}',
    it: '{0} presso {1}'
  };
}
```

When a Spanish-speaking user with a screen reader navigates to an experience entry, they hear "Desarrollador Senior en Acme Corp" rather than an English label that doesn't match the visible content. These details matter for creating a truly inclusive experience.

## Inclusive Design as a Core Value

Accessibility isn't a feature to add at the end—it's a fundamental aspect of professional software development. Building accessible products means reaching a wider audience, meeting legal requirements in many jurisdictions, and demonstrating respect for all users.

I approached this portfolio with accessibility as a first-class requirement, not an afterthought.

### Semantic Structure

The page uses proper HTML elements throughout: `<header>`, `<main>`, `<section>`, `<nav>`. This matters because assistive technologies understand these elements natively. Screen reader users can navigate by landmarks, jumping directly to the main content or a specific section.

```html
<main id="main-content">
  <section aria-labelledby="experience-heading">
    <h2 id="experience-heading">Experience</h2>
    <!-- content -->
  </section>
</main>
```

The heading hierarchy follows a logical structure (h1 → h2 → h3), giving screen reader users a "table of contents" they can use to understand and navigate the page.

### Keyboard Navigation

Every interactive element is fully keyboard-accessible. The code viewer modal implements proper focus management:

- **Focus trapping:** When the modal opens, keyboard focus stays inside until explicitly closed
- **Focus restoration:** When closed, focus returns to the element that opened it
- **Escape to close:** The universal "dismiss" key works as expected
- **Arrow key navigation:** Tabs can be navigated with arrow keys, following WAI-ARIA patterns

These aren't just technical requirements—they're what makes the difference between a frustrating experience and a professional one for keyboard users.

### Color Contrast and Visual Accessibility

The grayscale palette wasn't chosen randomly. Every color combination meets WCAG AA contrast requirements:

| Combination | Contrast Ratio | Standard |
|-------------|----------------|----------|
| Primary text on background | 12.6:1 | AAA |
| Secondary text on background | 7.2:1 | AAA |
| Subtle text on background | 4.6:1 | AA |
| Links on background | 4.5:1 | AA |

I also respect user preferences for reduced motion. When someone has indicated they experience discomfort from animations, the page disables all motion effects while maintaining full functionality:

```javascript
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  new ScrollAnimator();
}
```

### The Skip Link

A small but important detail: the very first focusable element is a "Skip to main content" link, hidden until focused. Keyboard users can bypass the header navigation with a single Tab + Enter, respecting their time and reducing repetitive navigation.

## Attention to User Experience Details

The small things often make the biggest impression. Here are a few details that demonstrate thoughtfulness in design:

### Real-Time Availability Indicator

The phone contact includes a live indicator showing whether I'm likely available based on my timezone (Italy, CET). During business hours (Monday–Friday, 9:00–17:00), the indicator shows green; outside those hours, it shows red with a tooltip explaining when I'm available.

This serves practical purposes:
- Sets realistic expectations for response times
- Reduces friction for recruiters in different timezones
- Demonstrates attention to the user's perspective

The indicator is also fully accessible, with proper ARIA labels that update dynamically so screen reader users receive the same information.

### Contact Protection

Email addresses left in plain HTML get harvested by spam bots within days. I implemented a lightweight obfuscation system that encodes contact information, then decodes it via JavaScript when the page loads.

This isn't meant to stop determined attackers—it's about eliminating casual harvesting while maintaining a seamless experience for legitimate visitors. The contact information works exactly as expected; the protection is invisible.

### Print-Optimized Output

Yes, people still print CVs. The page includes comprehensive print styles that:

- Remove all interactive elements (buttons, modals)
- Reorder content for optimal reading flow
- Adjust typography for paper (10pt base size)
- Prevent awkward page breaks mid-section
- Produce a clean, professional A4 document

You can print the page directly from any browser and hand it to someone in a meeting. The attention to this "edge case" reflects how I think about product completeness.

## Performance Without Complexity

Fast loading times aren't just a technical metric—they affect user perception, search rankings, and conversion rates. The portfolio loads quickly despite having no build optimization step:

**Font subsetting.** Rather than loading complete font files, I request only the specific characters used on the page—including accented characters for Spanish and Italian. This reduces font payload significantly.

**PDF prefetching.** The browser loads CV files in the background before the user clicks download, eliminating wait time when they request the file.

**Lazy rendering.** The code viewer doesn't process syntax highlighting until the user actually opens it, avoiding wasted computation for visitors who never use that feature.

**Embedded assets.** The profile photo is a small WebP image encoded as a data URI. One less HTTP request, zero layout shift while it loads.

These optimizations demonstrate that performance and simplicity aren't mutually exclusive. You don't always need complex build pipelines to deliver fast experiences.

## Design System Thinking

Even for a single-page project, I applied design system principles that would scale to larger applications:

### Systematic Color Palette

Colors are defined using OKLCH (a perceptually uniform color space) with a consistent naming convention:

```css
--c00: oklch(0.15 0 0);  /* Darkest */
--c24: oklch(0.42 0 0);  /* Secondary text */
--c99: oklch(0.99 0 0);  /* Lightest */
```

This approach ensures consistent visual weight across the palette and makes it trivial to adjust the entire scheme by modifying a few variables.

### Modular Typography Scale

Font sizes follow a mathematical ratio (Perfect Fourth, 1.333), creating natural visual hierarchy without arbitrary values:

```css
h1: scale^5  /* ~4.2× base */
h2: scale^4  /* ~3.2× base */
h3: scale^3  /* ~2.4× base */
h4: scale^2  /* ~1.8× base */
```

The scale adapts to viewport size—smaller ratio on mobile to prevent headlines from dominating, larger base size on desktop for comfortable reading.

### Consistent Spacing

All spacing uses a defined scale rather than arbitrary pixel values:

```css
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;      /* 16px */
--space-lg: 1.5rem;    /* 24px */
--space-xl: 2rem;      /* 32px */
```

This creates visual rhythm and makes the design feel cohesive. It also makes future modifications predictable—changing one variable updates spacing consistently throughout.

## What This Project Demonstrates

Building this portfolio gave me an opportunity to demonstrate values that don't always come through in a traditional CV:

**Thoughtful decision-making.** Choosing to avoid frameworks wasn't about lacking knowledge—it was about matching the solution to the problem. I can discuss the tradeoffs of any approach.

**User empathy.** From accessibility features to timezone-aware availability indicators, every decision considered the person on the other end.

**Attention to detail.** Print styles, focus management, color contrast ratios—the invisible details that distinguish professional work from quick prototypes.

**Clear communication.** The code is documented, the structure is logical, and this article explains the reasoning behind decisions. I believe in work that can be understood and maintained by others.

**International perspective.** Native-level support for three languages reflects my experience working across cultures and my respect for diverse users.

## See It in Action

The portfolio is live at [luciano-pereira.pages.dev](https://luciano-pereira.pages.dev/). I encourage you to:

- Click "View Source" to see the actual code
- Switch languages to see the full localization
- Try navigating with only the keyboard
- Print the page to see the optimized output
- Open DevTools and inspect the structure

The page is designed to withstand scrutiny because good work should be transparent.

---

*This portfolio was built with HTML, CSS, and JavaScript—demonstrating that solid fundamentals and thoughtful design can deliver professional results without unnecessary complexity.*
