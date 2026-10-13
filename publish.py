#!/usr/bin/env python3
"""
CodeCraft Static Site Generator - Publishing System
Headless site builder: used directly by CI and imported by codecraft.py
"""
from __future__ import annotations

import copy
import hashlib
import html
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import frontmatter
import minify_html
import yaml
from jinja2 import Environment, FileSystemLoader
from markdown import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

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
DIR_TEMPLATES = 'templates'
DIR_THEMES = 'themes'
DIR_TAGS = 'tags'

# File names
FILE_CONFIG_PATH = 'themes/config.yaml'
FILE_CSS_TEMPLATE = 'codeCraft.css'
FILE_CODECRAFT_CSS = 'codeCraft.css'
FILE_FEED = 'feed.xml'
FILE_SEARCH = 'search.json'
FILE_SITEMAP = 'sitemap.xml'
FILE_SITEMAP_HTML = 'sitemap.html'
FILE_SITEMAP_MD = 'sitemap.md'
FILE_LLMS = 'llms.txt'
FILE_LLMS_FULL = 'llms-full.txt'

# Markdown configuration
MD_EXTENSIONS = ['extra', 'toc']

# CSS classes
CSS_CLASS_HIGHLIGHT = 'highlight'
CSS_CLASS_HIGHLIGHTER_ROUGE = 'highlighter-rouge'
CSS_CLASS_LANGUAGE_PLAINTEXT = 'language-plaintext highlighter-rouge'
CSS_CLASS_LANGUAGE_MERMAID = 'language-mermaid'

# Regex patterns
PATTERN_TILDE_BLOCK = r'^~~~.*?^~~~[ \t]*$'
PATTERN_MERMAID_BLOCK = r'```mermaid\n(.*?)```'
PATTERN_CODE_BLOCK = r'```(\w+)?\n(.*?)```'
PATTERN_EXAMPLE_SHORTCODE = r'\[example:(\d+)\]'

# Include directive placeholders
PLACEHOLDER_POSTS = 'INCLUDE_POSTS_PLACEHOLDER'
PLACEHOLDER_CATEGORY = 'INCLUDE_CATEGORY_PLACEHOLDER'
PLACEHOLDER_ARCHIVE = 'INCLUDE_ARCHIVE_PLACEHOLDER'
PLACEHOLDER_TAG = 'INCLUDE_TAG_PLACEHOLDER'

# Template names
TEMPLATE_MAIN = 'codeCraft.html'
TEMPLATE_POSTS = 'posts.html'
TEMPLATE_CATEGORY = 'category.html'
TEMPLATE_ARCHIVE = 'archive.html'
TEMPLATE_TAG = 'tag.html'
TEMPLATE_TAGS = 'tags.html'
TEMPLATE_TAGS_MD = 'tags.md'

# Post limits
DEFAULT_POST_LIMIT = 10
FEED_POST_LIMIT = 10
DEFAULT_TAG_MIN_POSTS = 3

# Meta description length
DESCRIPTION_LENGTH = 160

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
    "tag_min_posts": DEFAULT_TAG_MIN_POSTS,
    "minify": True,
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
    "tags": {},
    "related": {
        "min": 2,
        "max": 5,
        "fallback": "section"
    },
    "rules": [],
    "scripts": {},
}

# Build messages
MESSAGES = {
    "config_not_found": "Config file not found: {} (using default configuration)",
    "invalid_yaml": "Invalid YAML format in {}: {} (using default configuration)",
    "reading_file": "Error reading {}: {}",
    "parsing_markdown": "Error parsing markdown in {}: {}",
    "unknown_tag": "Unknown tag in {}: {} (declare it under tags: in themes/config.yaml)",
    "missing_date": "No date in {}: using {} from {}",
    "sections_not_found": "Sections directory not found: {}",
    "building_site": "Building site...",
    "build_complete": "Build complete! Output in build/",
    "build_stats": "Posts: {}, Pages: {}",
}


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
    """Remove all whitespace from a string

    Args:
        value: String to process

    Returns:
        String with all whitespace removed
    """
    return re.sub(r'\s+', '', value)


def extract_description(content_html: str, limit: int = DESCRIPTION_LENGTH) -> str:
    """Plain text of the first real paragraph, cut at a word boundary

    Args:
        content_html: Rendered HTML content
        limit: Maximum length in characters

    Returns:
        Description text, or empty string if no paragraph is found
    """
    for paragraph in re.findall(r'<p>(.*?)</p>', content_html, re.DOTALL):
        text = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', paragraph)).split())
        if text and 'PLACEHOLDER' not in text:
            if len(text) <= limit:
                return text
            return text[:limit - 1].rsplit(' ', 1)[0].rstrip('.,;:—-') + '…'
    return ''


def tag_slug(name: Any) -> str:
    """URL slug of a tag name: lowercase, runs of other characters as one hyphen

    Args:
        name: Tag name as written in the config or a post

    Returns:
        Slug such as "sqlite" for "SQLite"
    """
    return re.sub(r'[^a-z0-9]+', '-', str(name).lower()).strip('-')


def normalize_url_path(path: str) -> str:
    """Normalize URL path by stripping leading/trailing slashes

    Args:
        path: URL path to normalize

    Returns:
        Normalized path without leading/trailing slashes
    """
    return path.strip('/')


# ============================================================================
# DATE FORMATTING FUNCTIONS
# ============================================================================

def _month_abbr(month_index: int, lang: str) -> str:
    """Get abbreviated month name for a zero-based month index"""
    return MONTHS.get(lang, MONTHS['en'])[month_index]


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
        return f"{_month_abbr(int(month) - 1, lang)} {year}"
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
        year, month, day = str(date_str).split("-")[:3]
        return f"{_month_abbr(int(month) - 1, lang)} {int(day):02d}"
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
    return str(date_str).split("-")[0]


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
        year, month, day = str(date_str).split("-")[:3]
        return f"{_month_abbr(int(month) - 1, lang)} {int(day):02d}, {year}"
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
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except Exception:
            return value
    if isinstance(value, (datetime, date)):
        return value.strftime(format)
    return value


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

    includes = [
        ('posts.html', PLACEHOLDER_POSTS, 'posts'),
        ('category.html', PLACEHOLDER_CATEGORY, 'category'),
        ('archive.html', PLACEHOLDER_ARCHIVE, 'archive'),
        ('tag.html', PLACEHOLDER_TAG, 'tag'),
    ]

    for template_name, placeholder, directive in includes:
        variants = (f'{{%- include {template_name} -%}}', f'{{% include {template_name} %}}')
        if any(variant in content for variant in variants):
            include_directives[placeholder] = directive
            for variant in variants:
                content = content.replace(variant, placeholder)

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


def protect_tilde_blocks(content: str) -> Tuple[str, List[str]]:
    """Set aside ~~~ fenced blocks so backtick passes don't reach inside them

    Args:
        content: Markdown content

    Returns:
        Tuple of (content with placeholders, list of tilde blocks)
    """
    tilde_blocks = []

    def save_tilde(match):
        tilde_blocks.append(match.group(0))
        return f'TILDE_PLACEHOLDER_{len(tilde_blocks)-1}'

    content = re.sub(PATTERN_TILDE_BLOCK, save_tilde, content, flags=re.DOTALL | re.MULTILINE)
    return content, tilde_blocks


def restore_tilde_blocks(content: str, tilde_blocks: List[str]) -> str:
    """Put ~~~ fenced blocks back for Markdown to render

    Args:
        content: Markdown content with placeholders
        tilde_blocks: List of tilde blocks

    Returns:
        Markdown content with tilde blocks restored
    """
    for i, block in enumerate(tilde_blocks):
        content = content.replace(f'TILDE_PLACEHOLDER_{i}', block)
    return content


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
            f'<pre><code class="{CSS_CLASS_LANGUAGE_MERMAID}">{html.escape(mermaid_content, quote=False)}</code></pre>'
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
        except Exception:
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

    # Set aside ~~~ fences
    content, tilde_blocks = protect_tilde_blocks(content)

    # Extract mermaid blocks
    content, mermaid_blocks = extract_mermaid_blocks(content)

    # Highlight code blocks
    content = highlight_code_blocks(content)

    # Restore ~~~ fences
    content = restore_tilde_blocks(content, tilde_blocks)

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
        self.posts = {name: [] for name in self.config['sections']}
        self.pages = []
        self.tags = {}

        # Content-hashed asset URLs, so a deploy never pairs new HTML with cached CSS or JS
        self.css_content = self.render_css()
        js_file = self.theme_dir / DIR_ASSETS / 'codeCraft.js'
        js_bytes = js_file.read_bytes() if js_file.exists() else b''
        self.css_url = f"./assets/{FILE_CODECRAFT_CSS}?v={hashlib.sha256(self.css_content.encode()).hexdigest()[:10]}"
        self.js_url = f"./assets/codeCraft.js?v={hashlib.sha256(js_bytes).hexdigest()[:10]}"

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
            self.warn(MESSAGES['config_not_found'].format(config_path))
        else:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                self.warn(MESSAGES['invalid_yaml'].format(config_path, e))
                config = {}
            except Exception as e:
                self.warn(MESSAGES['reading_file'].format(config_path, e))
                config = {}

        return apply_defaults(config, DEFAULT_CONFIG)

    def warn(self, message: str) -> None:
        """Report a non-fatal problem

        Args:
            message: Warning text
        """
        print(f"warning: {message}", file=sys.stderr)

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
            Dictionary with CDN URLs for mermaid
        """
        scripts = self.config.get('scripts', {})

        return {
            'mermaid': f"https://cdn.jsdelivr.net/npm/mermaid@{scripts.get('mermaid', '12.1.0')}/+esm"
        }

    def _get_path_defaults(self, file_path: Path) -> Dict[str, bool]:
        """Get default frontmatter values for a file path based on config rules

        Args:
            file_path: Path to the file

        Returns:
            Dictionary of default values
        """
        rules_config = self.config.get('rules', [])
        try:
            relative_path = file_path.relative_to(self.root_dir).as_posix()
        except ValueError:
            relative_path = file_path.as_posix()

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

            scope_path = scope_path.strip('/')
            if scope_path and (relative_path == scope_path or relative_path.startswith(scope_path + '/')):
                if 'features' in rule:
                    defaults.update(rule['features'])

        return defaults

    def file_date(self, file_path: Path) -> Tuple[date, str]:
        """Date of a file: its last commit, else its modification time (CI checkouts reset the latter)

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (date, where it came from)
        """
        try:
            log = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', str(file_path)],
                                 cwd=self.root_dir, capture_output=True, text=True, check=False)
            return date.fromisoformat(log.stdout.strip()), 'its last commit'
        except (OSError, ValueError):
            return date.fromtimestamp(file_path.stat().st_mtime), 'its modification time'

    def parse_markdown_file(self, file_path: Path, is_post: bool = True, source: Optional[str] = None) -> Optional[Dict]:
        """Parse a markdown file with frontmatter

        Args:
            file_path: Path to markdown file
            is_post: True for blog posts, False for pages
            source: Markdown text to parse instead of reading file_path

        Returns:
            Dictionary with post data or None on error
        """
        try:
            if source is not None:
                post = frontmatter.loads(source)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
        except Exception as e:
            self.warn(MESSAGES['reading_file'].format(file_path, e))
            return None

        path_defaults = self._get_path_defaults(file_path)
        post_date = post.get('date', '')
        if is_post and not post_date:
            post_date, origin = self.file_date(file_path)
            self.warn(MESSAGES['missing_date'].format(file_path, post_date, origin))
        tags = post.get('tags') or []
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

        try:
            content_html, include_directives = process_markdown_content(post.content)
        except Exception as e:
            self.warn(MESSAGES['parsing_markdown'].format(file_path, e))
            return None

        return {
            'content': content_html,
            'markdown': post.content,
            'title': post.get('title', ''),
            'description': post.get('description') or extract_description(content_html) or self.config['meta']['tagline'],
            'date': post_date,
            'updated': post.get('updated', ''),
            'comments': post.get('comments', path_defaults.get('comments', False)),
            'mermaid': post.get('mermaid', path_defaults.get('mermaid', False)),
            'codepen': post.get('codepen', path_defaults.get('codepen', False)),
            'toc': post.get('toc', path_defaults.get('toc', is_post)),
            'banner': post.get('banner', path_defaults.get('banner', False)),
            'sidebar': post.get('sidebar', True),
            'tags': list(dict.fromkeys(str(tag) for tag in tags)),
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

            for md_file in sorted(collection_dir.glob('*.md')):
                post_data = self.parse_markdown_file(md_file)

                if post_data is None:
                    continue

                post_slug = md_file.stem
                post_data['url'] = f"{collection_name}/{post_slug}/"
                post_data['md_url'] = f"{collection_name}/{post_slug}.md"
                post_data['collection'] = collection_name

                self.posts[collection_name].append(post_data)

        # Sort posts by date (newest first)
        for collection in self.posts:
            self.posts[collection].sort(
                key=lambda x: x.get('date', ''),
                reverse=True
            )

    def collect_tags(self) -> None:
        """Check every post's tags against the vocabulary and list the posts under each tag"""
        min_posts = self.config.get('tag_min_posts', DEFAULT_TAG_MIN_POSTS)
        vocabulary = self.config.get('tags') or {}
        if isinstance(vocabulary, list):
            vocabulary = {name: {'title': str(name)} for name in vocabulary}

        self.tags = {}
        for key, info in vocabulary.items():
            info = info or {}
            slug = tag_slug(key)
            self.tags[slug] = {
                'slug': slug,
                'title': info.get('title', str(key)),
                'description': info.get('description', ''),
                'url': f"{DIR_TAGS}/{slug}/",
                'md_url': f"{DIR_TAGS}/{slug}.md",
                'feed_url': f"{DIR_TAGS}/{slug}/{FILE_FEED}",
                'posts': [],
            }

        for post in self.get_all_posts():
            for name in post['tags']:
                if tag_slug(name) not in self.tags:
                    self.warn(MESSAGES['unknown_tag'].format(post['file_path'], name))
            post['tags'] = list(dict.fromkeys(tag_slug(name) for name in post['tags'] if tag_slug(name) in self.tags))
            post['tag_titles'] = [self.tags[slug]['title'] for slug in post['tags']]
            for slug in post['tags']:
                self.tags[slug]['posts'].append(post)

        for tag in self.tags.values():
            tag['has_page'] = len(tag['posts']) >= min_posts
            tag['lastmod'] = max((str(post.get('updated') or post['date']) for post in tag['posts']), default='')

    def collect_related(self) -> None:
        """Give every tagged post its related posts: most shared tags first, then its own section, newest first"""
        settings = self.config.get('related') or {}
        low, high = settings.get('min', 2), settings.get('max', 5)
        all_posts = self.get_all_posts()

        for post in all_posts:
            post['related'] = []
            if high <= 0 or not post['tags']:
                continue
            tags = set(post['tags'])
            shared = [(len(tags & set(other['tags'])), rank, other) for rank, other in enumerate(all_posts) if other is not post]
            picked = [other for count, _, other in sorted(shared, key=lambda item: (-item[0], item[1])) if count]
            if settings.get('fallback') == 'section':
                seen = {id(other) for other in picked}
                picked += [other for other in self.posts[post['collection']] if other is not post and id(other) not in seen]
            picked = picked[:high]
            if len(picked) >= low:
                post['related'] = picked

    @property
    def tag_pages(self) -> List[Dict]:
        """Tags with enough posts for a page of their own, in vocabulary order"""
        return [tag for tag in self.tags.values() if tag['has_page']]

    def collect_pages(self) -> None:
        """Collect all pages from sections directory"""
        sections_dir = self.theme_dir / DIR_SECTIONS

        if not sections_dir.exists():
            self.warn(MESSAGES['sections_not_found'].format(sections_dir))
            return

        page_files = {page_file.stem: (page_file, None) for page_file in sections_dir.glob('*.md')}
        for section in self.config['sections']:
            page_files.setdefault(section, (
                sections_dir / f"{section}.md",
                f"---\ntitle: {section.capitalize()}\n---\n{{% include category.html %}}\n",
            ))

        for stem in sorted(page_files):
            page_file, source = page_files[stem]
            page_data = self.parse_markdown_file(page_file, is_post=False, source=source)

            if page_data is None:
                continue

            if page_file.stem == 'home':
                page_data['url'] = '/'
                page_data['md_url'] = 'index.md'
            else:
                page_data['url'] = f"{page_file.stem}/"
                page_data['md_url'] = f"{page_file.stem}.md"
                page_data['section'] = page_file.stem

            self.pages.append(page_data)

    def annotate_pages(self) -> None:
        """Give each page the date of the newest post it lists, and drop section pages with no posts"""
        all_posts = self.get_all_posts()
        kept = []
        for page in self.pages:
            directives = page.get('include_directives', {}).values()
            if 'category' in directives:
                listed = self.posts.get(page.get('section'), [])
            elif 'posts' in directives or 'archive' in directives:
                listed = all_posts
            else:
                listed = []
            page['lastmod'] = max((str(post.get('updated') or post['date']) for post in listed), default='')
            if listed or 'category' not in directives:
                kept.append(page)
        self.pages = kept

    def get_all_posts(self) -> List[Dict]:
        """Get all posts combined from all sections

        Returns:
            List of all posts sorted by date
        """
        all_posts = [post for collection in self.posts.values() for post in collection]
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
            elif directive_type == 'tag' and page_data.get('tag'):
                rendered = self.env.get_template(TEMPLATE_TAG).render(tag=page_data['tag'], intro=page_data.get('tag_intro', ''))
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

    def page_url(self, page_data: Dict) -> str:
        """Absolute URL of a page or post

        Args:
            page_data: Page data dictionary

        Returns:
            Absolute URL string
        """
        return f"{self.base_url}/{page_data['url'].lstrip('/')}"

    def _structured_data(self, page_data: Dict, logo_file: str) -> Dict:
        """Build schema.org JSON-LD for a page or post

        Args:
            page_data: Page data dictionary
            logo_file: Logo file name inside assets

        Returns:
            JSON-LD dictionary
        """
        meta = self.config['meta']
        url = self.page_url(page_data)
        author = {'@type': 'Person', 'name': meta['author']}
        data = {
            '@context': 'https://schema.org',
            'url': url,
            'description': page_data['description'],
            'inLanguage': meta['locale'],
            'author': author,
        }

        if page_data.get('collection'):
            data.update({
                '@type': 'BlogPosting',
                'headline': page_data['title'],
                'mainEntityOfPage': url,
                'datePublished': str(page_data['date']),
                **({'dateModified': str(page_data['updated'])} if page_data.get('updated') else {}),
                'articleSection': page_data['collection'],
                **({'keywords': page_data['tag_titles']} if page_data.get('tag_titles') else {}),
                'publisher': {
                    '@type': 'Organization',
                    'name': meta['author'],
                    'logo': {'@type': 'ImageObject', 'url': f"{self.base_url}/{DIR_ASSETS}/{logo_file}"},
                },
            })
        elif page_data['url'] == '/':
            data.update({'@type': 'WebSite', 'name': meta['title']})
        else:
            data.update({
                '@type': 'WebPage',
                'name': page_data['title'],
                'isPartOf': {'@type': 'WebSite', 'name': meta['title'], 'url': f"{self.base_url}/"},
            })

        return data

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
            'tags': self.tags,
            'all_posts': self.get_all_posts()[:self.config.get('post_limit', DEFAULT_POST_LIMIT)],
            'use_base_tag': True,
            'base_url': self.base_url,
            'page_url': self.page_url(page_data),
            'structured_data': self._structured_data(page_data, logo_file),
            'domain': f"https://{self.config['base']['url']}",
            'folder': "",
            'asset': "./assets",
            'css': self.css_url,
            'js': self.js_url,
            'logo': f"./assets/{logo_file}",
            'favicon': f"./assets/{favicon_file}",
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
        if self.config.get('minify'):
            # minify_js stays off: codecraft serve matches an inline script comment
            html = minify_html.minify(html, minify_css=True, minify_js=False,
                                      keep_closing_tags=True, keep_html_and_head_opening_tags=True)

        # Write output
        output_file = self.output_dir / output_path / 'index.html'
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

    def generate_feed(self) -> None:
        """Generate the RSS feed, and one per tag page"""
        template = self.env.get_template(FILE_FEED)
        now = datetime.now()

        feed_xml = template.render(site=self.config, posts=self.get_all_posts()[:FEED_POST_LIMIT], tags=self.tags, now=now)
        with open(self.output_dir / FILE_FEED, 'w', encoding='utf-8') as f:
            f.write(feed_xml)

        for tag in self.tag_pages:
            feed_xml = template.render(site=self.config, posts=tag['posts'][:FEED_POST_LIMIT], tags=self.tags, tag=tag, now=now)
            output_file = self.output_dir / tag['feed_url']
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
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

    def render_page_markdown(self, page_data: Dict) -> str:
        """Render a section page as Markdown, expanding its includes with the .md templates

        Args:
            page_data: Page data dictionary

        Returns:
            Markdown document
        """
        body, include_directives = extract_include_directives(page_data['markdown'])
        all_posts = self.get_all_posts()
        context = {
            'site': self.config,
            'base_url': self.base_url,
            'page': page_data,
            'posts': self.posts,
            'tag': page_data.get('tag'),
            'intro': page_data.get('tag_intro', ''),
        }

        for placeholder, directive in include_directives.items():
            listed = all_posts[:self.config.get('post_limit', DEFAULT_POST_LIMIT)] if directive == 'posts' else all_posts
            rendered = self.env.get_template(f'{directive}.md').render(all_posts=listed, **context)
            body = body.replace(placeholder, rendered.strip())

        if page_data['url'] == '/':
            heading = f"# {self.config['meta']['title']}\n\n> {self.config['meta']['tagline']}"
        else:
            heading = f"# {page_data['title']}"
        return '\n\n'.join(filter(None, (heading, body.strip()))) + '\n'

    def sitemap_entries(self) -> List[Dict]:
        """Every page and every post, as the sitemap lists them

        Returns:
            List of entries with title, url, md_url, section and lastmod
        """
        entries = [
            {
                'title': page['title'],
                'url': page['url'].lstrip('/'),
                'md_url': page['md_url'],
                'section': '',
                'lastmod': page['lastmod'],
            }
            for page in self.pages
        ]
        if self.tag_pages:
            entries.append({
                'title': 'Tags',
                'url': f"{DIR_TAGS}/",
                'md_url': f"{DIR_TAGS}.md",
                'section': '',
                'lastmod': max(tag['lastmod'] for tag in self.tags.values()),
            })
            entries += [
                {
                    'title': tag['title'],
                    'url': tag['url'],
                    'md_url': tag['md_url'],
                    'section': '',
                    'lastmod': tag['lastmod'],
                }
                for tag in self.tag_pages
            ]
        entries += [
            {
                'title': post['title'],
                'url': post['url'],
                'md_url': post['md_url'],
                'section': post['collection'],
                'lastmod': str(post['updated'] or post['date']),
            }
            for post in self.get_all_posts()
        ]
        return entries

    def generated_page(self, title: str, description: str, url: str, md_url: str, content: str) -> Dict:
        """Page data for a page the build writes itself, with no Markdown source

        Args:
            title: Page title
            description: Meta description
            url: Page URL relative to the site root
            md_url: URL of its Markdown version
            content: Rendered HTML body

        Returns:
            Page data dictionary
        """
        return {
            'content': content,
            'markdown': '',
            'title': title,
            'description': description,
            'date': '',
            'updated': '',
            'comments': False,
            'mermaid': False,
            'codepen': False,
            'toc': False,
            'banner': False,
            'sidebar': False,
            'url': url,
            'md_url': md_url,
            'include_directives': {},
        }

    def render_sitemap_page(self, entries: List[Dict]) -> None:
        """Render sitemap/ as a page in the site layout"""
        page_data = self.generated_page(
            'Sitemap',
            f"Every page and post on {self.config['meta']['title']}, with its last modification date",
            'sitemap/',
            FILE_SITEMAP_MD,
            self.env.get_template(FILE_SITEMAP_HTML).render(entries=entries),
        )
        self.render_page(page_data, 'sitemap')

    def tag_page_data(self, tag: Dict) -> Optional[Dict]:
        """Page data for a tag's page, from themes/sections/tags/<tag>.md when it exists

        Args:
            tag: Tag dictionary from collect_tags

        Returns:
            Page data dictionary or None on error
        """
        page_file = self.theme_dir / DIR_SECTIONS / DIR_TAGS / f"{tag['slug']}.md"
        source = None
        if not page_file.exists():
            source = f"---\n{yaml.safe_dump({'title': tag['title']}, allow_unicode=True)}---\n{{% include {TEMPLATE_TAG} %}}\n"

        page_data = self.parse_markdown_file(page_file, is_post=False, source=source)
        if page_data is None:
            return None

        meta = frontmatter.loads(source) if source is not None else frontmatter.load(page_file)
        page_data.update({
            'title': page_data['title'] or tag['title'],
            'description': meta.get('description') or tag['description'] or extract_description(page_data['content'])
                           or f"Posts tagged {tag['title']} on {self.config['meta']['title']}",
            'url': tag['url'],
            'md_url': tag['md_url'],
            'feed_url': tag['feed_url'],
            'tag': tag,
            'tag_intro': tag['description'] if source is not None else '',
        })
        return page_data

    def render_tag_pages(self) -> None:
        """Render tags/, and a page with its Markdown version for every tag with enough posts"""
        if not self.tag_pages:
            return

        site_title = self.config['meta']['title']
        used = [tag for tag in self.tags.values() if tag['posts']]
        context = {'site': self.config, 'base_url': self.base_url}

        index = self.generated_page(
            'Tags',
            f"Every tag on {site_title}, with its number of posts",
            f"{DIR_TAGS}/",
            f"{DIR_TAGS}.md",
            self.env.get_template(TEMPLATE_TAGS).render(tags=used, **context),
        )
        self.render_page(index, DIR_TAGS)
        with open(self.output_dir / index['md_url'], 'w', encoding='utf-8') as f:
            f.write(self.env.get_template(TEMPLATE_TAGS_MD).render(tags=used, **context))

        for tag in self.tag_pages:
            page_data = self.tag_page_data(tag)
            if page_data is None:
                continue
            self.render_page(page_data, normalize_url_path(tag['url']))
            with open(self.output_dir / tag['md_url'], 'w', encoding='utf-8') as f:
                f.write(self.render_page_markdown(page_data))

    def generate_discovery_files(self) -> None:
        """Generate sitemap, llms.txt, llms-full.txt and Markdown versions of posts and pages"""
        context = {
            'site': self.config,
            'base_url': self.base_url,
            'posts': self.posts,
            'all_posts': self.get_all_posts(),
            'pages': self.pages,
            'tag_pages': self.tag_pages,
        }
        context['entries'] = self.sitemap_entries()
        context['newest'] = max((entry['lastmod'] for entry in context['entries']), default='')

        for name in (FILE_SITEMAP, FILE_SITEMAP_MD, FILE_LLMS, FILE_LLMS_FULL):
            with open(self.output_dir / name, 'w', encoding='utf-8') as f:
                f.write(self.env.get_template(name).render(**context))

        for post in context['all_posts']:
            shutil.copy2(post['file_path'], self.output_dir / post['md_url'])

        for page in self.pages:
            with open(self.output_dir / page['md_url'], 'w', encoding='utf-8') as f:
                f.write(self.render_page_markdown(page))

        self.render_sitemap_page(context['entries'])

    def render_css(self) -> str:
        """Render the CSS template with the configured fonts and sections

        Returns:
            CSS text
        """
        assets_config = self.config.get('assets', {})
        fonts_config = assets_config.get('fonts', [])

        fonts = []
        for font in fonts_config:
            font_data = font.copy()
            weight_str = font.get('weight', 'Regular').lower()
            font_data['weight_num'] = FONT_WEIGHT_MAP.get(weight_str, '400')
            fonts.append(font_data)

        template = self.env.get_template(FILE_CSS_TEMPLATE)
        return template.render(fonts=fonts, sections=self.config['sections'])

    def generate_css(self) -> None:
        """Write the rendered CSS into the build"""
        assets_dst = self.output_dir / DIR_ASSETS
        assets_dst.mkdir(parents=True, exist_ok=True)

        with open(assets_dst / FILE_CODECRAFT_CSS, 'w', encoding='utf-8') as f:
            f.write(self.css_content)

    def clean_output_dir(self) -> None:
        """Remove and recreate the output directory"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create .nojekyll file to disable GitHub Pages Jekyll processing
        (self.output_dir / '.nojekyll').touch()

    def copy_static_files(self) -> None:
        """Copy static assets to output directory"""
        # Copy theme assets (excluding CSS template)
        assets_src = self.theme_dir / DIR_ASSETS
        if assets_src.exists():
            assets_dst = self.output_dir / DIR_ASSETS
            assets_dst.mkdir(parents=True, exist_ok=True)

            for item in assets_src.iterdir():
                if item.name == FILE_CODECRAFT_CSS:
                    continue
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

    def render_posts(self) -> None:
        """Render every collected post"""
        for posts in self.posts.values():
            for post in posts:
                self.render_page(post, normalize_url_path(post['url']))

    def render_pages(self) -> None:
        """Render every collected page"""
        for page in self.pages:
            self.render_page(page, normalize_url_path(page['url']))

    @property
    def post_count(self) -> int:
        """Total number of collected posts"""
        return sum(len(posts) for posts in self.posts.values())

    def steps(self) -> List[Tuple[str, Callable[[], None]]]:
        """Ordered build steps as (label, action) pairs

        Returns:
            List of build steps
        """
        return [
            ("Cleaning output directory", self.clean_output_dir),
            ("Collecting posts and pages", lambda: (self.collect_posts(), self.collect_tags(), self.collect_related(), self.collect_pages(), self.annotate_pages())),
            ("Rendering posts", self.render_posts),
            ("Rendering pages", lambda: (self.render_pages(), self.render_tag_pages())),
            ("Generating feed & search", lambda: (self.generate_feed(), self.generate_search_index())),
            ("Writing discovery files", self.generate_discovery_files),
            ("Copying static assets", self.copy_static_files),
        ]

    def build(self) -> None:
        """Build the entire site"""
        print(MESSAGES['building_site'])

        for label, action in self.steps():
            print(f"→ {label}")
            action()

        print(f"\n✓ {MESSAGES['build_complete']}")
        print(f"   {MESSAGES['build_stats'].format(self.post_count, len(self.pages))}")


if __name__ == '__main__':
    builder = SiteBuilder()
    builder.build()
