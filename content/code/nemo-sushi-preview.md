---
title: "Nemo Sushi Preview: Quick Look for Linux"
date: 2026-04-19
comments: true
---

**Nemo Sushi Preview**: A Python extension that adds GNOME Sushi file previews to the Nemo file manager — triggered by the spacebar or right-click menu, the way Quick Look works on macOS.

## The Spacebar Gap

macOS users take Quick Look for granted. Select a file, press Space, see a full preview. No application opens. No window to manage. Just the content, immediately.

Linux file managers have partial support for this. Nautilus (GNOME Files) integrates GNOME Sushi natively. But Nemo — the file manager from the Cinnamon desktop, preferred by many for its dual-pane layout and traditional interface — doesn't ship with Sushi integration.

This extension adds it.

## How It Works

The extension hooks into Nemo's Python extension API. When you select a file and press Space (or right-click and choose Preview), it invokes GNOME Sushi with the selected file's URI.

```python
import subprocess
import urllib.parse
from pathlib import Path

class SushiPreviewExtension(GObject.GObject, Nemo.MenuProvider, Nemo.LocationWidgetProvider):

    def get_file_items(self, window, files):
        if len(files) != 1:
            return []

        item = Nemo.MenuItem(
            name="SushiPreview::Preview",
            label="Preview",
            tip="Preview file with GNOME Sushi",
        )
        item.connect("activate", self._preview, files[0])
        return [item]

    def _preview(self, menu, file):
        uri = file.get_uri()
        subprocess.Popen(["sushi", uri])
```

The spacebar binding hooks into Nemo's keyboard shortcut system. Nemo extensions can register keybindings through the `Nemo.KeybindingExtension` interface, mapping the Space key to the preview action when a single file is selected.

## Installation

```bash
git clone https://github.com/lucianofedericopereira/nemo-sushi-preview
cd nemo-sushi-preview

# Install GNOME Sushi if not already present
sudo apt install gnome-sushi    # Debian/Ubuntu
sudo dnf install gnome-sushi    # Fedora

# Install the extension
mkdir -p ~/.local/share/nemo/extensions
cp sushi_preview.py ~/.local/share/nemo/extensions/

# Restart Nemo
nemo -q && nemo &
```

## What Sushi Previews

GNOME Sushi handles most file types you'll encounter:

| Type | Preview |
|------|---------|
| Images (PNG, JPG, WebP, SVG) | Full image with zoom |
| Documents (PDF, ODF) | Rendered pages |
| Text files | Syntax-highlighted content |
| Audio (MP3, FLAC, OGG) | Waveform + playback controls |
| Video (MP4, MKV, WebM) | Inline playback |
| Fonts | Character map and specimen |
| Archives | File listing |

The preview window is keyboard-navigable. Arrow keys step through selected files. Escape closes. It feels like it belongs in the OS because Sushi is a genuine GNOME component — it just wasn't wired up to Nemo.

## The Small Friction Problem

This is a small extension solving a small problem. But small frictions compound. Every time you open an image to verify it's the right one, then close the viewer, then select the next file — that's a workflow interruption. Multiply by ten images, and the friction becomes real time.

The best tools remove friction so completely that you stop noticing the tool exists. This extension is trying to be one of those.

## Links

- **GitHub**: [lucianofedericopereira/nemo-sushi-preview](https://github.com/lucianofedericopereira/nemo-sushi-preview)
- **GNOME Sushi**: [gitlab.gnome.org/GNOME/sushi](https://gitlab.gnome.org/GNOME/sushi)

## License

GPL-2.0
