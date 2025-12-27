// Constants
const CONFIG = {
    READING_SPEED: 150, // words per minute
    DEBOUNCE_DELAY: 1500,
    LANG_SWITCH_DELAY: 2000,
    LANG_CHECK_TIMEOUT: 5000,
    LANG_CHECK_INTERVAL: 100,
    SEARCH_MIN_LENGTH: 2,
    SEARCH_BATCH_SIZE: 10,
    SEARCH_BATCH_DELAY: 100,
    COPY_FEEDBACK_DURATION: 4000,
    ASIDE_TRANSITION_DELAY: 10,
    CLOCK_INTERVAL: 1000,
    DESKTOP_WIDTH: 1280,
    SEARCH_PREVIEW_LENGTH: 100,
    DEFAULT_CODEPEN_HEIGHT: '300',
    DEFAULT_CODEPEN_TAB: 'html,result',
    DEFAULT_CODEPEN_USER: 'lucianofedericopereira'
};

// Utility functions
const $ = selector => document.querySelector(selector);
const $$ = selector => document.querySelectorAll(selector);

const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
};

const pad = num => num.toString().padStart(2, '0');

const parseMetaConfig = (name, delimiter = '|', pairDelimiter = '=') => {
    const metaTag = $(`meta[name="${name}"]`);
    if (!metaTag?.content) return null;
    return Object.fromEntries(
        metaTag.content.split(delimiter).map(pair => pair.split(pairDelimiter))
    );
};

const addStyles = content => {
    if (!content) return;
    const style = document.createElement('style');
    style.textContent = content;
    document.head.appendChild(style);
};

const loadScript = async src => {
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    document.head.appendChild(script);
    return new Promise((resolve, reject) => {
        script.onload = resolve;
        script.onerror = reject;
    });
};

// DOM Utilities
const createObserver = (callback, options = { childList: true, subtree: true }) => {
    const observer = new MutationObserver(mutations => {
        if (mutations.some(m => m.addedNodes.length > 0)) {
            callback();
        }
    });
    observer.observe(document.body, options);
    callback(); // Initial call
    return observer;
};

const removeFontTags = () => {
    $$('font').forEach(fontTag => {
        while (fontTag.firstChild) {
            fontTag.parentNode.insertBefore(fontTag.firstChild, fontTag);
        }
        fontTag.remove();
    });
};

// Clock functionality
const updateClock = () => {
    const now = new Date();
    const hours = pad(now.getHours());
    const minutes = pad(now.getMinutes());
    const separator = now.getSeconds() & 1 ? '\u200A\u2005' : ':';
    document.title = `design﹢code \u203A ${hours}${separator}${minutes}`;
};

// Custom Elements
const defineCodePenElement = () => {
    if (customElements.get('code-pen')) return;

    class CodePenElement extends HTMLElement {
        constructor() {
            super();
            if (!this.hasAttribute('data-height')) {
                this.setAttribute('data-height', CONFIG.DEFAULT_CODEPEN_HEIGHT);
            }
            if (!this.hasAttribute('data-default-tab')) {
                this.setAttribute('data-default-tab', CONFIG.DEFAULT_CODEPEN_TAB);
            }
            if (!this.hasAttribute('data-user')) {
                this.setAttribute('data-user', CONFIG.DEFAULT_CODEPEN_USER);
            }
        }

        connectedCallback() {
            this.innerHTML = `<div class="codepen"
                data-height="${this.getAttribute('data-height')}"
                data-default-tab="${this.getAttribute('data-default-tab')}"
                data-slug-hash="${this.getAttribute('data-slug-hash')}"
                data-user="${this.getAttribute('data-user')}">
              </div>`;
        }
    }

    customElements.define('code-pen', CodePenElement);
};

// Google Translate - CRITICAL: Maintain exact structure for Google's requirements
// IMPORTANT: Use var for variables accessed across iframe boundaries by Google Translate
const initializeTranslate = () => {
    // IMPORTANT: This function is called by Google's script via window.translate
    // Do not modify the callback structure
    new google.translate.TranslateElement({
        pageLanguage: 'en',
        autoDisplay: false,
        layout: google.translate.TranslateElement.InlineLayout.VERTICAL
    }, 'translate');

    // Security: Add noopener to Google's logo link
    $('.goog-logo-link')?.setAttribute('rel', 'noopener');

    var googleCombo = $('select.goog-te-combo');
    var translateDropdown = $('#translate-dropdown');
    var menu = $('#menu');
    var isMobile = window.innerWidth < CONFIG.DESKTOP_WIDTH;

    if (!googleCombo) return;

    // Event dispatcher for cross-browser compatibility
    const triggerEvent = (element, eventName) => {
        const event = new Event(eventName, { bubbles: true, cancelable: true });
        element.dispatchEvent(event);
    };

    // Debounced language change to prevent rapid switches
    const changeLanguage = debounce(lang => {
        googleCombo.value = lang;
        triggerEvent(googleCombo, 'change');
    }, CONFIG.DEBOUNCE_DELAY);

    // Language selection handlers
    $$('.lang-select').forEach(link => {
        link.addEventListener('click', event => {
            event.preventDefault();
            const lang = event.target.getAttribute('hreflang');
            if (!lang) return;

            // Update UI
            $('.lang-select.aside-selected')?.classList.remove('aside-selected');
            event.target.classList.add('aside-selected');

            // Trigger language change
            changeLanguage(lang);

            // Auto-close menus
            setTimeout(() => {
                translateDropdown.checked = false;
                if (isMobile) menu.checked = false;
            }, CONFIG.LANG_SWITCH_DELAY);
        });
    });

    // Sync selected language from Google Translate combo
    const syncInterval = setInterval(() => {
        const selectedLang = googleCombo.value;
        if (selectedLang) {
            const langLink = $(`.lang-select[hreflang="${selectedLang}"]`);
            if (langLink) {
                $('.lang-select.aside-selected')?.classList.remove('aside-selected');
                langLink.classList.add('aside-selected');
            }
            clearInterval(syncInterval);
        }
    }, CONFIG.LANG_CHECK_INTERVAL);

    setTimeout(() => clearInterval(syncInterval), CONFIG.LANG_CHECK_TIMEOUT);

    // Override Google Translate's tooltip functions (they interfere with UI)
    const overrideTooltips = (retries = 20, interval = 150) => {
        let attempts = 0;
        const timer = setInterval(() => {
            if (typeof window._tipoff === 'function' && typeof window._tipon === 'function') {
                window._tipoff = () => {};
                window._tipon = () => {};
                clearInterval(timer);
            } else if (++attempts >= retries) {
                clearInterval(timer);
            }
        }, interval);
    };

    overrideTooltips();
};

// Mermaid diagrams
const initializeMermaid = () => {
    const config = parseMetaConfig('mermaid');
    if (!config?.version) return;

    const script = document.createElement('script');
    script.type = 'module';
    script.defer = true;
    script.textContent = `
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@${config.version}/+esm';
        mermaid.initialize({ startOnLoad: true, theme: 'forest' });
        mermaid.run({ querySelector: '.language-mermaid' }).then(() => {
            document.querySelectorAll('.language-mermaid').forEach(el => {
                el.classList.add('mermaid-loaded');
            });
        });
    `;
    document.body.appendChild(script);
};

// Table of Contents
const createTOC = () => {
    const metaTag = $('meta[name="toc"]');
    if (!metaTag || metaTag.content !== 'enabled') return;

    updateReadingTime();

    const chaptersContainer = $('#chapters');
    if (!chaptersContainer) return;

    const headings = $$('main h2');

    if (headings.length > 0) {
        // Add TOC heading if not present
        let tocHeading = chaptersContainer.previousElementSibling;
        if (!tocHeading || tocHeading.tagName !== 'H3') {
            tocHeading = document.createElement('h3');
            tocHeading.textContent = 'Table of Contents';
            chaptersContainer.before(tocHeading);
        }

        // Add separator if not present
        let tocSeparator = chaptersContainer.nextElementSibling;
        if (!tocSeparator || tocSeparator.tagName !== 'HR') {
            tocSeparator = document.createElement('hr');
            chaptersContainer.after(tocSeparator);
        }

        // Build TOC
        chaptersContainer.innerHTML = '';
        headings.forEach((heading, index) => {
            heading.id = `chapter-${index + 1}`;
            const link = document.createElement('a');
            link.href = `#${heading.id}`;
            link.innerHTML = `<span>${heading.textContent}</span>`;

            link.addEventListener('click', event => {
                event.preventDefault();
                const target = $(`#${heading.id}`);
                target?.scrollIntoView({ behavior: 'smooth' });
            });

            chaptersContainer.appendChild(link);
        });
    } else {
        // Clean up empty TOC
        chaptersContainer.previousElementSibling?.remove();
        chaptersContainer.nextElementSibling?.remove();
        chaptersContainer.innerHTML = '';
    }
};

const updateReadingTime = () => {
    const mainText = $('main')?.innerText.replace(/\s+/g, ' ').trim();
    if (!mainText) return;

    const wordCount = mainText.split(' ').length;
    const readingTime = Math.ceil(wordCount / CONFIG.READING_SPEED);
    const author = $('meta[name="author"]')?.content || 'Unknown';
    const license = $('meta[name="license"]')?.content || 'All rights reserved';
    const date = $('meta[name="date"]')?.content || '';

    const readingTimeEl = $('#reading-time');
    if (readingTimeEl) {
        readingTimeEl.innerHTML = `<b>${author}</b> | ${date} | ~<b>${readingTime}</b> min read | ${license}`;
    }
};

// Comments
const loadComments = () => {
    const config = parseMetaConfig('comments-config');
    if (!config?.repo || !config?.src) return;

    const { theme = 'github-light', issue = 'title', repo, src } = config;
    const commentsDiv = $('#comments-utteranc');
    if (!commentsDiv) return;

    const script = Object.assign(document.createElement('script'), {
        src,
        async: true,
        crossOrigin: 'anonymous'
    });

    script.setAttribute('theme', theme);
    script.setAttribute('issue-term', issue);
    script.setAttribute('repo', repo);

    commentsDiv.appendChild(script);
};

// Clipboard functionality
const setupClipboard = () => {
    if (!navigator.clipboard) return;

    const icons = {
        copy: `<svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" class="bi bi-clipboard" viewBox="0 0 16 16">
            <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
            <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
        </svg>`,
        copied: `<svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" class="bi bi-clipboard-check-fill" viewBox="0 0 16 16">
            <path d="M6.5 0A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3Zm3 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3Z"/>
            <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1A2.5 2.5 0 0 1 9.5 5h-3A2.5 2.5 0 0 1 4 2.5v-1Zm6.854 7.354-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 0 1 .708-.708L7.5 10.793l2.646-2.647a.5.5 0 0 1 .708.708Z"/>
        </svg>`
    };

    $$('div.highlighter-rouge, div.listingblock > div.content, figure.highlight').forEach(codeBlock => {
        const button = document.createElement('button');
        button.type = 'button';
        button.setAttribute('aria-label', 'Copy code to clipboard');
        button.innerHTML = icons.copy;

        button.addEventListener('click', async () => {
            const codeElement = codeBlock.querySelector('pre:not(.lineno, .highlight)') || codeBlock.querySelector('code');
            const codeText = codeElement?.innerText;

            if (!codeText) return;

            try {
                await navigator.clipboard.writeText(codeText);
                button.innerHTML = icons.copied;
                setTimeout(() => button.innerHTML = icons.copy, CONFIG.COPY_FEEDBACK_DURATION);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });

        codeBlock.appendChild(button);
    });
};

// Build search index from documents
const buildSearchIndex = (lunrInstance, docs) => {
    lunrInstance.tokenizer.separator = /[\s/]+/;
    return lunrInstance(function() {
        this.ref('id');
        this.field('title', { boost: 200 });
        this.field('content', { boost: 2 });
        this.metadataWhitelist = ['position'];

        Object.keys(docs).forEach(key => {
            this.add({
                id: key,
                title: docs[key].title,
                content: docs[key].content
            });
        });
    });
};

// Perform search with fallback to fuzzy search
const performSearch = (index, lunrInstance, input) => {
    // Primary search
    let results = index.query(query => {
        const tokens = lunrInstance.tokenizer(input);
        query.term(tokens, { boost: 10 });
        query.term(tokens, { wildcard: lunrInstance.Query.wildcard.TRAILING });
    });

    // Fuzzy search fallback
    if (!results.length && input.length > CONFIG.SEARCH_MIN_LENGTH) {
        const tokens = lunrInstance.tokenizer(input).filter(token => token.str.length < 20);
        if (tokens.length) {
            results = index.query(query => {
                query.term(tokens, { editDistance: Math.round(Math.sqrt(input.length / 2 - 1)) });
            });
        }
    }

    return results;
};

// Render search results in batches
const renderSearchResults = (list, results, start, currentSearchIndex, searchIndexRef, docs, searchInput, searchResults) => {
    if (currentSearchIndex !== searchIndexRef.current) return;

    const end = Math.min(start + CONFIG.SEARCH_BATCH_SIZE, results.length);
    for (let i = start; i < end; i++) {
        const result = results[i];
        const doc = docs[result.ref];

        const item = document.createElement('li');
        item.classList.add('search-results-list-item');

        const link = document.createElement('a');
        link.classList.add('search-result');
        link.href = doc.url;
        link.addEventListener('click', event => {
            event.preventDefault();
            searchInput.value = '';
            searchResults.innerHTML = '';
            setTimeout(() => window.location.href = link.href, 10);
        });

        const title = document.createElement('div');
        title.classList.add('search-result-title');
        title.textContent = doc.title;
        link.appendChild(title);

        if (doc.content) {
            const preview = document.createElement('div');
            preview.classList.add('search-result-previews');
            const previewText = doc.content.slice(0, CONFIG.SEARCH_PREVIEW_LENGTH);
            const previewContent = document.createElement('div');
            previewContent.classList.add('search-result-preview');
            previewContent.textContent = `${previewText}…`;
            preview.appendChild(previewContent);
            link.appendChild(preview);
        }

        item.appendChild(link);
        list.appendChild(item);
    }

    if (end < results.length) {
        setTimeout(
            () => renderSearchResults(list, results, end, currentSearchIndex, searchIndexRef, docs, searchInput, searchResults),
            CONFIG.SEARCH_BATCH_DELAY
        );
    }
};

// Setup keyboard shortcuts for search
const setupSearchKeyboardShortcuts = (searchInput, menu, hideSearchFn) => {
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            menu.checked = true;
            searchInput.focus();
        }
        if (e.key === 'Escape') {
            hideSearchFn();
            searchInput.blur();
            menu.checked = false;
        }
    });
};

// Search functionality
const initializeSearch = async lunrInstance => {
    const searchInput = $('#search-input');
    const searchResults = $('#search-results');
    const metaTag = $('meta[name="search"]');
    const menu = $('#menu');

    if (!searchInput || !searchResults || !metaTag?.content) return;

    let currentInput = '';
    const searchIndexRef = { current: 0 };

    try {
        const response = await fetch(metaTag.content);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const docs = await response.json();
        const index = buildSearchIndex(lunrInstance, docs);

        const showSearch = () => document.documentElement.classList.add('search-active');
        const hideSearch = () => {
            document.documentElement.classList.remove('search-active');
            searchInput.value = '';
            searchResults.innerHTML = '';
            searchResults.style.display = 'none';
        };

        setupSearchKeyboardShortcuts(searchInput, menu, hideSearch);

        // Search input handler
        searchInput.addEventListener('input', () => {
            const input = searchInput.value.trim();

            if (input.length === 0) {
                hideSearch();
                return;
            }

            if (input.length < CONFIG.SEARCH_MIN_LENGTH) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
                return;
            }

            if (input === currentInput) return;

            currentInput = input;
            searchIndexRef.current++;
            searchResults.innerHTML = '';
            searchResults.style.display = 'block';
            showSearch();

            const results = performSearch(index, lunrInstance, input);

            if (results.length === 0) {
                searchResults.innerHTML = '<div class="search-no-result">No results found</div>';
            } else {
                const resultsList = document.createElement('ul');
                resultsList.classList.add('search-results-list');
                searchResults.appendChild(resultsList);
                renderSearchResults(resultsList, results, 0, searchIndexRef.current, searchIndexRef, docs, searchInput, searchResults);
            }
        });

        // Close on blur
        searchInput.addEventListener('blur', event => {
            if (!searchResults.contains(event.relatedTarget)) {
                hideSearch();
            }
        });

        // Watch for visibility changes
        const observer = new MutationObserver(() => {
            if (window.getComputedStyle(searchInput).display === 'none') {
                hideSearch();
            }
        });
        observer.observe(searchInput, { attributes: true, attributeFilter: ['style'] });

    } catch (error) {
        console.error('Search initialization failed:', error);
    }
};

// Clickable elements
const setupClickableElements = () => {
    $$('[data-clickable]').forEach(element => {
        element.style.cursor = 'pointer';
        element.addEventListener('click', function(event) {
            const href = this.getAttribute('data-href');
            if (href) {
                event.stopPropagation();
                window.location.href = href;
            } else {
                const link = this.querySelector('a');
                if (link) window.location.href = link.href;
            }
        });
    });
};

// UI Enhancements
const setupUIEnhancements = () => {
    // Set initial menu state based on screen size
    const menuCheckbox = $('#menu');
    if (menuCheckbox) {
        menuCheckbox.checked = window.innerWidth >= CONFIG.DESKTOP_WIDTH;
    }

    // Make footer paragraphs clickable
    $$('main footer p').forEach(p => {
        p.addEventListener('click', () => {
            p.querySelector('a')?.click();
        });
    });

    // Inline hover styles
    addStyles(`
        main footer p:hover {
            cursor: pointer;
            color: var(--c0);
        }
        main footer p:hover::before {
            color: var(--c2);
        }
        .dropbtn {
            cursor: pointer;
        }
        main footer p:hover a {
            text-decoration-style: solid;
            text-decoration-color: var(--c3);
        }
        .entry:hover .title a b {
            color: var(--r0);
        }
        .entry:hover p .section-tag {
            background-color: var(--r0);
            color: var(--c7);
        }
        .entry:hover .date-tag {
            color: var(--c1);
        }
        .entry:hover p {
            color: var(--c0);
        }
    `);

    // Add aside transition after initial render
    setTimeout(() => {
        addStyles('aside { transition: all 300ms ease-in-out; }');
    }, CONFIG.ASIDE_TRANSITION_DELAY);
};

// PJAX-like navigation for smooth page transitions
const setupPJAX = () => {
    const contentSelector = 'main';
    let isNavigating = false;

    // Intercept link clicks
    document.addEventListener('click', async (e) => {
        const link = e.target.closest('a');
        if (!link) return;

        const url = link.getAttribute('href');

        // Only intercept internal links
        if (!url ||
            url.startsWith('http://') ||
            url.startsWith('https://') ||
            url.startsWith('#') ||
            url.startsWith('mailto:') ||
            link.hasAttribute('download') ||
            link.target === '_blank') {
            return;
        }

        e.preventDefault();

        // Prevent rapid clicks
        if (isNavigating) return;
        isNavigating = true;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Extract the new content
            const newContent = doc.querySelector(contentSelector);
            const currentContent = document.querySelector(contentSelector);

            if (newContent && currentContent) {
                // Update content with fade effect
                currentContent.style.opacity = '0';

                setTimeout(() => {
                    currentContent.innerHTML = newContent.innerHTML;

                    // Update page title
                    const newTitle = doc.querySelector('title');
                    if (newTitle) document.title = newTitle.textContent;

                    // Update meta tags
                    const newMeta = doc.querySelectorAll('meta[name="description"], meta[property^="og:"]');
                    newMeta.forEach(meta => {
                        const existing = document.querySelector(`meta[name="${meta.name}"], meta[property="${meta.getAttribute('property')}"]`);
                        if (existing) {
                            existing.setAttribute('content', meta.getAttribute('content'));
                        }
                    });

                    // Re-initialize components for new content
                    createTOC();
                    setupClipboard();
                    setupClickableElements();
                    initializeMermaid();
                    loadComments();
                    removeFontTags();

                    // Scroll to top
                    window.scrollTo({ top: 0, behavior: 'smooth' });

                    // Update URL
                    history.pushState({ path: url }, '', url);

                    // Fade in
                    currentContent.style.opacity = '1';
                    isNavigating = false;
                }, 150);
            } else {
                // Fallback to normal navigation
                window.location.href = url;
            }
        } catch (err) {
            console.error('PJAX navigation error:', err);
            window.location.href = url;
        }
    });

    // Handle back/forward navigation
    window.addEventListener('popstate', async (e) => {
        // Ignore popstate on initial page load
        if (!e.state) {
            return;
        }

        if (isNavigating) return;
        isNavigating = true;

        try {
            const response = await fetch(location.href);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const newContent = doc.querySelector(contentSelector);
            const currentContent = document.querySelector(contentSelector);

            if (newContent && currentContent) {
                currentContent.style.opacity = '0';

                setTimeout(() => {
                    currentContent.innerHTML = newContent.innerHTML;

                    const newTitle = doc.querySelector('title');
                    if (newTitle) document.title = newTitle.textContent;

                    createTOC();
                    setupClipboard();
                    setupClickableElements();
                    initializeMermaid();
                    loadComments();
                    removeFontTags();

                    window.scrollTo({ top: 0, behavior: 'smooth' });

                    currentContent.style.opacity = '1';
                    isNavigating = false;
                }, 150);
            } else {
                window.location.reload();
            }
        } catch (err) {
            console.error('PJAX popstate error:', err);
            window.location.reload();
        }
    });

    // Add CSS transition for smooth fade
    addStyles(`
        main {
            transition: opacity 150ms ease-in-out;
        }
    `);
};

// Create a toggle pair with ARIA attributes
const createToggle = (toggleEl, targetEl) => {
    if (!toggleEl || !targetEl) return;

    toggleEl.addEventListener('click', () => {
        const isExpanded = toggleEl.getAttribute('aria-expanded') === 'true';
        toggleEl.setAttribute('aria-expanded', !isExpanded);
        targetEl.setAttribute('aria-hidden', isExpanded);
    });
};

// Toggle functionality for buttons
const setupToggles = () => {
    // Menu toggle - handles 3 viewport states:
    // 1. Mobile (< 575px): Slide from top, closed by default
    // 2. Tablet (575px - 1024px): Slide from left, closed by default
    // 3. Desktop (>= 1024px): Slide from left, OPEN by default
    const menuToggle = $('#menu-toggle');
    const menu = $('#menu');
    if (menuToggle && menu) {
        const isDesktop = () => window.innerWidth >= 1024; // 64rem = 1024px

        // Set initial state based on screen size
        const setInitialMenuState = () => {
            if (isDesktop()) {
                // Desktop: open by default
                menu.setAttribute('aria-hidden', 'false');
                menuToggle.setAttribute('aria-expanded', 'true');
            } else {
                // Mobile & Tablet: closed by default
                menu.setAttribute('aria-hidden', 'true');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        };

        setInitialMenuState();

        // Handle resize without animation
        let resizeTimer;
        window.addEventListener('resize', () => {
            // Disable transitions during resize
            menu.classList.remove('transitions-enabled');
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                setInitialMenuState();
                // Re-enable transitions after resize is done
                menu.classList.add('transitions-enabled');
            }, 100);
        });

        // Enable transitions after initial page load
        setTimeout(() => {
            menu.classList.add('transitions-enabled');
        }, 100);

        createToggle(menuToggle, menu);
    }

    // TOC toggle
    createToggle($('#toc-toggle'), $('#index'));

    // Translate dropdown toggle
    createToggle($('#translate-toggle'), $('#translate-dropdown'));
};

// Example Viewer functionality
class ExampleViewer {
    constructor(container, exampleData) {
        this.container = container;
        this.html = exampleData.html;
        this.css = exampleData.css;
        this.js = exampleData.js;
        this.currentTab = 0;

        this.render();
        this.attachEvents();
    }

    // Add line numbers and basic syntax highlighting
    formatCode(code, lang) {
        const lines = code.split('\n');
        const formatted = lines.map((line, i) => {
            const lineNum = i + 1;
            const highlighted = this.highlightSyntax(line, lang);
            return `<span class="code-line"><span class="line-number">${lineNum}</span><span class="code-content">${highlighted}</span></span>`;
        }).join('');
        return formatted;
    }

    // Safe and robust syntax highlighting
    highlightSyntax(line, lang) {
        // Safety check: return empty or whitespace-only lines as-is
        if (!line || !line.trim()) return line;

        try {
            if (lang === 'html') return this.highlightHTML(line);
            if (lang === 'css') return this.highlightCSS(line);
            if (lang === 'js') return this.highlightJavaScript(line);
            return line;
        } catch (e) {
            // If highlighting fails, return original line safely
            console.error('Syntax highlighting error:', e);
            return line;
        }
    }

    // HTML syntax highlighting
    highlightHTML(line) {
        let result = line;
        const tagMatches = [];

        // Extract and save complete tags
        result = result.replace(/(&lt;[^&]*?&gt;)/g, (match) => {
            tagMatches.push(match);
            return `___TAG_${tagMatches.length - 1}___`;
        });

        // Process each tag safely
        const processedTags = tagMatches.map(tag => {
            let processed = tag;

            // Highlight attributes with values (handles both &quot; and regular quotes)
            processed = processed.replace(
                /\s+([a-zA-Z][-a-zA-Z0-9]*)\s*=\s*(?:(&quot;)([^&]*?)(&quot;)|(['"])([^'"]*?)(['"]))/g,
                (_match, attrName, dq1, dqVal, dq2, sq1, sqVal, sq2) => {
                    if (dq1) {
                        return ` <span class="hl-attr">${attrName}</span>=${dq1}<span class="hl-string">${dqVal}</span>${dq2}`;
                    } else {
                        return ` <span class="hl-attr">${attrName}</span>=${sq1}<span class="hl-string">${sqVal}</span>${sq2}`;
                    }
                }
            );

            // Highlight tag names
            processed = processed.replace(
                /^(&lt;\/?)([a-zA-Z][-a-zA-Z0-9]*)/,
                '$1<span class="hl-tag">$2</span>'
            );

            return processed;
        });

        // Restore processed tags
        result = result.replace(/___TAG_(\d+)___/g, (_match, index) => {
            return processedTags[parseInt(index)];
        });

        return result;
    }

    // CSS syntax highlighting
    highlightCSS(line) {
        let result = line;
        const trimmed = result.trim();

        // Selector line (ends with {)
        if (/\{\s*$/.test(trimmed)) {
            result = result.replace(/^(\s*)([.#]?[-a-zA-Z0-9_]+)(\s*\{\s*)$/,
                '$1<span class="hl-selector">$2</span>$3');
        }
        // Property with value (contains : and ;)
        else if (/:/.test(trimmed) && /;/.test(trimmed)) {
            result = result.replace(/^(\s*)([-a-zA-Z]+)(\s*:\s*)([^;]+)(;\s*)$/,
                '$1<span class="hl-property">$2</span>$3<span class="hl-value">$4</span>$5');
        }
        // Property without value yet
        else if (/:/.test(trimmed) && !/;/.test(trimmed)) {
            result = result.replace(/^(\s*)([-a-zA-Z]+)(\s*:\s*)(.*)$/,
                '$1<span class="hl-property">$2</span>$3$4');
        }

        return result;
    }

    // JavaScript syntax highlighting
    highlightJavaScript(line) {
        let result = line;
        const stringPlaceholders = [];
        const commentPlaceholders = [];

        // Save comments first
        result = result.replace(/\/\/.*/g, (match) => {
            commentPlaceholders.push(match);
            return `___COMMENT_${commentPlaceholders.length - 1}___`;
        });

        // Save strings (improved regex for escaped quotes)
        result = result.replace(/(["'`])(?:[^\\]|\\[\s\S])*?\1/g, (match) => {
            stringPlaceholders.push(match);
            return `___STRING_${stringPlaceholders.length - 1}___`;
        });

        // Highlight keywords (comprehensive list)
        const keywords = [
            'const', 'let', 'var', 'function', 'return', 'if', 'else',
            'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
            'class', 'extends', 'new', 'this', 'super', 'static',
            'async', 'await', 'try', 'catch', 'finally', 'throw',
            'import', 'export', 'default', 'from', 'as',
            'null', 'undefined', 'true', 'false',
            'typeof', 'instanceof', 'delete', 'void', 'in', 'of'
        ];

        const keywordPattern = new RegExp(`\\b(${keywords.join('|')})\\b`, 'g');
        result = result.replace(keywordPattern, '<span class="hl-keyword">$1</span>');

        // Restore strings with highlighting
        stringPlaceholders.forEach((str, index) => {
            result = result.replace(`___STRING_${index}___`, `<span class="hl-string">${str}</span>`);
        });

        // Restore comments with highlighting
        commentPlaceholders.forEach((comment, index) => {
            result = result.replace(`___COMMENT_${index}___`, `<span class="hl-comment">${comment}</span>`);
        });

        return result;
    }

    render() {
        // Create container structure
        const container = document.createElement('div');
        container.className = 'example-container';

        // Create left side (tabs)
        const tabsSection = document.createElement('div');
        tabsSection.className = 'example-tabs';

        const tablist = document.createElement('div');
        tablist.className = 'example-tablist';
        tablist.setAttribute('role', 'tablist');
        tablist.setAttribute('aria-label', 'Example code tabs');

        ['HTML', 'CSS', 'JavaScript'].forEach((label, index) => {
            const tab = document.createElement('button');
            tab.className = 'example-tab';
            tab.setAttribute('role', 'tab');
            tab.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
            tab.setAttribute('aria-controls', `panel-${label.toLowerCase()}`);
            tab.setAttribute('data-tab', index.toString());
            tab.textContent = label;
            tablist.appendChild(tab);
        });

        const panels = document.createElement('div');
        panels.className = 'example-panels';

        [this.html, this.css, this.js].forEach((content, index) => {
            const panel = document.createElement('div');
            panel.className = `example-panel${index === 0 ? ' active' : ''}`;
            panel.setAttribute('role', 'tabpanel');
            const lang = ['html', 'css', 'js'][index];
            const langLabel = ['HTML', 'CSS', 'JavaScript'][index];
            panel.setAttribute('id', `panel-${lang}`);
            panel.setAttribute('data-lang', langLabel);

            const pre = document.createElement('pre');
            const code = document.createElement('code');
            code.className = `language-${lang}`;

            // Escape HTML first
            const escaped = content.replace(/&/g, '&amp;')
                                 .replace(/</g, '&lt;')
                                 .replace(/>/g, '&gt;');

            // Apply formatting with line numbers and syntax highlighting
            code.innerHTML = this.formatCode(escaped, lang);

            pre.appendChild(code);
            panel.appendChild(pre);
            panels.appendChild(panel);
        });

        tabsSection.appendChild(tablist);
        tabsSection.appendChild(panels);

        // Create right side (preview)
        const previewSection = document.createElement('div');
        previewSection.className = 'example-preview';

        const label = document.createElement('div');
        label.className = 'example-preview-label';

        const labelText = document.createElement('span');
        labelText.textContent = 'Result';
        label.appendChild(labelText);

        // Add open in new tab button
        const openButton = document.createElement('button');
        openButton.className = 'example-open-tab';
        openButton.innerHTML = '↗';
        openButton.setAttribute('aria-label', 'Open example in new tab');
        openButton.setAttribute('title', 'Open in new tab');
        label.appendChild(openButton);

        const previewContent = document.createElement('div');
        previewContent.className = 'example-preview-content';

        const iframe = document.createElement('iframe');
        iframe.setAttribute('srcdoc', this.generatePreview());
        iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
        iframe.style.width = '100%';
        iframe.style.border = 'none';

        // Auto-adjust iframe height when content changes
        iframe.addEventListener('load', () => {
            const resizeIframe = () => {
                try {
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    const height = iframeDoc.documentElement.scrollHeight;
                    iframe.style.height = height + 'px';
                } catch (e) {
                    // Fallback if cross-origin restrictions apply
                    iframe.style.height = '600px';
                }
            };

            resizeIframe();

            // Re-adjust on any changes inside the iframe
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            if (iframeDoc) {
                const observer = new MutationObserver(resizeIframe);
                observer.observe(iframeDoc.body, {
                    childList: true,
                    subtree: true,
                    attributes: true
                });
            }
        });

        previewContent.appendChild(iframe);
        previewSection.appendChild(label);
        previewSection.appendChild(previewContent);

        // Handle open in new tab
        openButton.addEventListener('click', () => {
            const newWindow = window.open('', '_blank');
            newWindow.document.write(this.generatePreview());
            newWindow.document.close();
        });

        // Assemble
        container.appendChild(tabsSection);
        container.appendChild(previewSection);

        this.container.innerHTML = '';
        this.container.appendChild(container);
    }

    generatePreview() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>${this.css}</style>
</head>
<body>
    ${this.html}
    <script>${this.js}<\/script>
</body>
</html>`;
    }

    attachEvents() {
        const tabs = this.container.querySelectorAll('.example-tab');
        const panels = this.container.querySelectorAll('.example-panel');

        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                // Update tabs
                tabs.forEach(t => {
                    t.setAttribute('aria-selected', 'false');
                });
                tab.setAttribute('aria-selected', 'true');

                // Update panels
                panels.forEach(p => {
                    p.classList.remove('active');
                });
                panels[index].classList.add('active');

                this.currentTab = index;
            });
        });
    }
}

// Load a single example
const loadExample = async (container) => {
    const exampleId = container.getAttribute('data-example-id');

    try {
        // Fetch the example HTML file (use relative path to respect <base> tag)
        const response = await fetch(`examples/${exampleId}.html`);
        if (!response.ok) throw new Error(`Failed to load example ${exampleId}`);

        const htmlContent = await response.text();

        // Parse the HTML to extract CSS and JS
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlContent, 'text/html');

        // Extract CSS from <style id="example-css">
        const styleTag = doc.querySelector('style#example-css');
        const css = styleTag ? styleTag.textContent.trim() : '';

        // Extract JS from <script id="example-js">
        const scriptTag = doc.querySelector('script#example-js');
        const js = scriptTag ? scriptTag.textContent.trim() : '';

        // Extract HTML from <body> (excluding the script tag)
        const body = doc.querySelector('body');
        if (scriptTag) scriptTag.remove();
        const html = body ? body.innerHTML.trim() : '';

        // Initialize the viewer
        new ExampleViewer(container, { html, css, js });

        // Mark as loaded to remove loading state
        container.classList.add('loaded');

    } catch (error) {
        console.error(`Error loading example ${exampleId}:`, error);
        container.innerHTML = `<div style="padding: 1rem; color: red;">Error loading example ${exampleId}</div>`;
        container.classList.add('loaded'); // Remove loading state even on error
    }
};

// Initialize example viewers
const initializeExamples = async () => {
    const exampleContainers = $$('.example-viewer[data-example-id]');

    // Load all examples in parallel and wait for all to complete
    await Promise.allSettled(
        Array.from(exampleContainers).map(container => loadExample(container))
    );
};

// Main initialization
export const codeCraft = {
    init: async function(lunrInstance) {
        setupPJAX();
        setupToggles();
        setupUIEnhancements();
        initializeMermaid();
        createTOC();
        setupClipboard();
        setupClickableElements();
        await initializeExamples();
        await initializeSearch(lunrInstance);
        loadComments();
        createObserver(removeFontTags);
        defineCodePenElement();

        // CRITICAL: Google Translate requires window.translate callback
        window.translate = initializeTranslate;
        loadScript('https://translate.google.com/translate_a/element.js?cb=translate');

        // Start clock
        setInterval(updateClock, CONFIG.CLOCK_INTERVAL);
    }
};
