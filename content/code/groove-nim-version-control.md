---
title: "Groove: Save States for Solo Development"
date: 2026-05-03
comments: true
---

**Groove** (GROOVE Retains Older Object Versions Effortlessly): A Nim tool for solo developers who need frequent checkpoints and clean releases — the layer before git, not a replacement for it.

## The Solo Developer's VCS Problem

Traditional version control was designed for teams. Meaningful commits, descriptive messages, linear history that others can read. This works well when other people read your commits. When you're the only one working on something, the overhead becomes friction.

Solo development tends toward endless WIP cycles. You make twenty small edits before anything is worth committing. You commit anyway — "wip", "more wip", "fix that thing" — and your history becomes noise. Then you need to release something and spend twenty minutes squashing and rebasing to produce a clean history nobody asked for.

Groove separates two concerns that git conflates:

- **wips** — anonymous save states, cheap to create, for undo
- **releases** — named versions, permanent, consolidated from wips

Between releases you wip freely. On release, all wips collapse into the version. History stays clean without squashing.

## Installation

```bash
nimble build
cp groove /usr/local/bin/
```

Requires Nim 2.0+. No other dependencies.

## Daily Commands

```bash
groove wip              # save current state (undo point)
groove undo             # restore previous wip
groove redo             # step forward through wip history

groove release v0.1     # consolidate wips → named release
groove ls               # list wips and releases
groove show v0.1        # inspect a release

groove diff             # changes since last wip
groove diff v0.1        # changes since a release
```

This is the entire interface. There is no branching, no merging, no remote. Groove is not trying to be git.

## When to Use Groove

Groove is useful for the period when a project is actively being drafted — the phase before it deserves a public repository. You're exploring a design. You're writing a library but haven't decided on the API. You're building something for yourself.

During this phase, git's overhead is real. Naming every save. Deciding what to stage. Maintaining a coherent commit history for an audience of one. Groove removes that overhead.

When the project is real — when others will contribute, when you need blame or bisect, when a CI pipeline needs to run — push to git. Groove can export to a git repository at any point:

```bash
groove export --git ./myproject.git
```

The releases become git tags. The wip history is collapsed (it was never meant to be permanent).

## The Release Model

A release in Groove is an immutable named snapshot:

```bash
groove release v0.2 --message "Search endpoint complete"
```

All wips since the previous release are consolidated. The wip chain is cleared. You start fresh for the next release.

```
wip → wip → wip → wip → release v0.1
wip → wip → release v0.2
wip → wip → wip → release v0.3 ← you are here
```

This matches how solo work actually happens: sprints of exploration, then a stable point. The release is the unit of history worth keeping.

## Why Nim

Groove is written in Nim because the storage model — versioned file trees — maps naturally to Nim's system programming capabilities. The tool needs to hash files, detect changes, serialize state, and do all of it quickly.

Nim compiles to C, produces small binaries, and has no runtime to install. `groove` is a single executable. You compile it once, copy it anywhere.

The storage format is plain directories — no binary database format to corrupt, no external tool to inspect it. Each wip is a directory named by timestamp hash. Each release is a tagged symlink. You can examine the store with `ls` and recover data with `cp` if anything goes wrong.

## What Groove Is Not

It's worth being explicit:

- Not a git replacement. When you need branches, blame, CI, or collaboration — use git.
- Not a backup tool. For retention policies and offsite backup, use restic or borg.
- Not a filesystem snapshot tool. For that, btrfs and zfs exist.

Groove is the layer before git. It keeps you from losing work while you figure out what you're building.

## Links

- **GitHub**: [lucianofedericopereira/groove](https://github.com/lucianofedericopereira/groove)

## License

MIT
