---
title: "Linknim: A Bookmark Server Written in Nim"
date: 2026-05-17
comments: true
---

**Linknim**: A self-hosted bookmark manager written in Nim that stores everything in plain CSV and INI files — compatible with the linkding API, readable without special tools.

## The Bookmark Problem

Browser bookmarks are siloed. Your Firefox bookmarks don't follow you to Chromium. Your work browser doesn't know what you saved at home. Cloud-based bookmark managers solve the sync problem but introduce a dependency on a service that can change pricing, shut down, or decide to monetize your reading habits.

Self-hosted bookmark managers exist — linkding being the most polished — but they require a Python server, a database, Docker, and ongoing maintenance. The stack is heavier than the problem warrants.

Linknim solves the same problem with a Nim binary and two file types.

## The Storage Model

Every bookmark is a row in a CSV file. Every configuration option is a key in an INI file. That's it.

```
# bookmarks.csv
id,url,title,description,tags,is_archived,created_at
1,https://example.com,Example Site,An example,web dev,0,2026-01-15
2,https://nim-lang.org,Nim Language,Systems programming language,nim programming,0,2026-01-20
```

```ini
# bookmarks.ini
[server]
host = 127.0.0.1
port = 8888
token = your-secret-token

[display]
theme = auto
page_size = 30
```

The implications of this storage model:
- **Backup**: copy two files.
- **Version control**: commit two files.
- **Read without the server**: open in a text editor or spreadsheet.
- **Migrate**: export from any CSV-capable tool.
- **Recover from a crash**: the data was never in a format that required special tools to read.

## linkding API Compatibility

Linknim implements the linkding REST API. This matters because browser extensions — the Firefox and Chrome linkding extensions — work with Linknim without modification. You configure the extension to point at `http://127.0.0.1:8888` instead of your linkding instance, and it continues to work.

```bash
# Save a bookmark via API (same as linkding)
curl -X POST http://127.0.0.1:8888/api/bookmarks/ \
  -H "Authorization: Token your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "title": "Example", "tag_names": ["web"]}'
```

The API compatibility means you don't need to change your workflow. If you're already using linkding, migration is: export from linkding, import into Linknim, point extensions at the new server.

## Features

- **Web UI** with search, tag tree, bundle saved searches, and bulk actions
- **TUI** for a full terminal interface without a browser
- **CLI** for scripting: `linknim add`, `linknim list`, `linknim export --format json`
- **RSS feed** at `/feed.xml` for shared bookmarks
- **Bookmarklet** for saving pages without a browser extension
- **Favicon fetching** — cached locally in `data/favicons/`
- **Import** Netscape bookmark HTML (the format every browser exports)
- **Dark/light/auto theme** set in INI or toggled per session

## Quick Start

```bash
git clone https://github.com/lucianofedericopereira/linknim
cd linknim
nimble install illwill
nim c -d:release linknim.nim

# Initialize config with a random token
./linknim init

# Start the server
./linknim serve
# → http://127.0.0.1:8888
```

Or use the TUI without running a server:

```bash
./linknim tui
```

## The Nim Choice

Nim compiles to C and produces a single statically-linked binary. The deployment story is: compile once, copy the binary. No runtime, no interpreter, no package manager.

For a tool you run on a personal server or a Raspberry Pi, this matters. The binary starts in milliseconds. It uses minimal memory. You don't need to maintain a Python virtualenv or track security updates to a web framework.

The implementation uses `illwill` for the TUI — a Nim library for full-screen terminal UIs — and Nim's standard HTTP library for the server. Everything else is the language itself.

## Links

- **GitHub**: [lucianofedericopereira/linknim](https://github.com/lucianofedericopereira/linknim)

## License

LGPL-2.1
