---
title: "lgit: Local Git with SQLite Sync and Style"
date: 2025-07-05
comments: true
---

**lgit** (Local Git): A shell script that wraps common Git workflows with Nerd Font-styled output and SQLite-powered push/pull — version control that looks good and works offline.

## The Aesthetic Case for Tooling

Most Git wrappers exist to add functionality. lgit starts from a different premise: the terminal is where you spend your day, and the tools you use should look like they belong there.

lgit wraps Git commands with colorful headers, Nerd Font icons, and box-drawing characters. This is cosmetic, but cosmetics affect how you feel about using a tool, and that affects how often you use it.

```
╭─ lgit status ─────────────────────────────────╮
│  branch: main                                  │
│  ✓ clean working tree                          │
╰────────────────────────────────────────────────╯
```

```
╭─ lgit log ─────────────────────────────────────╮
│  ● a3f2c1d  add search endpoint        3h ago  │
│  ○ 7b8e9f2  initial structure          1d ago  │
╰────────────────────────────────────────────────╯
```

The substance is ordinary `git status` and `git log`. The presentation is what makes you glance at it rather than scroll past.

## SQLite as a Git Remote

The more unusual feature is SQLite sync. lgit uses `git-remote-sqlite` — a Git remote helper that lets you push and pull to a `.db` file using the `sqlite://` protocol.

This makes a local SQLite file a full Git remote. You can push your history into it, pull from it, and rebuild a `.git` directory from it. The database is a single portable file with no server, no authentication, and no network dependency.

```bash
# Initialize a repo with SQLite backing
lgit init myproject
cd myproject

# Push history into the database
lgit commit "first commit"
# → runs: git commit -m "..." && git push sqlite://~/.lgit/myproject/git.db

# On another machine, or after losing .git:
lgit rebuild
# → reconstructs .git from git.db
```

The `rebuild` command is the critical one. If your working directory's `.git` folder is gone — deleted, corrupted, moved — you can reconstruct it from the SQLite database as long as the `.db` file is intact.

## Commands

```bash
lgit init [name]         Initialize repo, add all files, push to SQLite
lgit add [file...]       Stage files
lgit commit [message]    Commit and push to SQLite
lgit status              Working tree status (styled)
lgit log                 Recent history (graph view, styled)
lgit restore [hash] [file]  Restore file from a commit (with prompt)
lgit reset [hash]        Hard reset to a commit (with confirmation)
lgit rebuild             Reconstruct .git from SQLite snapshot
```

Every destructive operation — `restore`, `reset`, `rebuild` — prompts for confirmation. lgit doesn't assume you meant to do something irreversible.

## Installation

```bash
git clone https://github.com/lucianofedericopereira/lgit
chmod +x lgit/lgit
sudo cp lgit/lgit /usr/local/bin/
```

You also need `git-remote-sqlite`:
```bash
# Install from source
git clone https://github.com/chrislloyd/git-remote-sqlite
cd git-remote-sqlite && make install
```

lgit itself has no other dependencies beyond Git and standard shell utilities.

## Nerd Fonts

The styling uses Unicode characters from the [Nerd Fonts](https://www.nerdfonts.com) extended icon set. If your terminal uses a Nerd Font, the icons render correctly. If not, they fall back to readable ASCII equivalents — lgit checks `$TERM` and `$NERD_FONTS` before choosing which characters to use.

```bash
# Automatic detection — no configuration needed
lgit status

# Force ASCII mode
NERD_FONTS=0 lgit status
```

## When lgit Fits

lgit is not a replacement for Git in team contexts. It's a personal workflow tool for:

- Personal projects that don't need a remote server
- Offline work where you want history without a network connection
- Situations where you want a portable, self-contained archive of a project's history

The SQLite file can be backed up like any file. It can be encrypted, compressed, or attached to an email. The entire history of a project — all commits, all branches — in a single portable database.

## Links

- **GitHub**: [lucianofedericopereira/lgit](https://github.com/lucianofedericopereira/lgit)
- **git-remote-sqlite**: [chrislloyd/git-remote-sqlite](https://github.com/chrislloyd/git-remote-sqlite)

## License

MIT
