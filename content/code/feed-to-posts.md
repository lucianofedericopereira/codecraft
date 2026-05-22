---
title: "Feed to Posts: Keeping Your GitHub Profile Current"
date: 2025-12-27
comments: true
---

**Feed to Posts**: A lightweight Python script that reads an RSS or Atom feed and updates a GitHub README automatically — so your latest articles appear on your profile without any manual effort.

## The GitHub Profile README Problem

A GitHub profile README is a great idea until it goes stale. You write one when you're excited about it, fill it with links and stats, and then promptly forget to update it when you publish something new. Six months later, the "latest posts" section still shows articles from last year.

The fix is automation. If your blog publishes an RSS or Atom feed — and any blog worth its salt does — you can parse it and update the README on a schedule.

## How It Works

The script fetches a feed URL, extracts the most recent entries, and rewrites a marked section of your README with formatted links. The rest of the README is untouched.

```python
import feedparser
import re
from pathlib import Path

FEED_URL = "https://lucianofedericopereira.github.io/codecraft/feed.xml"
README_PATH = Path("README.md")
MAX_POSTS = 5

MARKER_START = "<!-- BLOG-POST-LIST:START -->"
MARKER_END   = "<!-- BLOG-POST-LIST:END -->"

def fetch_posts(url: str, limit: int) -> list[dict]:
    feed = feedparser.parse(url)
    return [
        {
            "title": entry.title,
            "link":  entry.link,
            "date":  entry.published[:10] if hasattr(entry, 'published') else "",
        }
        for entry in feed.entries[:limit]
    ]

def render_posts(posts: list[dict]) -> str:
    lines = []
    for post in posts:
        lines.append(f"- [{post['title']}]({post['link']}) — {post['date']}")
    return "\n".join(lines)

def update_readme(readme: Path, content: str) -> None:
    text = readme.read_text()
    pattern = rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}"
    replacement = f"{MARKER_START}\n{content}\n{MARKER_END}"
    updated = re.sub(pattern, replacement, text, flags=re.DOTALL)
    readme.write_text(updated)

if __name__ == "__main__":
    posts = fetch_posts(FEED_URL, MAX_POSTS)
    content = render_posts(posts)
    update_readme(README_PATH, content)
    print(f"Updated README with {len(posts)} posts")
```

The marker comments in your README delimit the section that gets replaced. Everything outside those markers stays exactly as you wrote it.

```markdown
## Latest Articles

<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->
```

## Running It on a Schedule

The script runs locally or in a GitHub Actions workflow:

```yaml
name: Update README with latest posts

on:
  schedule:
    - cron: '0 6 * * *'   # daily at 6 AM UTC
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install feedparser

      - run: python feed_to_posts.py

      - name: Commit if changed
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git diff --quiet || (git add README.md && git commit -m "docs: update latest posts")
          git push
```

The `git diff --quiet || ...` pattern is the correct idiom here — only commit if the README actually changed. If there are no new posts since the last run, nothing is committed, and your history stays clean.

## Feed Format Handling

`feedparser` handles both RSS 2.0 and Atom transparently. You don't need to know which format your blog uses:

```python
feed = feedparser.parse(url)

# Works for both RSS and Atom
for entry in feed.entries:
    print(entry.title)   # RSS: <title>, Atom: <title>
    print(entry.link)    # RSS: <link>,  Atom: <link href="...">
    print(entry.summary) # RSS: <description>, Atom: <summary>
```

The normalization is feedparser's great contribution — it smooths over the formatting variations so you write one code path for both formats.

## Multiple Feeds

If you contribute to more than one blog or publication, the script handles multiple sources:

```python
FEEDS = [
    {"url": "https://myblog.com/feed.xml", "label": "Blog"},
    {"url": "https://dev.to/feed/username", "label": "Dev.to"},
]

all_posts = []
for feed_config in FEEDS:
    posts = fetch_posts(feed_config["url"], limit=3)
    for post in posts:
        post["source"] = feed_config["label"]
    all_posts.extend(posts)

all_posts.sort(key=lambda p: p["date"], reverse=True)
```

## Links

- **GitHub**: [lucianofedericopereira/feed-to-posts](https://github.com/lucianofedericopereira/feed-to-posts)

## License

MIT
