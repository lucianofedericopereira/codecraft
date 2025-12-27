---
title: "Bash: Automating Self-Hosting Git Repository Backups"
date: 2025-11-10
comments: true
---

Backing up your Git repositories is essential—not just for preserving your work, but for ensuring resilience in the face of hardware failures, accidental deletions, or other unexpected issues. Whether you're managing personal projects or hosting code for a team, having a reliable backup strategy is non-negotiable.

If you're self-hosting Git using a platform like Gitea, this article introduces a robust and elegant Bash script that automates the entire backup process. It covers everything from creating shallow clones and generating Git bundles to syncing with an external disk for added redundancy.

But this isn't just about backups—it's also a great opportunity to sharpen your Bash scripting skills. The script showcases a variety of useful techniques, including:

- Conditional logic and error handling
- Directory and file management
- Git operations via CLI
- Visual logging with ANSI colors and Nerd Font icons
- Background processes and spinner animations

Whether you're a seasoned shell user or just getting started, you'll find plenty of clever tricks and reusable patterns that can elevate your scripting game.

Let’s dive in and explore how this script works—and how you can adapt it to your own Git workflow.

## Prerequisites

Before running the script, ensure you have Gitea running in a container. 

Here's a quick setup using Podman:

```bash
podman run -d --name gitea -p 3000:3000 -p 2222:22 -v /srv/gitea:/data docker.io/gitea/gitea:latest
```

Your repositories will be located under `/srv/gitea/git/repositories/$USER`, and the web interface at `http://localhost:3000`.
For the sake of simplicity i matched the user and repo name.

## Script Overview

This script performs the following tasks:

- Creates shallow clones of each Git repository
- Generates Git bundles for the latest commits
- Syncs backups to an external disk (if mounted)
- Maintains a log file and cleans up old bundles

### Configuration Variables

- `BACKUP_DISK`: Path to your external backup disk
- `GIT_COMMITS`: Number of recent commits to include in the bundle
- `MAX_BACKUPS`: Maximum number of bundles to keep per repo

### Directory Setup

```bash
GIT_SOURCES="/srv/gitea/git/repositories/$USER"
GIT_BACKUPS="/home/$USER/Backups"
GIT_LOGFILE="$GIT_BACKUPS/git_job.log"
GIT_SHALLOW="$GIT_BACKUPS/git_shallow"
GIT_BUNDLES="$GIT_BACKUPS/git_bundles"
```

These paths define where the script looks for repositories and stores backups.

## Key Functions Explained

- `ensure_dirs`: Creates necessary directories and checks if the external disk is mounted.
- `create_shallow_clone`: Performs a shallow clone of the repository using `--depth $GIT_COMMITS`.
- `create_bundle`: Generates a Git bundle containing the last N commits. If the commit range is empty, it skips bundle creation.
- `sync_to_external`: Uses `rsync` to copy the shallow clone and bundle to the external disk.
- `cleanup_old_bundles`: Deletes older bundles beyond the `MAX_BACKUPS` threshold.

## Visual Logging with Nerd Fonts

The script includes visual enhancements using ANSI colors and Nerd Fonts for icons. This improves readability and adds a stylish touch to terminal output.

Example log output:
```
2025-11-10 19:00:00 - External disk detected at /mnt/external_disk/GIT_BACKUP
2025-11-10 19:00:01 - Processing my-repo...
2025-11-10 19:00:05 - Processing my-repo done
```

## Execution Flow

The main loop scans all `.git` directories, validates them, and processes each repository:

```bash
find "$GIT_SOURCES" -type d -name "*.git" | while read -r repo_path; do
  # Validate repo
  # Create shallow clone
  # Create bundle
  # Sync to external disk
  # Cleanup old bundles
done
```

## The Code

```bash
#!/bin/bash

# ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
# │ INSTALL: >_ podman run -d --name gitea -p 3000:3000 -p 2222:22 -v /srv/gitea:/data docker.io/gitea/gitea:latest │
# └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

BACKUP_DISK="/mnt/external_disk/GIT_BACKUP"
GIT_COMMITS=5
MAX_BACKUPS=3

GIT_SOURCES="/srv/gitea/git/repositories/$USER"
GIT_BACKUPS="/home/$USER/Backups"
GIT_LOGFILE="$GIT_BACKUPS/git_job.log"
GIT_SHALLOW="$GIT_BACKUPS/git_shallow"
GIT_BUNDLES="$GIT_BACKUPS/git_bundles"

declare -A MSG=(  
  [git_bundle_create]='Creating bundle...'
  [git_done]="Processing %s done"
  [git_done_all]="All repositories backed up."
  [git_ext_detect]='External disk detected at'
  [git_ext_missing]='External disk not available. Skipping external sync.'
  [git_ext_sync]='Syncing to external disk...'
  [git_process]="Processing %s..."
  [git_shallow]="Creating shallow clone..."
  [git_start]='Starting Git backup...'
  [git_skip_bundle]='Skipping bundle — no commit range in'
  [git_skip_ext]='Skipped external sync for %s — disk not mounted.'
  [git_skip_invalid]='Skipping invalid repo:'
)
declare -A COLORS=(
  [orange]='204;125;75'
    [dark]='190;170;130'
   [beige]='234;219;178'
   [green]='144;185;144'
    [blue]='102;153;204'
)
declare -A ICON=(
  # Actions & States
    [cog]=""
    [done]=""
    [ok]=""
    [warn]=""
    [error]=""
    [info]=""
    [question]=""
    [plus]=""
    [minus]=""
    [check]=""
    [cross]=""
  # Files & Folders
    [box]=""
    [zip]=""
    [cube]=""
    [file]=""
    [folder]=""
    [folder_open]=""
    [symlink]=""
  # VCS / Git
    [git]=""
    [branch]=""
    [commit]="ﰖ"
    [merge]=""
    [pull]=""
    [push]=""
  # UI / Navigation
    [arrow_left]=""
    [arrow_right]=""
    [arrow_up]=""
    [arrow_down]=""
    [home]=""
    [search]=""
    [settings]=""
    [lock]=""
    [unlock]=""
  # Misc
    [star]=""
    [heart]=""
    [calendar]=""
    [clock]=""
    [bolt]=""
    [fire]=""
)

declare -A ESC=(
  [cursorshow]="\e[?25h"
  [cursorhide]="\e[?25l"
   [cleanline]='\r\033[K'
          [nc]='\033[0m'
)
for color in "${!COLORS[@]}"; do
  ESC[$color]="\e[38;2;${COLORS[$color]}m"
done

# ┌────────────────────────────────────────────┐
# │ UTILITIES: Visuals                         │
# └────────────────────────────────────────────┘

cursor_hide() {
  echo -ne "${ESC[cursorhide]}"
}
cursor_show() {
  echo -ne "${ESC[cursorshow]}"
}
strip_ansi() {
  echo -e "$1" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g'
}
log_line() {
  local line="${ESC[beige]}$(date '+%Y-%m-%d %H:%M:%S')${ESC[dark]} - $1${ESC[nc]}"
  echo -e "${ESC[cleanline]}${ESC[blue]} ${ICON[info]}  $(printf "%-$(tput cols)s" "$line")"
  echo "$(strip_ansi "$line")" >> "$GIT_LOGFILE"
}
log_spin() {
  local message="$1"
  local spinner_icons=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local i=0
  SPINNER_MESSAGE="$message"
  (
    while true; do
      local icon="${spinner_icons[i]}"
      local line="${ESC[orange]} ${icon}${ESC[beige]} $(date '+%Y-%m-%d %H:%M:%S') - ${SPINNER_MESSAGE}${ESC[nc]}"
      echo -ne "${ESC[cleanline]}$(printf "%-$(tput cols)s" "$line")"
      i=$(( (i + 1) % ${#spinner_icons[@]} ))
      sleep 0.1
    done
  ) &
  SPINNER_PID=$!
}
log_tick() {
  local message="$1"
  kill "$SPINNER_PID" &> /dev/null
  wait "$SPINNER_PID" 2>/dev/null
  local line="$(date '+%Y-%m-%d %H:%M:%S')${ESC[dark]} - ${message}${ESC[nc]}"
  echo -e "${ESC[cleanline]}$(printf "%-$(tput cols)s" "${ESC[green]} ${ICON[done]} ${ESC[beige]} $line")"
  echo "$(strip_ansi "$line")" >> "$GIT_LOGFILE"
}

# ┌────────────────────────────────────────────┐
# │ UTILITIES: Backuo                          │
# └────────────────────────────────────────────┘

ensure_dirs() {
    mkdir -p "$GIT_SHALLOW" "$GIT_BUNDLES"
    if mountpoint -q "$BACKUP_DISK"; then
        mkdir -p "$BACKUP_DISK/bundles"
        EXTERNAL_AVAILABLE=true
        log_line "${MSG[git_ext_detect]} $BACKUP_DISK"
    else
        EXTERNAL_AVAILABLE=false
        log_line "${MSG[git_ext_missing]}"
    fi
}
create_shallow_clone() {
    local repo_path="$1"
    local shallow_path="$2"
    rm -rf "$shallow_path"
    git config --global --add safe.directory "$repo_path"
    git clone --depth "$GIT_COMMITS" "file://$repo_path" "$shallow_path" &> /dev/null
}
create_bundle() {
    local shallow_path="$1"
    local bundle_path="$2"
    cd "$shallow_path" || return
    local latest_commit=$(git rev-parse HEAD)
    local base_commit=$(git rev-list HEAD | tail -n "$GIT_COMMITS" | head -n 1)
    if [ "$base_commit" = "$latest_commit" ]; then
        log_line "${MSG[git_skip_bundle]} ${ESC[orange]}$(basename "$shallow_path")"
        return
    fi
    git bundle create "$bundle_path" "$base_commit..$latest_commit" &> /dev/null
}
sync_to_external() {
    local shallow_path="$1"
    local bundle_path="$2"
    local repo_name="$3"
    if [ "$EXTERNAL_AVAILABLE" = true ]; then
        rsync -a --delete --checksum "$shallow_path/" "$BACKUP_DISK/$repo_name/"
        rsync -a --checksum "$bundle_path" "$BACKUP_DISK/bundles/"
    else
        log_line "$(printf "${MSG[git_skip_ext]}" "${ESC[orange]}$repo_name${ESC[dark]}")"
    fi
}
cleanup_old_bundles() {
    local repo_name="$1"
    find "$GIT_BUNDLES" -name "${repo_name}_*.bundle" | sort -r | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f
}

# ┌────────────────────────────────────────────┐
# │ MAIN EXECUTION                             │
# └────────────────────────────────────────────┘
echo
cursor_hide
trap 'kill $SPINNER_PID 2>/dev/null; cursor_show' EXIT
log_tick "${MSG[git_start]}"
ensure_dirs
find "$GIT_SOURCES" -type d -name "*.git" | while read -r repo_path; do
    if [ ! -f "$repo_path/HEAD" ] || [ ! -d "$repo_path/objects" ]; then
        log_line "${ICON[warn]} ${MSG[git_skip_invalid]} $repo_path"
        continue
    fi
    repo_name=$(basename "$repo_path" .git)
    shallow_path="$GIT_SHALLOW/$repo_name"
    bundle_path="$GIT_BUNDLES/${repo_name}_$(date +%Y%m%d%H%M).bundle"
    log_spin "$(printf "${MSG[git_process]}" "$repo_name")"
    create_shallow_clone "$repo_path" "$shallow_path"
    create_bundle "$shallow_path" "$bundle_path"
    sync_to_external "$shallow_path" "$bundle_path" "$repo_name"
    cleanup_old_bundles "$repo_name"
    log_tick "$(printf "${MSG[git_done]}" "${ESC[orange]}$repo_name${ESC[dark]}")"
done
log_tick "${MSG[git_done_all]}"
cursor_show
```

## Final Thoughts

This script is a powerful tool for automating Git backups in a self-hosted environment. It ensures redundancy, minimizes storage usage with shallow clones, and keeps your backup history manageable.
