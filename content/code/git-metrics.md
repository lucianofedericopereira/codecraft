---
title: "Git Metrics: GitHub Stats as SVG Images"
date: 2025-12-28
comments: true
---

**Git Metrics**: A Python script that queries the GitHub API, calculates contribution statistics, and renders them as SVG or PNG images — embeddable in any README without relying on third-party services.

## The Third-Party Problem

The popular GitHub stats cards — github-readme-stats and its variants — are excellent projects, but they depend on servers you don't control. When those servers go down, rate-limit, or deprecate an endpoint, your profile shows broken images. You can't fix it. You can only wait.

Git Metrics runs on your own infrastructure, generates the images locally, and commits them to your repository. Once generated, the images are static files. They don't depend on any external service at runtime.

## What Gets Measured

The script calculates a curated set of metrics from the GitHub API:

```python
from github import Github
from datetime import datetime, timedelta

def collect_metrics(username: str, token: str) -> dict:
    g = Github(token)
    user = g.get_user(username)

    repos = list(user.get_repos(type='owner'))

    total_stars  = sum(r.stargazers_count for r in repos)
    total_forks  = sum(r.forks_count for r in repos)
    languages    = {}

    for repo in repos:
        if repo.language:
            languages[repo.language] = languages.get(repo.language, 0) + 1

    # Contributions in the last year
    since = datetime.utcnow() - timedelta(days=365)
    commits = sum(
        repo.get_commits(author=username, since=since).totalCount
        for repo in repos
        if not repo.fork
    )

    return {
        "username":    username,
        "stars":       total_stars,
        "forks":       total_forks,
        "repos":       len(repos),
        "commits_1y":  commits,
        "top_langs":   sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5],
    }
```

The output is a Python dictionary — language-agnostic data that can feed any renderer.

## SVG Rendering

SVG is the right format for stats cards. It scales without pixelation, supports text natively, and can be styled with CSS. The renderer builds the SVG as a string template:

```python
def render_svg(metrics: dict, theme: str = "dark") -> str:
    colors = THEMES[theme]
    langs_html = "\n".join(
        f'<text x="20" y="{100 + i * 20}" fill="{colors["text"]}" font-size="12">'
        f'{lang}: {count} repos</text>'
        for i, (lang, count) in enumerate(metrics["top_langs"])
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
  <rect width="400" height="200" rx="10" fill="{colors['bg']}"/>
  <text x="20" y="30" fill="{colors['title']}" font-size="16" font-weight="bold">
    {metrics['username']}
  </text>
  <text x="20" y="55" fill="{colors['text']}" font-size="12">
    ★ {metrics['stars']} stars · {metrics['forks']} forks · {metrics['repos']} repos
  </text>
  <text x="20" y="75" fill="{colors['text']}" font-size="12">
    {metrics['commits_1y']} commits in the last year
  </text>
  {langs_html}
</svg>"""
```

For PNG output, the SVG is passed through `cairosvg`:

```python
import cairosvg

def render_png(svg_string: str, output_path: str) -> None:
    cairosvg.svg2png(bytestring=svg_string.encode(), write_to=output_path)
```

## Themes

The script ships with several color themes, each defined as a simple dictionary:

```python
THEMES = {
    "dark": {
        "bg":    "#0d1117",
        "text":  "#c9d1d9",
        "title": "#58a6ff",
    },
    "light": {
        "bg":    "#ffffff",
        "text":  "#24292f",
        "title": "#0550ae",
    },
    "gruvbox": {
        "bg":    "#282828",
        "text":  "#ebdbb2",
        "title": "#fabd2f",
    },
}
```

Adding a theme is four lines. No framework required.

## Automation

Run it on a schedule to keep the stats current:

```yaml
- name: Update metrics
  run: python git_metrics.py --username lucianofedericopereira --output stats/

- name: Commit images
  run: |
    git add stats/
    git diff --cached --quiet || git commit -m "chore: update GitHub stats"
    git push
```

Then embed in your README:

```markdown
![GitHub Stats](stats/overview.svg)
![Top Languages](stats/languages.svg)
```

The images are committed files. They load instantly, work offline, and never break due to a third-party outage.

## Links

- **GitHub**: [lucianofedericopereira/git-metrics](https://github.com/lucianofedericopereira/git-metrics)

## License

MIT
