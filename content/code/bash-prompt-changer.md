---
title: "Bash Prompt Changer: A Gallery for Your Terminal"
date: 2025-07-04
comments: true
---

**Bash Prompt Changer**: A shell script that rotates through a curated gallery of bash prompt themes, turning your `PS1` from an afterthought into something you actually look forward to seeing.

## Why the Prompt Matters

You stare at your bash prompt more than almost any other piece of text on your screen. It's there between every command, setting the visual rhythm of your terminal session. Most people set it once, forget about it, and spend years looking at `user@host:~$`.

There's a better way — not necessarily a permanent theme you commit to, but a rotating gallery that shows you what's possible and lets you settle on what fits.

## How It Works

The script maintains a directory of prompt definitions — each one a small Bash file that sets `PS1` and optionally `PS2`. Running the script sources a new one, cycling through the gallery.

```bash
#!/usr/bin/env bash

PROMPT_DIR="${HOME}/.bash_prompts"
STATE_FILE="${HOME}/.bash_prompt_state"

# Read current index
current=0
[ -f "$STATE_FILE" ] && current=$(cat "$STATE_FILE")

# Get sorted list of prompts
prompts=("$PROMPT_DIR"/*.sh)
total=${#prompts[@]}

# Wrap around
next=$(( (current + 1) % total ))

# Source the new prompt
source "${prompts[$next]}"

# Save state
echo "$next" > "$STATE_FILE"

echo "Prompt ${next+1}/${total}: $(basename "${prompts[$next]}" .sh)"
```

Add this to your `.bashrc` or bind it to a key:

```bash
bind '"\C-p": "source ~/.local/bin/bash-prompt-changer\n"'
```

Now `Ctrl+P` cycles your prompt without leaving the terminal.

## What a Prompt Definition Looks Like

Each theme in the gallery is a standalone `.sh` file that sets the prompt variables and nothing else:

```bash
# theme: minimal-git
__git_branch() {
  git branch 2>/dev/null | grep '^\*' | cut -d' ' -f2
}

PS1='\[\e[2m\]$(__git_branch) \[\e[0m\]\[\e[1m\]\W\[\e[0m\] › '
```

```bash
# theme: retro-green
PS1='\[\e[32m\]┌─[\u@\h]─[\w]\n\[\e[32m\]└─▶\[\e[0m\] '
```

```bash
# theme: minimal
PS1='\[\e[90m\]\W\[\e[0m\] $ '
```

The isolation matters: each file is self-contained. A broken theme doesn't break other themes. You can add and remove files from the gallery directory without touching the rotation script.

## The 256-Color Palette

Bash prompts have access to the full xterm 256-color palette, which most people never use because the escape sequences are awkward to type:

```bash
# Set foreground to color 208 (orange)
\[\e[38;5;208m\]

# Set background to color 236 (dark gray)  
\[\e[48;5;236m\]
```

The script includes helper functions that make these readable:

```bash
fg() { printf '\[\e[38;5;%dm\]' "$1"; }
bg() { printf '\[\e[48;5;%dm\]' "$1"; }
reset='\[\e[0m\]'

PS1="$(bg 236)$(fg 208) \W $(reset)$(fg 236)$(reset) "
```

## Nerd Fonts Integration

When paired with a [Nerd Font](https://www.nerdfonts.com), the prompt can use icon glyphs directly:

```bash
# Git branch icon: 
# Folder icon: 
# Arrow: 

PS1=' \[\e[34m\]\W\[\e[0m\]  $(__git_branch) $ '
```

This is purely cosmetic but meaningfully changes how the terminal feels to work in. The information density goes up; the visual noise stays manageable.

## Building Your Own Theme

The gallery is a starting point, not a limit. Writing a new theme takes five minutes:

1. Create `~/.bash_prompts/my-theme.sh`
2. Set `PS1` and optionally `PS2`
3. Run the changer — it appears in the rotation immediately

The constraint of one file per theme keeps things clean. If you find yourself writing more than twenty lines, the prompt is doing too much.

## Links

- **GitHub**: [lucianofedericopereira/bash-prompt-changer](https://github.com/lucianofedericopereira/bash-prompt-changer)

## License

MIT
