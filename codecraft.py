#!/usr/bin/env python3
"""
CodeCraft Static Site Generator
Terminal CLI on top of publish.py: build, serve, watch, clean, new
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from publish import DIR_BUILD, DIR_CONTENT, DIR_THEMES, SiteBuilder
from publish import MESSAGES as BUILD_MESSAGES

# ============================================================================
# CONSTANTS - Configuration and Magic Values
# ============================================================================

# Directory names
DIR_PYCACHE = '__pycache__'

# File extensions
EXT_MD = '.md'
EXT_HTML = '.html'

# Server defaults
DEFAULT_SERVER_PORT = 8000

# Regex patterns
PATTERN_CONSOLE_SUPPRESS = rb'// Aggressively suppress all console.*?\}\)\(\);\s*'

# Post template
POST_TEMPLATE = """---
title: "{title}"
date: {date}
comments: {comments}
toc: {toc}
mermaid: {mermaid}
codepen: {codepen}
---

## Introduction

Write your introduction here...
"""

# User messages
MESSAGES = {
    "error": {
        "editor_not_found": "Editor '{}' not found",
        "file_exists": "Warning: File {} already exists",
    },
    "examples": [
        "%(prog)s build Build the site",
        "%(prog)s serve Start local server (port 8000)",
        "%(prog)s serve -p 3000 Start local server on port 3000",
        "%(prog)s watch Watch for changes and rebuild",
        "%(prog)s clean Clean build artifacts",
        '%(prog)s new -c code -t "My Article" Create a new code post',
        '%(prog)s new -c design -t "UI Tips" -s ui-design-tips Custom slug',
        '%(prog)s new -c code -t "Python" --mermaid --edit With mermaid, open in editor',
    ],
    "help": {
        "command": "  command",
        "description": "Description",
        "new": "Create a new blog post",
        "category": "Post category",
        "clean": "Clean build artifacts",
        "port": f"Port number (default: {DEFAULT_SERVER_PORT})",
        "title": "Post title",
        "slug": "URL-friendly slug (auto-generated if not provided)",
        "date": "Post date (YYYY-MM-DD, default: today)",
        "no_comments": "Disable comments",
        "no_toc": "Disable table of contents",
        "mermaid": "Enable Mermaid diagrams",
        "codepen": "Enable CodePen embeds",
        "edit": "Open in $EDITOR after creation",
        "force": "Overwrite existing file without asking",
        "watch": "Watch for changes and rebuild automatically",
        "serve": "Start a local HTTP server",
        "build": "Build the static site",
    },
    "info": {
        "aborted": "Aborted.",
        "change_detected": "Change detected: {}",
        "clean_complete": "Clean complete",
        "cleaning": "Cleaning build artifacts...",
        'description': 'Blog management CLI - Build, serve, and manage your blog',
        "examples_title": "Examples:",
        "fedora_install": "Fedora: sudo dnf install inotify-tools",
        "inotifywait_hint": "\nAlternatively, use inotifywait (Linux):",
        "next_steps": "Next steps:",
        "pip_install": "pip install pyinotify",
        "post_category": "Category: {}",
        "post_created": "Created new post: {}",
        "post_date": "Date: {}",
        "post_slug": "Slug: {}",
        "post_title": "Title: {}",
        "pyinotify_not_installed": "pyinotify not installed. Install with:",
        "rebuilding": "Rebuilding...",
        "removed": "Removed {}",
        "server_dir": "Serving: {}",
        "server_start": "Starting local server at http://localhost:{}",
        "server_stop_hint": "Press Ctrl+C to stop",
        "server_stopped": "Server stopped",
        "server_rewrite": "(Auto-rewrites <base> tags for local development)",
        "step_build": "2. Build: python codecraft.py build",
        "step_edit": "1. Edit: {}",
        "step_deploy": "4. Deploy: git add {} && git commit -m 'Add: {}' && git push",
        "step_preview": "3. Preview: python codecraft.py serve",
        "ubuntu_install": "Ubuntu/Debian: sudo apt install inotify-tools",
        "watch_stopped": "Stopped watching",
        "watching": "Watching for changes...",
    },
    "prompt": {
        "overwrite": "Overwrite? (y/N): ",
    },
}

# Console symbols
CHECK = " \033[92m✔\033[0m"
CROSS = " \033[91m✘\033[0m"
ARROW = " \033[93m⮞\033[0m"
INFO = " \033[94mℹ\033[0m"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug

    Args:
        text: Text to slugify

    Returns:
        URL-safe slug
    """
    slug = ''.join(c if c.isalnum() or c in ' -' else '' for c in text.lower())
    slug = slug.replace(' ', '-')
    return re.sub(r'-{2,}', '-', slug).strip('-')


# ============================================================================
# TERMINAL BUILDER
# ============================================================================

class TerminalSiteBuilder(SiteBuilder):
    """SiteBuilder with colored warnings and a progress bar"""

    def warn(self, message: str) -> None:
        """Report a non-fatal problem

        Args:
            message: Warning text
        """
        print(f'{CROSS} {message}')

    def build(self) -> None:
        """Build the entire site"""
        steps = self.steps()

        with tqdm(total=len(steps), desc="Building site", unit="step", ncols=80,
                  bar_format="{l_bar}{bar} {n_fmt}/{total_fmt} [{elapsed}]") as progress:
            for index, (label, action) in enumerate(steps):
                symbol = CHECK if index == len(steps) - 1 else ARROW
                progress.set_description_str(f"{symbol} {index+1}. {label[:25].ljust(25)}")
                action()
                progress.update(1)

        print(f"{CHECK} {BUILD_MESSAGES['build_complete']}")
        print(f"{INFO} {BUILD_MESSAGES['build_stats'].format(self.post_count, len(self.pages))}")


# ============================================================================
# CLI INTERFACE
# ============================================================================

class BlogCLI:
    """Command-line interface for blog management"""

    def __init__(self):
        """Initialize the CLI"""
        self.root_dir = Path(__file__).parent

    def build(self, args: argparse.Namespace) -> None:
        """Build the site

        Args:
            args: Command-line arguments
        """
        TerminalSiteBuilder().build()

    def serve(self, args: argparse.Namespace) -> None:
        """Start local development server

        Args:
            args: Command-line arguments
        """
        port = args.port
        site_dir = self.root_dir / DIR_BUILD

        builder = TerminalSiteBuilder()
        if not site_dir.exists():
            print(BUILD_MESSAGES['building_site'])
            builder.build()

        site_url = f"{builder.base_url}/".encode()
        site_dir_abs = str(site_dir.resolve())

        print(MESSAGES['info']['server_start'].format(port))
        print(f"   {MESSAGES['info']['server_dir'].format(site_dir_abs)}")
        print(f"   {MESSAGES['info']['server_rewrite']}")
        print(f"   {MESSAGES['info']['server_stop_hint']}")

        import http.server
        import socketserver

        class RewritingHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            """HTTP handler that rewrites paths for local development"""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=site_dir_abs, **kwargs)

            def log_error(self, format: str, *args) -> None:
                """Suppress broken pipe errors"""
                if args and isinstance(args[0], str) and 'Broken pipe' in args[0]:
                    return
                super().log_error(format, *args)

            def send_head(self):
                """Override to handle HTML rewriting"""
                path = self.translate_path(self.path)
                f = None

                # Handle directory index
                if os.path.isdir(path):
                    parts = urllib.parse.urlsplit(self.path)
                    if not parts.path.endswith('/'):
                        self.send_response(301)
                        new_parts = (parts[0], parts[1], parts[2] + '/', parts[3], parts[4])
                        new_url = urllib.parse.urlunsplit(new_parts)
                        self.send_header("Location", new_url)
                        self.end_headers()
                        return None

                    for index in "index.html", "index.htm":
                        index_path = os.path.join(path, index)
                        if os.path.exists(index_path):
                            path = index_path
                            break

                try:
                    f = open(path, 'rb')
                except OSError:
                    self.send_error(404, "File not found")
                    return None

                try:
                    content = f.read()
                    f.close()

                    # Point <base> and absolute site URLs at the local root
                    if path.endswith(EXT_HTML) and (b'<html' in content or b'<!DOCTYPE' in content):
                        content = content.replace(site_url, b'/')
                        content = re.sub(
                            PATTERN_CONSOLE_SUPPRESS,
                            b'// Console suppression disabled for local development\n\n        ',
                            content,
                            flags=re.DOTALL
                        )

                    # Send response
                    self.send_response(200)
                    self.send_header("Content-type", self.guess_type(path))
                    self.send_header("Content-Length", str(len(content)))
                    if path.endswith(EXT_HTML):
                        self.send_header('Cache-Control', 'no-store')
                    self.end_headers()

                    return io.BytesIO(content)

                except Exception as e:
                    if f:
                        f.close()
                    self.send_error(500, f"Internal error: {e}")
                    return None

        class RewritingTCPServer(socketserver.TCPServer):
            """TCP server with address reuse enabled"""
            allow_reuse_address = True

        try:
            with RewritingTCPServer(("", port), RewritingHTTPRequestHandler) as httpd:
                httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['info']['server_stopped']}")

    def watch(self, args: argparse.Namespace) -> None:
        """Watch for changes and rebuild

        Args:
            args: Command-line arguments
        """
        try:
            import pyinotify
        except ImportError:
            print(MESSAGES['info']['pyinotify_not_installed'])
            print(f"   {MESSAGES['info']['pip_install']}")
            print(MESSAGES['info']['inotifywait_hint'])
            print(f"   {MESSAGES['info']['ubuntu_install']}")
            print(f"   {MESSAGES['info']['fedora_install']}")
            return

        print(MESSAGES['info']['watching'])
        print(f"   {MESSAGES['info']['server_stop_hint']}")

        self.build(args)

        wm = pyinotify.WatchManager()
        mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE

        class EventHandler(pyinotify.ProcessEvent):
            """File system event handler"""

            def __init__(self, cli: BlogCLI, args: argparse.Namespace):
                self.cli = cli
                self.args = args

            def process_default(self, event):
                """Handle file system events"""
                if not event.pathname.startswith(str(self.cli.root_dir / DIR_BUILD)):
                    print(f"\n{MESSAGES['info']['change_detected'].format(event.pathname)}")
                    print(f"   {MESSAGES['info']['rebuilding']}")
                    self.cli.build(self.args)

        handler = EventHandler(self, args)
        notifier = pyinotify.Notifier(wm, handler)

        watch_dirs = [DIR_THEMES, DIR_CONTENT]
        watch_files = ['codecraft.py', 'publish.py']

        for d in watch_dirs:
            path = self.root_dir / d
            if path.exists():
                wm.add_watch(str(path), mask, rec=True)

        for f in watch_files:
            path = self.root_dir / f
            if path.exists():
                wm.add_watch(str(path), mask)

        try:
            notifier.loop()
        except KeyboardInterrupt:
            print(f"\n{MESSAGES['info']['watch_stopped']}")

    def clean(self, args: argparse.Namespace) -> None:
        """Clean build artifacts

        Args:
            args: Command-line arguments
        """
        print(MESSAGES['info']['cleaning'])

        build_dir = self.root_dir / DIR_BUILD
        pycache = self.root_dir / DIR_PYCACHE

        if build_dir.exists():
            shutil.rmtree(build_dir)
            print(f"  {MESSAGES['info']['removed'].format(build_dir)}")

        if pycache.exists():
            shutil.rmtree(pycache)
            print(f"  {MESSAGES['info']['removed'].format(pycache)}")

        print(MESSAGES['info']['clean_complete'])

    def new(self, args: argparse.Namespace) -> None:
        """Create a new blog post

        Args:
            args: Command-line arguments
        """
        # Generate slug
        slug = args.slug if args.slug else slugify(args.title)

        # Get date
        date = args.date if args.date else datetime.now().strftime('%Y-%m-%d')

        # Create directory structure
        content_dir = self.root_dir / DIR_CONTENT
        content_dir.mkdir(exist_ok=True)
        directory = content_dir / args.category
        directory.mkdir(exist_ok=True)

        # Create file
        filename = directory / f"{slug}{EXT_MD}"

        if filename.exists() and not args.force:
            print(MESSAGES['error']['file_exists'].format(filename))
            response = input(MESSAGES['prompt']['overwrite'])
            if response.lower() != 'y':
                print(MESSAGES['info']['aborted'])
                sys.exit(0)

        content = POST_TEMPLATE.format(
            title=args.title,
            date=date,
            comments='true' if args.comments else 'false',
            toc='true' if args.toc else 'false',
            mermaid='true' if args.mermaid else 'false',
            codepen='true' if args.codepen else 'false'
        )

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(MESSAGES['info']['post_created'].format(filename))
        print(f"   {MESSAGES['info']['post_title'].format(args.title)}")
        print(f"   {MESSAGES['info']['post_category'].format(args.category)}")
        print(f"   {MESSAGES['info']['post_slug'].format(slug)}")
        print(f"   {MESSAGES['info']['post_date'].format(date)}")
        print()
        print(MESSAGES['info']['next_steps'])
        print(f"  {MESSAGES['info']['step_edit'].format(filename)}")
        print(f"  {MESSAGES['info']['step_build']}")
        print(f"  {MESSAGES['info']['step_preview']}")
        print(f"  {MESSAGES['info']['step_deploy'].format(filename, args.title)}")

        if args.edit:
            editor = os.environ.get('EDITOR', 'vim')
            try:
                subprocess.run([editor, str(filename)])
            except FileNotFoundError:
                print(MESSAGES['error']['editor_not_found'].format(editor))


def main() -> None:
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description=MESSAGES["info"]["description"],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(MESSAGES["info"]["examples_title"] + "\n  " + "\n  ".join(MESSAGES["examples"]))
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help=MESSAGES["help"]["description"],
        metavar=MESSAGES["help"]["command"]
    )

    # Build command
    subparsers.add_parser(
        'build',
        help=MESSAGES["help"]["build"],
    )

    # Serve command
    serve_parser = subparsers.add_parser(
        'serve',
        help=MESSAGES["help"]["serve"]
    )
    serve_parser.add_argument(
        '-p', '--port',
        type=int,
        default=DEFAULT_SERVER_PORT,
        help=MESSAGES["help"]["port"]
    )

    # Watch command
    subparsers.add_parser(
        'watch',
        help=MESSAGES["help"]["watch"]
    )

    # Clean command
    subparsers.add_parser(
        'clean',
        help=MESSAGES["help"]["clean"]
    )

    # New command
    new_parser = subparsers.add_parser(
        'new',
        help=MESSAGES["help"]["new"]
    )
    new_parser.add_argument(
        '-c', '--category',
        required=True,
        choices=TerminalSiteBuilder().config['sections'],
        help=MESSAGES["help"]["category"]
    )
    new_parser.add_argument(
        '-t', '--title',
        required=True,
        help=MESSAGES["help"]["title"]
    )
    new_parser.add_argument(
        '-s', '--slug',
        help=MESSAGES["help"]["slug"]
    )
    new_parser.add_argument(
        '-d', '--date',
        help=MESSAGES["help"]["date"]
    )
    new_parser.add_argument(
        '--no-comments',
        dest='comments',
        action='store_false',
        default=True,
        help=MESSAGES["help"]["no_comments"]
    )
    new_parser.add_argument(
        '--no-toc',
        dest='toc',
        action='store_false',
        default=True,
        help=MESSAGES["help"]["no_toc"]
    )
    new_parser.add_argument(
        '--mermaid',
        action='store_true',
        help=MESSAGES["help"]["mermaid"]
    )
    new_parser.add_argument(
        '--codepen',
        action='store_true',
        help=MESSAGES["help"]["codepen"]
    )
    new_parser.add_argument(
        '-e', '--edit',
        action='store_true',
        help=MESSAGES["help"]["edit"]
    )
    new_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help=MESSAGES["help"]["force"]
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = BlogCLI()
    commands = {
        'build': cli.build,
        'serve': cli.serve,
        'watch': cli.watch,
        'clean': cli.clean,
        'new': cli.new,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
