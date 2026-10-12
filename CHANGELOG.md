# Changelog

Every release, as it ships.

## v1.2 — 2026-10-12

- Added `sitemap.xml`, listing every page and post with the post date as `lastmod`
- Added `llms.txt`, an index of every entry with its description, and `llms-full.txt`, the full text of every entry in one file
- Added each entry as raw Markdown beside its page, so `code/my-post/` is also served as `code/my-post.md`, linked from the page as a `text/markdown` alternate
- Added a `description` frontmatter field; without one, the post's first paragraph is used, cut at a word boundary within 160 characters
- Added Open Graph article tags to posts — `og:type article`, `article:published_time`, `article:author`, `article:section` — and `twitter:description` everywhere
- Added schema.org JSON-LD generated as JSON: `BlogPosting` on posts, `WebSite` on the home page, `WebPage` on section pages, with an absolute logo URL
- Added `<description>` and `<guid>` to RSS items
- Added HTML minification with minify-html, on by default and turned off with `minify: false` in `themes/config.yaml`
- Added warnings from `publish.py` on stderr when a post or the config cannot be read, where it used to skip them silently
- Changed `codecraft.py` from a second copy of the builder into a terminal layer over `publish.py`, so a local build is byte-identical to what CI deploys
- Changed `codecraft.py serve` to point `<base>` at the local server and read the site URL from the config instead of a hard-coded domain
- Changed `codecraft.py watch` to rebuild when `publish.py` changes too
- Changed the meta description, `og:description` and JSON-LD description to the post's description instead of a copy of the title
- Changed page titles to keep their capitalization, so `GitHub` and `SVG` are no longer lowercased
- Changed the feed's alternate link to `application/rss+xml`, titled from the config
- Changed Mermaid to initialize with `startOnLoad: false`, as rendering is explicit, and to log render errors
- Fixed the canonical URL, `og:url` and JSON-LD `url` missing the slash between the site folder and the page path (`…/codecraftcode/post/`), which pointed every post at a 404
- Fixed a `mermaid` code block shown as an example inside a `~~~` fence rendering as the text `MERMAID_PLACEHOLDER_0`
- Fixed Mermaid diagrams containing `<` or `&`: the source is now HTML-escaped
- Updated Markdown 3.10.2 → 3.11, which requires Python 3.11 or later
- Updated python-frontmatter 1.1.0 → 1.3.0, MarkupSafe 3.0.3 → 3.0.4, Pygments 2.19.2 → 2.21.0 and tqdm 4.67.3 → 4.70.1
- Updated Mermaid 11.4.1 → 12.1.0, which lays diagrams out with ELK by default and requires Safari 17.4 or later
- Updated actions/checkout v6 → v7, actions/setup-python v6 → v7, actions/upload-pages-artifact v4 → v5 and actions/deploy-pages v4 → v5
- Updated Dependabot to group `tqdm` and `minify-html` with the other Python dependencies

## v1.1 — 2026-07-05

- Added example 3, a Perlin noise demonstration (`examples/3.html`)
- Added a tiled noise texture behind the main content area (`codeCraft.webp`)
- Changed `publish.py` and `codecraft.py` internally with no change in output: the unused `PostData` dataclass, `render_template_safe` helper and unused imports are gone, the date filters share one month-name helper, include directives are extracted from a table, and bare `except:` is now `except Exception:`
- Fixed RSS item links missing the slash between the site folder and the post path
- Updated Markdown 3.10 → 3.10.2 and tqdm 4.67.1 → 4.67.3

## v1.0 — 2025-12-27

- Added `publish.py`, the site builder GitHub Actions runs to build and deploy to GitHub Pages
- Added the `codecraft.py` command line: `build`, `serve` with URL rewriting for local preview, `watch` to rebuild on change through pyinotify, `clean`, and `new` to scaffold a post
- Added Markdown posts with YAML frontmatter, organized in `design`, `code` and `projects` sections, with section pages in `themes/sections/`
- Added per-path feature defaults through `rules` in `themes/config.yaml`
- Added Pygments syntax highlighting, a table of contents, Mermaid diagrams, CodePen embeds and Utterances comments, each switched on per post
- Added the interactive example viewer, embedded with `[example:N]` (`examples/1.html`, `examples/2.html`)
- Added the RSS feed (`feed.xml`) and the Lunr.js search index (`search.json`)
- Added archive and category listings, placed with `{% include %}` in section pages
- Added fonts configured in YAML and generated into the CSS template
- Added dates formatted in English, Spanish and Italian
- Added Dependabot for Python dependencies and GitHub Actions
