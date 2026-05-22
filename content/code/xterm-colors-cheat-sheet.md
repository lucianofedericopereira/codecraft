---
title: "xterm Colors Cheat Sheet: All 256 Colors, One Click Away"
date: 2026-03-04
comments: true
---

**xterm Colors Cheat Sheet**: An interactive HTML reference for all 256 xterm terminal colors — click any color name, hex value, RGB, or HSL to copy it to your clipboard. Built with vanilla JavaScript, CSS, and HTML.

## Why Another Color Reference

The existing xterm color references are static. They show you the colors; they don't help you use them. You see the color you want, read the ANSI code, type it into your terminal, get it wrong, look it up again.

The cheat sheet is interactive. Every value is a button. Click a hex code and it's in your clipboard. Click an RGB value and it's in your clipboard. Click the ANSI code number and it's in your clipboard. No copying, no mistyping, no looking up again.

## The 256-Color Palette Structure

The xterm 256-color palette has a logical structure that most references don't explain:

**Colors 0–7**: The standard 8 ANSI colors. Black, red, green, yellow, blue, magenta, cyan, white. These are the ones your terminal theme controls — they vary between terminal themes.

**Colors 8–15**: The high-intensity variants of the standard colors — "bright black" (dark gray), bright red, bright green, etc. Also theme-controlled.

**Colors 16–231**: A 6×6×6 RGB color cube. The three components each step through 0, 95, 135, 175, 215, 255. This gives you 216 colors with even distribution across the visible gamut.

```javascript
// Formula: color index = 16 + 36r + 6g + b
// where r, g, b are in range 0–5
function cubeColor(r, g, b) {
  const values = [0, 95, 135, 175, 215, 255];
  return {
    index: 16 + 36 * r + 6 * g + b,
    hex: `#${values[r].toString(16).padStart(2,'0')}` +
             `${values[g].toString(16).padStart(2,'0')}` +
             `${values[b].toString(16).padStart(2,'0')}`,
  };
}
```

**Colors 232–255**: A grayscale ramp from dark gray (232) to light gray (255). Not pure black or white — those are in the 0–7 range.

## The Interactive Interface

Each color is a card showing:
- The color swatch (click to copy the hex)
- The ANSI index number (click to copy for use in escape sequences)
- The hex value (click to copy)
- The RGB value (click to copy)
- The HSL value (click to copy)
- The common name if one exists

```javascript
function copyToClipboard(text, element) {
  navigator.clipboard.writeText(text).then(() => {
    const original = element.textContent;
    element.textContent = 'Copied!';
    element.classList.add('copied');
    setTimeout(() => {
      element.textContent = original;
      element.classList.remove('copied');
    }, 1500);
  });
}

document.querySelectorAll('[data-copy]').forEach(el => {
  el.addEventListener('click', () => copyToClipboard(el.dataset.copy, el));
});
```

The visual feedback — "Copied!" for 1.5 seconds — confirms the action without an alert dialog.

## Using Colors in Terminal Applications

The copied values are useful in different contexts:

**In bash escape sequences** (the ANSI index):
```bash
# Foreground color 208 (orange)
echo -e "\e[38;5;208mHello\e[0m"

# Background color 236 (dark gray)
echo -e "\e[48;5;236m Hello \e[0m"
```

**In CSS for terminal emulators** (the hex):
```css
.terminal { background-color: #1c1c1c; }  /* color 234 */
.keyword   { color: #d7875f; }             /* color 173 */
```

**In Python with curses** (the index):
```python
curses.init_pair(1, 208, 236)  # orange on dark gray
stdscr.addstr(0, 0, "Hello", curses.color_pair(1))
```

**In Vim/Neovim colorscheme** (the index or hex):
```vim
highlight Keyword ctermfg=208 guifg=#d7875f
```

## Search and Filter

The interface includes a search box that filters colors by name, hex value, or ANSI index as you type:

```javascript
const searchInput = document.querySelector('#color-search');
const cards = document.querySelectorAll('.color-card');

searchInput.addEventListener('input', () => {
  const query = searchInput.value.toLowerCase();
  cards.forEach(card => {
    const matches =
      card.dataset.name.toLowerCase().includes(query) ||
      card.dataset.hex.toLowerCase().includes(query)  ||
      card.dataset.index.includes(query);
    card.style.display = matches ? '' : 'none';
  });
});
```

Searching "orange" shows all colors whose names include "orange". Searching "ff5f" shows any color whose hex contains that substring. Searching "208" shows color 208 directly.

## No Dependencies

The entire tool is HTML, CSS, and vanilla JavaScript. No build step, no framework, no bundler. Open the HTML file in a browser and it works. Host it anywhere that serves static files.

This is intentional: a reference tool should be maximally accessible. You might want to run it locally without internet access, on a server without Node.js, or in an environment where installing packages is restricted.

## Links

- **GitHub**: [lucianofedericopereira/xterm-colors-cheat-sheet](https://github.com/lucianofedericopereira/xterm-colors-cheat-sheet)
- **Live**: [lucianofedericopereira.github.io/xterm-colors-cheat-sheet](https://lucianofedericopereira.github.io/xterm-colors-cheat-sheet)

## License

MIT
