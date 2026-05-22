---
title: "AutoCommit: The Green Grid as a Learning Device"
date: 2026-05-22
comments: true
---

**AutoCommit**: A GitHub Actions workflow that makes commits on a schedule — not to inflate the contribution graph, but to give you a real, running pipeline to study and dissect.

## The Confession

Everyone notices the GitHub contribution graph. The green squares reward consistency, and that reward creates a temptation: fake the consistency. Automated commits that mean nothing. Green boxes that represent no work.

AutoCommit leans into this temptation deliberately, then subverts it. Yes, it auto-commits. Yes, your grid turns green. And along the way you learn how GitHub Actions actually works — triggers, runners, secrets, environment variables, artifact management — by watching a live system do something trivial, so you can apply the same patterns to something meaningful.

Goodhart's Law says: when a measure becomes a target, it ceases to be a good measure. The green grid is the wrong target. Understanding the pipeline that produces it is the right one.

## The Pirate Connection

The project is named after Guybrush Ulysses Threepwood, the famously incompetent pirate from Monkey Island. The metaphor holds: Guybrush wants to be a pirate captain but often achieves his goals through accidents and persistence rather than skill. AutoCommit gives you the captain's hat before you've earned it — then shows you what it takes to earn it for real.

## What the Workflow Does

The GitHub Actions workflow runs on a cron schedule, makes a small, deterministic change to the repository, and commits it. No secrets. No external dependencies. Just the GitHub token that Actions provides automatically.

```yaml
name: AutoCommit
on:
  schedule:
    - cron: '0 12 * * 1-5'  # Monday–Friday at noon UTC
  workflow_dispatch:          # also triggerable manually

jobs:
  commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Make a change
        run: |
          echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> log.txt

      - name: Commit and push
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add log.txt
          git commit -m "chore: automated entry $(date -u +%Y-%m-%d)"
          git push
```

This is a complete, working pipeline. Reading it teaches you:

- **Triggers**: `schedule` (cron) and `workflow_dispatch` (manual) are two of the most common event types.
- **Runners**: `ubuntu-latest` is the default. Swap it for `macos-latest` or `windows-latest` to see the difference.
- **Tokens**: `GITHUB_TOKEN` is injected automatically — you don't create it. Understanding that distinction matters when you need actual secrets.
- **Bot identity**: commits from Actions use a special bot email so they're traceable.

## The Real Lesson

Most GitHub Actions tutorials show you `Hello, World` in isolation. AutoCommit shows you a workflow that integrates with the repository state itself — checking out, modifying, pushing back. This is the pattern used by:

- Automated changelog generators
- Dependency update bots (Dependabot, Renovate)
- Asset compilation pipelines that commit built output
- README auto-updaters that pull in external data

Once you understand the loop — trigger → run → commit → push — you can build any of these.

## Multilingual Documentation

The repository documents the project in five languages: English, Spanish, Italian, German, and French. Not for internationalization's sake, but as a reminder that the people who taught themselves to code came from everywhere, and the tools we use to teach should meet them where they are.

## Extending It

Once the basic workflow runs, the natural next experiments are:

```yaml
# Add a matrix to run on multiple OS
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
runs-on: ${{ matrix.os }}
```

```yaml
# Cache dependencies between runs
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

```yaml
# Upload an artifact
- uses: actions/upload-artifact@v4
  with:
    name: log
    path: log.txt
```

Each extension teaches something new. The commits themselves are still meaningless. The learning is not.

## Links

- **GitHub**: [lucianofedericopereira/autocommit](https://github.com/lucianofedericopereira/autocommit)

## License

MIT
