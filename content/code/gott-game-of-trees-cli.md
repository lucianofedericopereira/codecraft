---
title: "gott: A Friendlier CLI for Game of Trees"
date: 2026-03-17
comments: true
---

**gott**: A Perl wrapper around Game of Trees (`got`) that collapses multi-step workflows into single commands — so version control gets out of your way and lets you work.

## Why Game of Trees

Game of Trees is a version control system from the OpenBSD team. It reads and writes git-compatible repositories, speaks the git wire protocol, and can push to GitHub or any git host. Your collaborators never need to install it.

What it offers in exchange is deliberate simplicity:

- The repository and work tree are physically separate. Your `.git`-equivalent lives in `myproject.git/`; your editable files live in `myproject/`. No hidden directory mixed into your source.
- Commands are named after what they do. `got add`, `got commit`, `got revert`. No porcelain/plumbing split. No `git checkout` doing three different things depending on flags.
- The codebase is small and auditable. It's an OpenBSD project — the code quality expectation is high.

For a solo developer or a small team, this simplicity is valuable. The tooling disappears; the work remains.

## What gott Adds

`got` is deliberate, which sometimes means verbose. A new project requires: `got init`, adding a seed commit, `got checkout`. A daily snapshot requires: `got add -R .` then `got commit -m "..."`. gott handles the sequences:

| Task | With got | With gott |
|------|----------|-----------|
| Start a project | 4 commands | `gott new myproject` |
| Commit everything | `got add -R . && got commit -m "..."` | `gott snap "message"` |
| New branch + switch | `got branch -c x && got update -b x` | `gott nb x` |
| Stash work in progress | multiple steps | `gott stash` |
| Merge topic branch | `got integrate` + cleanup | `gott land x` |

gott doesn't hide what got does — it shortens what you type for things you do every day.

## Installation

```bash
git clone https://github.com/lucianofedericopereira/gott
sudo cp gott/gott /usr/local/bin/
chmod +x /usr/local/bin/gott
```

Requires Perl 5 (pre-installed on any BSD or Linux system) and a working `got` installation.

On Linux:
```bash
# Debian/Ubuntu
sudo apt install game-of-trees

# From source
git clone https://github.com/nicowillis/got
```

On OpenBSD:
```
pkg_add got
```

## Daily Workflow

```bash
# Start a new project
gott new myproject
cd myproject

# Work, then snapshot
gott snap "initial structure"

# Branch for a feature
gott nb feature/search
# ... work ...
gott snap "add search endpoint"

# Merge back to main
gott land feature/search

# Push to git remote
got send
```

The push step uses `got send` — gott doesn't wrap this because it maps to exactly one command. Wrapping it would add noise, not clarity.

## The Stash Command

`got` doesn't have a stash command. That's deliberate — the got developers consider stash to be a workaround for unclear branching, and they're not entirely wrong. But the use case is real: you're mid-edit when something urgent comes up.

gott implements stash as a branch:

```perl
sub cmd_stash {
    my ($self, @args) = @_;
    my $branch = "stash/" . time();
    $self->run_got("branch", "-c", $branch);
    $self->run_got("add", "-R", ".");
    $self->run_got("commit", "-m", "WIP stash");
    $self->run_got("update", "-b", "main");
    print "Stashed to $branch\n";
}

sub cmd_unstash {
    my ($self, @args) = @_;
    my $branch = $args[0] // $self->latest_stash();
    $self->run_got("update", "-b", $branch);
    print "Restored $branch\n";
}
```

The stash is visible in `got log`. It's not hidden state that can be lost — it's a real branch with a real commit. This trades some magic for auditability.

## Why Perl

Same reason as sqltool, jinja2tt2, and other tools in this collection: Perl is pre-installed on every BSD and Linux system. A Perl script dropped into `/usr/local/bin/` runs everywhere with no setup. For a tool you use ten times a day, that reliability matters.

The implementation is a thin object that wraps `got` commands. Perl's `system()` and backtick operator handle subprocess calls cleanly. No framework, no dependencies, no build step.

## Links

- **GitHub**: [lucianofedericopereira/gott](https://github.com/lucianofedericopereira/gott)
- **Game of Trees**: [gameoftrees.org](https://gameoftrees.org)

## License

LGPL-2.1
