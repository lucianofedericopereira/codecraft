# Changelog

Every release, as it ships.

## v1.3 - Unreleased

- Changed search to look through the full text of every post, where it used to see only the first 200 characters
- Changed search to load its index the first time the search box is used, instead of on every page view
- Changed search to list title matches first, each with an excerpt around the match and the match highlighted
- Added arrow keys and Enter to move through and open search results
- Changed the search shortcut from Ctrl/Cmd+K, which browsers keep for their own search, to `s`, or Alt+S from inside another text field
- Fixed the search shortcut on narrow screens focusing a search box hidden inside the closed menu
- Added an outline to the search box on hover and while it has focus, drawn inside its edge so nothing moves
- Fixed Back to the first page of a visit leaving the next page's content on screen
- Fixed the language menu, and the menu on narrow screens, staying open after a language is picked
- Fixed a jsDelivr outage stopping every script on the site, where only diagrams depend on it now
- Fixed `search.json` escaping quotes by hand: it is written with Jinja's `tojson`, so a backslash or control character in a post can no longer break the index
- Removed Lunr.js, `search_file` and `scripts.lunr` from the config, and the `search` meta tag
- Removed the jsDelivr preconnect from pages without a Mermaid diagram
- Removed the unused `search_enabled` setting, and a search observer that never fired
- Added tags: a `tags:` list of names in `themes/config.yaml` (or a mapping, for a description per tag) and `tags: linux, bash` in a post's frontmatter (a YAML list works too), matched in any case, with a build warning naming the file for a tag the config doesn't declare
- Added tag chips under each post, linking to the tag's page once it has one
- Added a page, a Markdown version and an RSS feed for every tag used by at least `tag_min_posts` posts (3 by default), and `tags/` listing every tag in use with its count
- Added tag pages to `sitemap.xml`, `sitemap/`, `sitemap.md` and `llms.txt`
- Added each post's tags as `article:tag` meta tags, JSON-LD `keywords`, RSS `<category>` elements and a `tags` field in `search.json`
- Added an optional `themes/sections/tags/<tag>.md` to give a tag's page its own title and introduction, with `{% include tag.html %}` placing the list, as section pages do
- Added related posts at the end of each tagged post, built without JavaScript: most shared tags first, then the newest from the post's section, set with `related` (`min`, `max`, `fallback`) in `themes/config.yaml`
- Fixed posts with the same date coming out in a different order on different machines; they now follow their file names
- Fixed a post without a `date` crashing the whole build: it now takes the date of the file's last commit, or its modification time if uncommitted, with a warning naming the file
- Changed the deploy workflow to check out the full history, so the commit date of every file is available to the build
- Changed the paper texture behind the content from a tiled image to fibre and grain layers drawn in the browser from a seed, set with `texture` in `themes/config.yaml` (seed, colours, fibre count, opacities); leave it out for a plain background
- Removed `codeCraft.webp` and the `multiply` blend on the content area that it needed

## v1.2 — 2026-10-12

- Added `sitemap.xml`, listing every post with its date as `lastmod` and every page with the date of the newest post it lists; a section page with no posts is left out
- Added a human-readable sitemap in the site's own theme at `sitemap/`, and as `sitemap.md`; neither is linked from the pages, `sitemap.xml` lists both and `llms.txt` links the Markdown one
- Added `llms.txt`, an index of every entry with its description, and `llms-full.txt`, the full text of every entry in one file
- Added each entry as raw Markdown beside its page, so `code/my-post/` is also served as `code/my-post.md`, linked from the page as a `text/markdown` alternate
- Added Markdown versions of the home, archive and section pages (`index.md`, `archive.md`, `code.md`, …), rendered through `posts.md`, `category.md` and `archive.md` templates and listed in `llms.txt`
- Added a `description` frontmatter field; without one, the post's first paragraph is used, cut at a word boundary within 160 characters
- Added an `updated` frontmatter field, used as the sitemap `lastmod`, JSON-LD `dateModified` and `article:modified_time`
- Added Open Graph article tags to posts — `og:type article`, `article:published_time`, `article:section`
- Added schema.org JSON-LD generated as JSON: `BlogPosting` on posts, `WebSite` on the home page, `WebPage` on section pages, with an absolute logo URL
- Added `<description>` and `<guid>` to RSS items
- Added HTML minification with minify-html, on by default and turned off with `minify: false` in `themes/config.yaml`
- Added warnings from `publish.py` on stderr when a post or the config cannot be read, where it used to skip them silently
- Added a workflow that keeps the README's badges, project tree and release numbers current with sigilbadges, treegen2 and sigilmd, committing only when something changed
- Changed the README into a plain guide to the engine, and corrected what it claimed: the license is MIT, `watch` does not reload the browser, and Python 3.11 is the minimum
- Changed tables to the body font, a sans-serif, instead of the title font
- Changed `codecraft.py` from a second copy of the builder into a terminal layer over `publish.py`, so a local build is byte-identical to what CI deploys
- Changed `codecraft.py serve` to point `<base>` at the local server and read the site URL from the config instead of a hard-coded domain
- Changed `codecraft.py watch` to rebuild when `publish.py` changes too
- Changed the meta description, `og:description` and JSON-LD description to the post's description instead of a copy of the title
- Changed page titles to keep their capitalization, so `GitHub` and `SVG` are no longer lowercased
- Changed the feed's alternate link to `application/rss+xml`, titled from the config
- Changed section pages to build in filename order, so every machine produces the same output
- Removed head tags that were wrong or had no effect: `X-UA-Compatible`, the non-standard `copyright` and `repository`, `robots: index, follow` (the default), `og:locale` in a format Open Graph does not accept, `article:author` holding a name where a profile URL is expected, the `twitter:title` and `twitter:description` copies of their Open Graph tags, and a preconnect to the site's own origin
- Changed Mermaid to initialize with `startOnLoad: false`, as rendering is explicit, and to log render errors
- Fixed the archive's Code and Design filters hiding the 2026 heading: the filter only knew 2021 to 2025, so every new year lost its heading
- Changed the archive into one group per year, so a year with nothing in the chosen section hides itself, heading and all
- Changed the archive filter buttons, the filter rules in the stylesheet and `codecraft.py new` to read `sections` from the config; adding a section is one line in the config and a folder of posts
- Added a generated page for every section without a file in `themes/sections/`, and stopped building section pages that have no posts
- Changed `rules` to match paths from the repository root (`content`, `themes/sections`) instead of anywhere in the file path, and merged the three identical per-section rules into one `content` rule
- Fixed browsers pairing new pages with a cached old stylesheet or script after a deploy: `codeCraft.css` and `codeCraft.js` are linked with a version taken from their content, so a changed file gets a new URL
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
