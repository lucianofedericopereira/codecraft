---
title: "Oh My GruvBox: Bringing Retro Colors to Oh My Posh"
date: 2026-05-22
comments: true
---

**Oh My GruvBox**: A Gruvbox-inspired theme for Oh My Posh — warm off-whites, forest greens, terracotta accents, and the golden yellows of the original Gruvbox palette, translated into a terminal prompt that feels cohesive and lived-in.

## Why Gruvbox

Gruvbox, created by Pavel Pertsev, has been one of the most enduring color schemes in the programming world. Where most themes aim for maximum contrast — stark whites on pure black, or neon colors on dark backgrounds — Gruvbox aims for warmth. The palette is derived from retro-computing aesthetics: amber monitors, warm fluorescent lighting, paper and wood.

The colors are:
- **Background**: A warm dark gray, not pure black
- **Text**: A warm off-white, not pure white
- **Accent colors**: Muted but saturated — forest green, burnt orange, golden yellow, dusty rose

Staring at code in Gruvbox for eight hours is qualitatively different from staring at a high-contrast dark theme. The warmth reduces fatigue in a way that's hard to quantify but easy to notice.

## Oh My Posh

Oh My Posh is a prompt theme engine for any shell — bash, zsh, fish, PowerShell. It reads a JSON configuration file and renders a themed prompt with segments for git status, current directory, language versions, time, and anything else you configure.

The GruvBox theme configuration:

```json
{
  "$schema": "https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/main/themes/schema.json",
  "blocks": [
    {
      "type": "prompt",
      "alignment": "left",
      "segments": [
        {
          "type": "path",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#282828",
          "background": "#d79921",
          "properties": {
            "style": "folder",
            "max_depth": 3
          }
        },
        {
          "type": "git",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#282828",
          "background": "#98971a",
          "foreground_templates": [
            "{{ if .Working.Changed }}#cc241d{{ end }}"
          ],
          "properties": {
            "branch_icon": " ",
            "fetch_status": true
          }
        },
        {
          "type": "exit",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#282828",
          "background": "#458588",
          "templates": [
            "{{ if .Success }}  {{ else }}  {{ end }}"
          ]
        }
      ]
    }
  ],
  "final_space": true
}
```

The Gruvbox palette in hex:
```
Background: #282828    Bright Blue:   #83a598
Red:        #cc241d    Bright Purple: #d3869b
Green:      #98971a    Bright Aqua:   #8ec07c
Yellow:     #d79921    Bright Orange: #fe8019
Blue:       #458588    Foreground:    #ebdbb2
Purple:     #b16286    Gray:          #928374
Aqua:       #689d6a    Bright Red:    #fb4934
Orange:     #d65d0e    Bright Green:  #b8bb26
```

## Installation

```bash
# Install Oh My Posh
curl -s https://ohmyposh.dev/install.sh | bash -s

# Download the theme
curl -o ~/.config/oh-my-posh/gruvbox.json \
  https://raw.githubusercontent.com/lucianofedericopereira/oh-my-gruvbox/main/gruvbox.omp.json

# Set in your shell config (.bashrc, .zshrc)
eval "$(oh-my-posh init bash --config ~/.config/oh-my-posh/gruvbox.json)"
```

A Nerd Font is required for the powerline symbols and icons. Recommended: JetBrains Mono Nerd Font, or FiraCode Nerd Font.

## The Terminal Stack

The theme is designed to pair with a Gruvbox terminal color scheme. In Alacritty:

```toml
[colors.primary]
background = "#282828"
foreground = "#ebdbb2"

[colors.normal]
black   = "#282828"
red     = "#cc241d"
green   = "#98971a"
yellow  = "#d79921"
blue    = "#458588"
magenta = "#b16286"
cyan    = "#689d6a"
white   = "#a89984"
```

When the terminal colors, the shell prompt, and the editor theme all use the same palette, the environment stops feeling like a collection of separate tools and starts feeling like a unified workspace. That coherence is worth the effort of alignment.

## Extending the Theme

Oh My Posh themes are JSON — readable, editable, version-controllable. Adding a segment:

```json
{
  "type": "node",
  "style": "powerline",
  "powerline_symbol": "",
  "foreground": "#282828",
  "background": "#8ec07c",
  "properties": {
    "display_mode": "files"
  }
}
```

This adds a Node.js version indicator using Gruvbox aqua — only visible when you're in a directory with a `package.json`.

## Links

- **GitHub**: [lucianofedericopereira/oh-my-gruvbox](https://github.com/lucianofedericopereira/oh-my-gruvbox)
- **Oh My Posh**: [ohmyposh.dev](https://ohmyposh.dev)

## License

MIT
