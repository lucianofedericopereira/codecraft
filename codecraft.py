#!/usr/bin/env python3
"""
CodeCraft Static Site Generator
A Python-based static site generator using Jinja2 templates and Markdown
"""
from __future__ import annotations

import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import argparse
import frontmatter
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from markdown import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from tqdm import tqdm

# ============================================================================
# CONSTANTS - Configuration and Magic Values
# ============================================================================

# Internationalization
MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
    "it": ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
}

# Directory names
DIR_ASSETS = 'assets'
DIR_BUILD = 'build'
DIR_SECTIONS = 'sections'
DIR_CONTENT = 'content'
DIR_PYCACHE = '__pycache__'
DIR_TEMPLATES = 'templates'
DIR_THEMES = 'themes'

# File names
FILE_CONFIG_PATH = 'themes/config.yaml'
FILE_CSS_TEMPLATE = 'codeCraft.css'
FILE_CODECRAFT_CSS = 'codeCraft.css'
FILE_FEED = 'feed.xml'
FILE_SEARCH = 'search.json'

# File extensions
EXT_MD = '.md'
EXT_HTML = '.html'
EXT_CSS = '.css'
EXT_JS = '.js'

# Markdown configuration
MD_EXTENSIONS = ['extra', 'toc']

# CSS classes
CSS_CLASS_HIGHLIGHT = 'highlight'
CSS_CLASS_HIGHLIGHTER_ROUGE = 'highlighter-rouge'
CSS_CLASS_LANGUAGE_PLAINTEXT = 'language-plaintext highlighter-rouge'
CSS_CLASS_LANGUAGE_MERMAID = 'language-mermaid'

# Server defaults
DEFAULT_SERVER_PORT = 8000

# Regex patterns
PATTERN_MERMAID_BLOCK = r'```mermaid\n(.*?)```'
PATTERN_CODE_BLOCK = r'```(\w+)?\n(.*?)```'
PATTERN_EXAMPLE_SHORTCODE = r'\[example:(\d+)\]'
PATTERN_BASE_TAG = rb'<base\s+href="[^"]*"[^>]*>\s*'
PATTERN_CONSOLE_SUPPRESS = rb'// Aggressively suppress all console.*?\}\)\(\);\s*'

# Include directive placeholders
PLACEHOLDER_POSTS = 'INCLUDE_POSTS_PLACEHOLDER'
PLACEHOLDER_CATEGORY = 'INCLUDE_CATEGORY_PLACEHOLDER'
PLACEHOLDER_ARCHIVE = 'INCLUDE_ARCHIVE_PLACEHOLDER'

# Template names
TEMPLATE_MAIN = 'codeCraft.html'
TEMPLATE_POSTS = 'posts.html'
TEMPLATE_CATEGORY = 'category.html'
TEMPLATE_ARCHIVE = 'archive.html'

# Post limits
DEFAULT_POST_LIMIT = 10
FEED_POST_LIMIT = 10

# Font weight mappings
FONT_WEIGHT_MAP = {
    'thin': '100',
    'extralight': '200',
    'light': '300',
    'regular': '400',
    'medium': '500',
    'semibold': '600',
    'bold': '700',
    'extrabold': '800',
    'black': '900'
}

# Default configuration
DEFAULT_CONFIG = {
    "post_limit": DEFAULT_POST_LIMIT,
    "search_enabled": False,
    "base": {
        "url": "localhost",
        "folder": ""
    },
    "meta": {
        "title": "My Blog",
        "tagline": "A simple blog",
        "author": "Anonymous",
        "repository": "",
        "license": "",
        "locale": "en"
    },
    "assets": {
        "images": {
            "logo": "codeCraft.ico",
            "favicon": "codeCraft.ico"
        },
        "fonts": []
    },
    "links": {},
    "sections": ["design", "code", "projects"],
    "rules": [],
    "scripts": {},
}

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
        "category": "Error: Category must be one of: {}",
        "sections_not_found": "Sections directory not found: {}",
        "config_not_found": "Config file not found: {}",
        "editor_not_found": "Editor '{}' not found",
        "file_exists": "Warning: File {} already exists",
        "invalid_yaml": "Invalid YAML format in {}: {}",
        "loading_template": "Error loading template {}: {}",
        "parsing_markdown": "Error parsing markdown in {}: {}",
        "reading_file": "Error reading {}: {}",
        "rendering_template": "Error rendering template {}: {}",
        "template_not_found": "Template not found: {}",
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
        "build_complete": "Build complete! Output in build/",
        "building_site": "Building site...",
        "build_stats": "Posts: {}, Pages: {}",
        "build_steps": [
            "Cleaning output directory ",
            "Collecting posts and pages",
            "Rendering posts           ",
            "Rendering pages           ",
            "Generating feed & search  ",
            "Copying static assets     ",
        ],
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
        "using_default_config": "Using default configuration",
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
# DATA CLASSES
# ============================================================================

@dataclass
class PostData:
    """Represents a blog post or page with its metadata"""
    content: str
    title: str
    date: str
    url: str
    file_path: Path
    comments: bool = False
    mermaid: bool = False
    codepen: bool = False
    toc: bool = False
    banner: bool = False
    sidebar: bool = True
    collection: str = ""
    section: str = ""
    include_directives: Dict[str, str] = None

    def __post_init__(self):
        if self.include_directives is None:
            self.include_directives = {}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def apply_defaults(data: Optional[Dict], defaults: Dict) -> Dict:
    """Deep merge defaults into data dictionary

    Args:
        data: Target dictionary
        defaults: Source dictionary with default values

    Returns:
        Merged dictionary with defaults applied
    """
    def deep_merge(target: Dict, source: Dict) -> Dict:
        for key, value in source.items():
            if isinstance(value, dict):
                node = target.setdefault(key, {})
                deep_merge(node, value)
            else:
                target.setdefault(key, value)
        return target

    merged_data = copy.deepcopy(data) if data else {}
    return deep_merge(merged_data, defaults)


def strip_all_whitespace(value: str) -> str:
    """Remove all whitespace from a string"""
    return re.sub(r'\s+', '', value)


def normalize_url_path(path: str) -> str:
    """Normalize URL path by stripping leading/trailing slashes

    Args:
        path: URL path to normalize

    Returns:
        Normalized path without leading/trailing slashes
    """
    return path.strip('/')


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug

    Args:
        text: Text to slugify

    Returns:
        URL-safe slug
    """
    slug = text.lower()
    slug = ''.join(c if c.isalnum() or c in ' -' else '' for c in slug)
    slug = slug.replace(' ', '-').strip('-')
    # Remove consecutive dashes
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug


# ============================================================================
# DATE FORMATTING FUNCTIONS
# ============================================================================

def format_month_year(date_str: str, lang: str = "en") -> str:
    """Format YYYY-MM date string to abbreviated month + year

    Args:
        date_str: Date string in YYYY-MM format
        lang: Language code (en, es, it)

    Returns:
        Formatted string like "Jan 2024" or original string if parsing fails
    """
    if not date_str:
        return ""
    try:
        year, month = str(date_str).split("-")[:2]
        month_index = int(month) - 1
        return f"{MONTHS.get(lang, MONTHS['en'])[month_index]} {year}"
    except Exception:
        return str(date_str)


def format_date_archive(date_str: str, lang: str = "en") -> str:
    """Format YYYY-MM-DD date string to 3-letter month + padded day

    Args:
        date_str: Date string in YYYY-MM-DD format
        lang: Language code (en, es, it)

    Returns:
        Formatted string like "Nov 17" or original string if parsing fails
    """
    if not date_str:
        return ""
    try:
        parts = str(date_str).split("-")
        if len(parts) >= 3:
            year, month, day = parts[:3]
            month_index = int(month) - 1
            day_num = int(day)
            return f"{MONTHS.get(lang, MONTHS['en'])[month_index]} {day_num:02d}"
        return str(date_str)
    except Exception:
        return str(date_str)


def extract_year(date_str: str) -> str:
    """Extract year from YYYY-MM-DD date string

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Year as string or original string if parsing fails
    """
    if not date_str:
        return ""
    try:
        return str(date_str).split("-")[0]
    except Exception:
        return str(date_str)


def format_date_full(date_str: str, lang: str = "en") -> str:
    """Format YYYY-MM-DD date string to 3-letter month + padded day + year

    Args:
        date_str: Date string in YYYY-MM-DD format
        lang: Language code (en, es, it)

    Returns:
        Formatted string like "Nov 17, 2025" or original string if parsing fails
    """
    if not date_str:
        return ""
    try:
        parts = str(date_str).split("-")
        if len(parts) >= 3:
            year, month, day = parts[:3]
            month_index = int(month) - 1
            day_num = int(day)
            return f"{MONTHS.get(lang, MONTHS['en'])[month_index]} {day_num:02d}, {year}"
        return str(date_str)
    except Exception:
        return str(date_str)


def format_date_jinja(value: Any, format: str = '%B %d, %Y') -> str:
    """Format date for Jinja2 templates

    Args:
        value: Date value (string or datetime object)
        format: strftime format string

    Returns:
        Formatted date string
    """
    from datetime import date
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except Exception:
            return value
    if isinstance(value, (datetime, date)):
        return value.strftime(format)
    return value


# ============================================================================
# TEMPLATE RENDERING
# ============================================================================

def render_template_safe(env: Environment, template_name: str, context: Dict) -> Optional[str]:
    """Safely render a template with comprehensive error handling

    Args:
        env: Jinja2 Environment
        template_name: Template filename
        context: Context dictionary for rendering

    Returns:
        Rendered string or None on error
    """
    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        print(f'{CROSS} {MESSAGES["error"]["template_not_found"].format(template_name)}')
        return None
    except Exception as e:
        print(f'{CROSS} {MESSAGES["error"]["loading_template"].format(template_name, e)}')
        return None

    try:
        return template.render(**context)
    except Exception as e:
        print(f'{CROSS} {MESSAGES["error"]["rendering_template"].format(template_name, e)}')
        return None


# ============================================================================
# MARKDOWN PROCESSING
# ============================================================================

def extract_include_directives(content: str) -> Tuple[str, Dict[str, str]]:
    """Extract Jinja include directives and replace with placeholders

    Args:
        content: Markdown content with include directives

    Returns:
        Tuple of (modified content, directives dict)
    """
    include_directives = {}

    # Posts include
    if '{%- include posts.html -%}' in content or '{% include posts.html %}' in content:
        include_directives[PLACEHOLDER_POSTS] = 'posts'
        content = content.replace('{%- include posts.html -%}', PLACEHOLDER_POSTS)
        content = content.replace('{% include posts.html %}', PLACEHOLDER_POSTS)

    # Category include
    if '{%- include category.html -%}' in content or '{% include category.html %}' in content:
        include_directives[PLACEHOLDER_CATEGORY] = 'category'
        content = content.replace('{%- include category.html -%}', PLACEHOLDER_CATEGORY)
        content = content.replace('{% include category.html %}', PLACEHOLDER_CATEGORY)

    # Archive include
    if '{%- include archive.html -%}' in content or '{% include archive.html %}' in content:
        include_directives[PLACEHOLDER_ARCHIVE] = 'archive'
        content = content.replace('{%- include archive.html -%}', PLACEHOLDER_ARCHIVE)
        content = content.replace('{% include archive.html %}', PLACEHOLDER_ARCHIVE)

    return content, include_directives


def extract_example_shortcodes(content: str, directives: Dict[str, str]) -> str:
    """Replace [example:N] shortcodes with placeholders

    Args:
        content: Markdown content
        directives: Dictionary to store directive mappings

    Returns:
        Content with placeholders
    """
    def replace_example(match):
        example_id = match.group(1)
        placeholder = f'EXAMPLE_PLACEHOLDER_{example_id}'
        directives[placeholder] = f'example:{example_id}'
        return f'\n\n{placeholder}\n\n'

    return re.sub(PATTERN_EXAMPLE_SHORTCODE, replace_example, content)


def extract_mermaid_blocks(content: str) -> Tuple[str, List[str]]:
    """Extract mermaid blocks and replace with placeholders

    Args:
        content: Markdown content

    Returns:
        Tuple of (content with placeholders, list of mermaid blocks)
    """
    mermaid_blocks = []

    def save_mermaid(match):
        mermaid_blocks.append(match.group(1))
        return f'\n\nMERMAID_PLACEHOLDER_{len(mermaid_blocks)-1}\n\n'

    content = re.sub(PATTERN_MERMAID_BLOCK, save_mermaid, content, flags=re.DOTALL)
    return content, mermaid_blocks


def restore_mermaid_blocks(content_html: str, mermaid_blocks: List[str]) -> str:
    """Restore mermaid blocks with proper language class

    Args:
        content_html: HTML content with placeholders
        mermaid_blocks: List of mermaid block contents

    Returns:
        HTML with restored mermaid blocks
    """
    for i, mermaid_content in enumerate(mermaid_blocks):
        content_html = content_html.replace(
            f'<p>MERMAID_PLACEHOLDER_{i}</p>',
            f'<pre><code class="{CSS_CLASS_LANGUAGE_MERMAID}">{mermaid_content}</code></pre>'
        )
    return content_html


def highlight_code_blocks(content: str) -> str:
    """Process fenced code blocks with Pygments syntax highlighting

    Args:
        content: Markdown content with fenced code blocks

    Returns:
        Content with highlighted code blocks
    """
    def highlight_match(match):
        lang = match.group(1) or 'text'
        code = match.group(2)
        try:
            lexer = get_lexer_by_name(lang, stripall=False)
            formatter = HtmlFormatter(cssclass=CSS_CLASS_HIGHLIGHT, noclasses=False)
            highlighted = highlight(code, lexer, formatter)
            return f'<div class="{CSS_CLASS_HIGHLIGHTER_ROUGE}">{highlighted}</div>'
        except:
            return f'<div class="{CSS_CLASS_HIGHLIGHTER_ROUGE}"><div class="{CSS_CLASS_HIGHLIGHT}"><pre><code class="language-{lang}">{code}</code></pre></div></div>'

    return re.sub(PATTERN_CODE_BLOCK, highlight_match, content, flags=re.DOTALL)


def add_inline_code_classes(content_html: str) -> str:
    """Add CSS classes to inline code elements

    Args:
        content_html: HTML content

    Returns:
        HTML with classes added to inline code
    """
    return re.sub(
        r'<code>(?!</code>)',
        f'<code class="{CSS_CLASS_LANGUAGE_PLAINTEXT}">',
        content_html
    )


def process_markdown_content(content: str) -> Tuple[str, Dict[str, str]]:
    """Process markdown content with all transformations

    Args:
        content: Raw markdown content

    Returns:
        Tuple of (processed HTML, include directives dict)
    """
    # Extract include directives
    content, include_directives = extract_include_directives(content)

    # Extract example shortcodes
    content = extract_example_shortcodes(content, include_directives)

    # Extract mermaid blocks
    content, mermaid_blocks = extract_mermaid_blocks(content)

    # Highlight code blocks
    content = highlight_code_blocks(content)

    # Convert markdown to HTML
    content_html = markdown(content, extensions=MD_EXTENSIONS, extension_configs={})

    # Add classes to inline code
    content_html = add_inline_code_classes(content_html)

    # Restore mermaid blocks
    content_html = restore_mermaid_blocks(content_html, mermaid_blocks)

    return content_html, include_directives


# ============================================================================
# SITE BUILDER
# ============================================================================

class SiteBuilder:
    """Main site builder class that handles all build operations"""

    def __init__(self, config_path: str = FILE_CONFIG_PATH):
        """Initialize the site builder

        Args:
            config_path: Path to config file
        """
        self.root_dir = Path(__file__).parent
        self.config = self._load_config(config_path)
        self.output_dir = self.root_dir / DIR_BUILD
        self.theme_dir = self.root_dir / DIR_THEMES
        self.templates_dir = self.theme_dir / DIR_TEMPLATES

        # Set base URL
        self.base_url = self._build_base_url()

        # Initialize Jinja2 environment
        self.env = self._create_jinja_environment()

        # Resolve asset URLs
        self.asset_urls = self._get_asset_urls()

        # Storage for posts and pages
        sections = self.config.get('sections', [])
        self.posts = {name: [] for name in sections} if sections else {'design': [], 'code': [], 'projects': []}
        self.pages = []

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        config_file = self.root_dir / config_path
        config = {}

        if not config_file.exists():
            print(f'{CROSS} {MESSAGES["error"]["config_not_found"].format(config_path)}')
            print(f'{INFO}  {MESSAGES["info"]["using_default_config"]}')
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    config = config if config else {}
            except yaml.YAMLError as e:
                print(f'{CROSS} {MESSAGES["error"]["invalid_yaml"].format(config_path, e)}')
                print(f'{INFO}  {MESSAGES["info"]["using_default_config"]}')
                config = {}
            except Exception as e:
                print(f'{CROSS} {MESSAGES["error"]["reading_file"].format(config_path, e)}')
                print(f'{INFO}  {MESSAGES["info"]["using_default_config"]}')
                config = {}

        return apply_defaults(config, DEFAULT_CONFIG)

    def _build_base_url(self) -> str:
        """Build the base URL from config

        Returns:
            Base URL string
        """
        folder = self.config.get('base', {}).get('folder', '')
        base_domain = self.config['base']['url']

        if folder:
            return f"https://{base_domain}/{folder}"
        else:
            return f"https://{base_domain}"

    def _create_jinja_environment(self) -> Environment:
        """Create and configure Jinja2 environment

        Returns:
            Configured Jinja2 Environment
        """
        env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

        # Add custom filters
        env.filters['date_format'] = format_date_jinja
        env.filters['month_year'] = format_month_year
        env.filters['date_archive'] = format_date_archive
        env.filters['date_full'] = format_date_full
        env.filters['year'] = extract_year
        env.filters['strip_whitespace'] = strip_all_whitespace
        env.filters['split'] = lambda s, sep: s.split(sep) if s else []

        return env

    def _get_asset_urls(self) -> Dict[str, str]:
        """Generate CDN URLs from script version numbers in config

        Returns:
            Dictionary with CDN URLs for lunr and mermaid
        """
        scripts = self.config.get('scripts', {})

        return {
            'lunr': f"https://cdn.jsdelivr.net/npm/lunr@{scripts.get('lunr', '2.3.9')}/+esm",
            'mermaid': f"https://cdn.jsdelivr.net/npm/mermaid@{scripts.get('mermaid', '11.4.1')}/+esm"
        }

    def _get_path_defaults(self, file_path: Path) -> Dict[str, bool]:
        """Get default frontmatter values for a file path based on config rules

        Args:
            file_path: Path to the file

        Returns:
            Dictionary of default values
        """
        rules_config = self.config.get('rules', [])
        file_path_str = str(file_path)

        defaults = {
            'toc': False,
            'comments': False,
            'mermaid': False,
            'codepen': False,
            'banner': False
        }

        for rule in rules_config:
            scope = rule.get('scope', {})
            scope_path = scope.get('path', '')

            if scope_path and scope_path in file_path_str:
                if 'features' in rule:
                    defaults.update(rule['features'])

        return defaults

    def parse_markdown_file(self, file_path: Path, is_post: bool = True) -> Optional[Dict]:
        """Parse a markdown file with frontmatter

        Args:
            file_path: Path to markdown file
            is_post: True for blog posts, False for pages

        Returns:
            Dictionary with post data or None on error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
        except Exception as e:
            print(f'{CROSS} {MESSAGES["error"]["reading_file"].format(file_path, e)}')
            return None

        path_defaults = self._get_path_defaults(file_path)

        try:
            content_html, include_directives = process_markdown_content(post.content)
        except Exception as e:
            print(f'{CROSS} {MESSAGES["error"]["parsing_markdown"].format(file_path, e)}')
            return None

        return {
            'content': content_html,
            'title': post.get('title', ''),
            'date': post.get('date', ''),
            'comments': post.get('comments', path_defaults.get('comments', False)),
            'mermaid': post.get('mermaid', path_defaults.get('mermaid', False)),
            'codepen': post.get('codepen', path_defaults.get('codepen', False)),
            'toc': post.get('toc', path_defaults.get('toc', is_post)),
            'banner': post.get('banner', path_defaults.get('banner', False)),
            'sidebar': post.get('sidebar', True),
            'url': '',
            'file_path': file_path,
            'include_directives': include_directives
        }

    def collect_posts(self) -> None:
        """Collect all posts from section directories"""
        content_dir = self.root_dir / DIR_CONTENT
        sections = self.config.get('sections', DEFAULT_CONFIG['sections'])

        for collection_name in sections:
            collection_dir = content_dir / collection_name

            if not collection_dir.exists():
                continue

            for md_file in collection_dir.glob(f'*{EXT_MD}'):
                post_data = self.parse_markdown_file(md_file)

                if post_data is None:
                    continue

                post_slug = md_file.stem
                post_data['url'] = f"/{collection_name}/{post_slug}/"
                post_data['collection'] = collection_name

                self.posts[collection_name].append(post_data)

        # Sort posts by date (newest first)
        for collection in self.posts:
            self.posts[collection].sort(
                key=lambda x: x.get('date', ''),
                reverse=True
            )

    def collect_pages(self) -> None:
        """Collect all pages from sections directory"""
        sections_dir = self.theme_dir / DIR_SECTIONS

        if not sections_dir.exists():
            print(f'{CROSS} {MESSAGES["error"]["sections_not_found"].format(sections_dir)}')
            return

        for page_file in sections_dir.glob(f'*{EXT_MD}'):
            page_data = self.parse_markdown_file(page_file, is_post=False)

            if page_data is None:
                continue

            if page_file.stem == 'home':
                page_data['url'] = '/'
            else:
                page_data['url'] = f"/{page_file.stem}/"
                page_data['section'] = page_file.stem

            self.pages.append(page_data)

    def get_all_posts(self) -> List[Dict]:
        """Get all posts combined from all sections

        Returns:
            List of all posts sorted by date
        """
        all_posts = []
        for collection in self.posts.values():
            all_posts.extend(collection)

        all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        return all_posts

    def _process_include_directives(self, page_data: Dict) -> str:
        """Process include directives in page content

        Args:
            page_data: Page data dictionary

        Returns:
            Processed content with directives replaced
        """
        content = page_data['content']
        include_directives = page_data.get('include_directives', {})

        for placeholder, directive_type in include_directives.items():
            if directive_type == 'posts':
                rendered = self._render_posts_include()
            elif directive_type == 'category':
                rendered = self._render_category_include(page_data)
            elif directive_type == 'archive':
                rendered = self._render_archive_include()
            elif directive_type.startswith('example:'):
                example_id = directive_type.split(':')[1]
                rendered = f'<div class="example-viewer" data-example-id="{example_id}"></div>'
            else:
                continue

            content = content.replace(f'<p>{placeholder}</p>', rendered)
            content = content.replace(placeholder, rendered)

        return content

    def _render_posts_include(self) -> str:
        """Render the posts include template

        Returns:
            Rendered HTML string
        """
        posts_template = self.env.get_template(TEMPLATE_POSTS)
        return posts_template.render(
            site=self.config,
            posts=self.posts,
            all_posts=self.get_all_posts()[:self.config.get('post_limit', DEFAULT_POST_LIMIT)]
        )

    def _render_category_include(self, page_data: Dict) -> str:
        """Render the category include template

        Args:
            page_data: Page data dictionary

        Returns:
            Rendered HTML string
        """
        section_name = page_data.get('section')
        if not section_name:
            section_name = normalize_url_path(page_data['url']).split('/')[-1]

        page_data['section'] = section_name
        category_template = self.env.get_template(TEMPLATE_CATEGORY)
        return category_template.render(
            site=self.config,
            page=page_data,
            posts=self.posts
        )

    def _render_archive_include(self) -> str:
        """Render the archive include template

        Returns:
            Rendered HTML string
        """
        archive_template = self.env.get_template(TEMPLATE_ARCHIVE)
        return archive_template.render(
            site=self.config,
            posts=self.posts,
            all_posts=self.get_all_posts()
        )

    def _build_template_context(self, page_data: Dict) -> Dict:
        """Build template rendering context

        Args:
            page_data: Page data dictionary

        Returns:
            Context dictionary for template rendering
        """
        assets_config = self.config.get('assets', {})
        images_config = assets_config.get('images', {})
        logo_file = images_config.get('logo', 'codeCraft.ico')
        favicon_file = images_config.get('favicon', 'codeCraft.ico')

        return {
            'page': page_data,
            'site': self.config,
            'posts': self.posts,
            'pages': self.pages,
            'all_posts': self.get_all_posts()[:self.config.get('post_limit', DEFAULT_POST_LIMIT)],
            'use_base_tag': True,
            'base_url': self.base_url,
            'domain': f"https://{self.config['base']['url']}",
            'folder': "",
            'asset': "/assets",
            'css': f"/assets/{FILE_CODECRAFT_CSS}",
            'js': "/assets/codeCraft.js",
            'logo': f"/assets/{logo_file}",
            'favicon': f"/assets/{favicon_file}",
            'asset_urls': self.asset_urls,
            'now': datetime.now()
        }

    def render_page(self, page_data: Dict, output_path: str) -> None:
        """Render a single page using template

        Args:
            page_data: Page data dictionary
            output_path: Output path relative to build directory
        """
        template = self.env.get_template(TEMPLATE_MAIN)

        # Process include directives
        page_data['content'] = self._process_include_directives(page_data)

        # Build context and render
        context = self._build_template_context(page_data)
        html = template.render(**context)

        # Write output
        output_file = self.output_dir / output_path / 'index.html'
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

    def generate_feed(self) -> None:
        """Generate RSS feed"""
        template = self.env.get_template(FILE_FEED)

        context = {
            'site': self.config,
            'posts': self.get_all_posts()[:FEED_POST_LIMIT],
            'now': datetime.now()
        }

        feed_xml = template.render(**context)

        with open(self.output_dir / FILE_FEED, 'w', encoding='utf-8') as f:
            f.write(feed_xml)

    def generate_search_index(self) -> None:
        """Generate search.json for client-side search"""
        template = self.env.get_template(FILE_SEARCH)

        context = {
            'site': self.config,
            'posts': self.get_all_posts()
        }

        search_json = template.render(**context)

        with open(self.output_dir / FILE_SEARCH, 'w', encoding='utf-8') as f:
            f.write(search_json)

    def generate_css(self) -> None:
        """Generate CSS from template with font configurations"""
        assets_config = self.config.get('assets', {})
        fonts_config = assets_config.get('fonts', [])

        fonts = []
        for font in fonts_config:
            font_data = font.copy()
            weight_str = font.get('weight', 'Regular').lower()
            font_data['weight_num'] = FONT_WEIGHT_MAP.get(weight_str, '400')
            fonts.append(font_data)

        template = self.env.get_template(FILE_CSS_TEMPLATE)
        css_content = template.render(fonts=fonts)

        assets_dst = self.output_dir / DIR_ASSETS
        assets_dst.mkdir(parents=True, exist_ok=True)

        with open(assets_dst / FILE_CODECRAFT_CSS, 'w', encoding='utf-8') as f:
            f.write(css_content)

    def clean_output_dir(self) -> None:
        """Remove and recreate the output directory"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def copy_static_files(self) -> None:
        """Copy static assets to output directory"""
        # Copy theme assets (excluding CSS template)
        assets_src = self.theme_dir / DIR_ASSETS
        if assets_src.exists():
            assets_dst = self.output_dir / DIR_ASSETS
            assets_dst.mkdir(parents=True, exist_ok=True)

            for item in assets_src.iterdir():
                if item.name != FILE_CODECRAFT_CSS:
                    if item.is_file():
                        shutil.copy2(item, assets_dst / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, assets_dst / item.name, dirs_exist_ok=True)

        # Copy examples directory if it exists
        examples_src = self.root_dir / 'examples'
        if examples_src.exists():
            examples_dst = self.output_dir / 'examples'
            if examples_dst.exists():
                shutil.rmtree(examples_dst)
            shutil.copytree(examples_src, examples_dst)

        # Generate CSS from template
        self.generate_css()

    def build(self) -> None:
        """Build the entire site"""
        steps = MESSAGES['info']["build_steps"]
        step = -1

        def progress_step():
            nonlocal step
            step += 1
            if step < len(steps):
                padded = steps[step][:25].ljust(25)
                symbol = CHECK if step == len(steps) - 1 else ARROW
                progress.set_description_str(f"{symbol} {step+1}. {padded}")
                progress.update(1)

        with tqdm(total=len(steps), desc="Building site", unit="step", ncols=80,
                  bar_format="{l_bar}{bar} {n_fmt}/{total_fmt} [{elapsed}]") as progress:
            self.clean_output_dir()
            progress_step()

            self.collect_posts()
            self.collect_pages()
            progress_step()

            total_posts = sum(len(posts) for posts in self.posts.values())
            if total_posts > 0:
                for collection_name, posts in self.posts.items():
                    for post in posts:
                        output_path = normalize_url_path(post['url'])
                        self.render_page(post, output_path)
            progress_step()

            for page in self.pages:
                if page['url'] == '/':
                    output_path = ''
                else:
                    output_path = normalize_url_path(page['url'])
                self.render_page(page, output_path)
            progress_step()

            self.generate_feed()
            self.generate_search_index()
            progress_step()

            self.copy_static_files()
            progress_step()

        print(f"{CHECK} {MESSAGES['info']['build_complete']}")
        print(f"{INFO} {MESSAGES['info']['build_stats'].format(total_posts, len(self.pages))}")


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
        builder = SiteBuilder()
        builder.build()

    def serve(self, args: argparse.Namespace) -> None:
        """Start local development server

        Args:
            args: Command-line arguments
        """
        port = args.port
        site_dir = self.root_dir / DIR_BUILD

        if not site_dir.exists():
            print(MESSAGES['info']['building_site'])
            builder = SiteBuilder()
            builder.build()

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
                if args and len(args) > 0:
                    if isinstance(args[0], str) and 'Broken pipe' in str(args[0]):
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

                    # Rewrite HTML content
                    if path.endswith(EXT_HTML) and (b'<html' in content or b'<!DOCTYPE' in content):
                        content = re.sub(PATTERN_BASE_TAG, b'', content)
                        # Rewrite absolute URLs to relative for local development
                        content = content.replace(b'https://lucianofedericopereira.github.io/codecraft/', b'/')
                        content = content.replace(b'./assets/', b'/assets/')
                        content = content.replace(b'"./examples/', b'"/examples/')
                        content = content.replace(b"'examples/", b"'/examples/")
                        content = re.sub(
                            PATTERN_CONSOLE_SUPPRESS,
                            b'// Console suppression disabled for local development\n\n        ',
                            content,
                            flags=re.DOTALL
                        )

                    # Rewrite JavaScript content
                    elif path.endswith(EXT_JS):
                        content = content.replace(b'`examples/${', b'`/examples/${')

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
        watch_files = ['codecraft.py']

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
        if args.category not in DEFAULT_CONFIG['sections']:
            print(MESSAGES['error']['category'].format(', '.join(DEFAULT_CONFIG['sections'])))
            sys.exit(1)

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
    build_parser = subparsers.add_parser(
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
    watch_parser = subparsers.add_parser(
        'watch',
        help=MESSAGES["help"]["watch"]
    )

    # Clean command
    clean_parser = subparsers.add_parser(
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
        choices=DEFAULT_CONFIG['sections'],
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
