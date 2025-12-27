---
title: "JavaScript Email Obfuscation with XOR Encoding"
date: 2024-10-25
comments: true
toc: true
---

Email harvesters and bots constantly scan the Internet for email addresses to add to spam lists. While there's no perfect solution, XOR-based obfuscation provides a lightweight way to protect email addresses from basic scrapers while keeping them accessible to humans.

## Background

Platforms like Cloudflare use email obfuscation to prevent harvesting. While researching protection methods, I discovered an article by Andrew Lock<a href="#footnote1" aria-label="Footnote 1"></a> describing a simple XOR-based encoding approach.

**XOR** (exclusive OR) is a logical operation that returns `true` when its two inputs differ. This makes XOR perfect for reversible encryption: applying the same operation twice returns the original value.

```
Original:  01001000 (H)
Key:       10101010
XOR 1st:   11100010 (encoded)
XOR 2nd:   01001000 (H) ← Back to original!
```

## How It Works

Select a numeric key between 0 and 255. For each character in the email:

1. Get its ASCII code (e.g., `'h'.charCodeAt(0)` = `104`)
2. XOR it with the key: `104 ^ 156 = 244`
3. Convert to hex: `244.toString(16)` = `'f4'`

Example with `key = 156`:

```
Original: hello@example.com
Key: 156 (0x9C)
Result: 9c f4 f9 f0 f0 f1 d3 f9 e8 f7 f1 f6 f0 f9 dd f9 f1 f6
```

## The Encoder Function

```js
const encodeEmail = (email, key) => {
  const keyHex = key.toString(16).padStart(2, '0');
  const encoded = [...email]
    .map(char => (char.charCodeAt(0) ^ key).toString(16).padStart(2, '0'))
    .join('');
  return keyHex + encoded;
};
```

## The Decoder Function

```js
const decodeEmail = (encoded) => {
  const key = parseInt(encoded.slice(0, 2), 16);
  return encoded
    .slice(2)
    .match(/.{1,2}/g)
    .map(hex => String.fromCharCode(parseInt(hex, 16) ^ key))
    .join('');
};
```

## HTML Integration

Store encoded emails in `data-` attributes:

```html
<a href="#" class="eml" data-encoded="9cf4f9f0f0f1d3f9e8f7f1f6f0f9ddf9f1f6">
  [contact]
</a>
```

## The Parser Function

Decode all emails on page load:

```js
const parseEmails = (className = 'eml') => {
  const emailElements = document.getElementsByClassName(className);

  for (const element of emailElements) {
    const { encoded } = element.dataset;
    if (!encoded) continue;

    try {
      const decoded = decodeEmail(encoded);
      element.textContent = decoded;
      element.href = `mailto:${decoded}`;
    } catch (error) {
      console.error('Failed to decode email:', error);
    }
  }
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', parseEmails);
} else {
  parseEmails();
}
```

## Interactive Example

Try encoding your own email address:

[example:1]

## Production Script

Here's the production-ready version with error handling and validation:

```js
function decodeEmails({ cls = 'eml', regex = null } = {}) {
  const decode = (encoded) => {
    if (!encoded || encoded.length < 4 || encoded.length % 2 !== 0) {
      return '';
    }

    try {
      const key = parseInt(encoded.slice(0, 2), 16);
      let result = '';
      for (let i = 2; i < encoded.length; i += 2) {
        const byte = parseInt(encoded.slice(i, i + 2), 16);
        result += String.fromCharCode(byte ^ key);
      }

      if (regex && !regex.test(result)) {
        console.warn('Decoded email failed validation:', result);
        return '';
      }

      return result;
    } catch (error) {
      console.error('Decode error:', error);
      return '';
    }
  };

  const processEmails = () => {
    const elements = document.getElementsByClassName(cls);
    for (const element of elements) {
      const encoded = element.dataset?.encoded;
      if (!encoded) continue;

      const decoded = decode(encoded);
      if (decoded) {
        element.textContent = decoded;
        element.href = `mailto:${decoded}`;
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processEmails);
  } else {
    processEmails();
  }
}
```

Usage:

```js
decodeEmails();
decodeEmails({ cls: 'email-link' });
decodeEmails({ cls: 'eml', regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ });
```

## Minified Version

For production use (optimized, 442 bytes):

```js
function decodeEmails({cls='eml',regex=null}={}){const d=e=>{if(!e||e.length<4
||e.length%2)return'';try{const k=parseInt(e.slice(0,2),16);let r='';for(let i=2;i<e.length;i+=2)r+=String.fromCharCode(parseInt(e.slice(i,i+2),16)^k);return regex&&!regex.test(r)?'':r}catch{return''}};const p=()=>{for(const el of document.getElementsByClassName(cls)){const x=d(el.dataset?.encoded);x&&
(el.textContent=x,el.href='mailto:'+x)}};'loading'===document.readyState?document.addEventListener('DOMContentLoaded',p):p()}
```

## Security Considerations

**Important:** This is obfuscation, not encryption.

**What it protects against:**
- Basic email scrapers looking for `mailto:` links
- Simple regex-based harvesters
- Automated bots that don't execute JavaScript

**What it doesn't protect against:**
- Determined attackers
- Bots that execute JavaScript
- Manual copying from rendered page
- Browser view-source (encoded string is visible)

**Best used in combination with:**
- Contact forms (preferred method)
- CAPTCHA/reCAPTCHA
- Rate limiting on server side
- Honeypot fields

## Browser Compatibility

All modern browsers (Chrome 60+, Firefox 55+, Safari 11+, Edge 79+)

For older browsers, transpile with Babel.

### Footnotes

<footer>
  <p id="footnote1"><a href="https://andrewlock.net">Andrew Lock</a> .NET Escapades.</p>
</footer>

**License:** Code examples in this article are released under GPL v2.
