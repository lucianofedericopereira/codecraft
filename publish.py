#!/usr/bin/env python3
"""
CodeCraft Static Site Generator - Publishing System
Handles site building and publishing for the CodeCraft static site generator
"""
from __future__ import annotations

import copy
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import frontmatter
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
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

# File names
FILE_CONFIG_PATH = 'themes/config.yaml'
FILE_CSS_TEMPLATE = 'codeCraft.css'
FILE_CODECRAFT_CSS = 'codeCraft.css'
FILE_FEED = 'feed.xml'
FILE_SEARCH = 'search.json'

# Markdown configuration
MD_EXTENSIONS = ['extra', 'toc']

# CSS classes
CSS_CLASS_HIGHLIGHT = 'highlight'
CSS_CLASS_HIGHLIGHTER_ROUGE = 'highlighter-rouge'
CSS_CLASS_LANGUAGE_PLAINTEXT = 'language-plaintext highlighter-rouge'
CSS_CLASS_LANGUAGE_MERMAID = 'language-mermaid'

# Regex patterns
PATTERN_MERMAID_BLOCK = r'```mermaid\n(.*?)```'
PATTERN_CODE_BLOCK = r'```(\w+)?\n(.*?)```'
PATTERN_EXAMPLE_SHORTCODE = r'\[example:(\d+)\]'

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

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    config = config if config else {}
            except Exception:
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
        except Exception:
            return None

        path_defaults = self._get_path_defaults(file_path)

        try:
            content_html, include_directives = process_markdown_content(post.content)
        except Exception:
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

            for md_file in collection_dir.glob('*.md'):
                post_data = self.parse_markdown_file(md_file)

                if post_data is None:
                    continue

                post_slug = md_file.stem
                post_data['url'] = f"{collection_name}/{post_slug}/"
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
            return

        for page_file in sections_dir.glob('*.md'):
            page_data = self.parse_markdown_file(page_file, is_post=False)

            if page_data is None:
                continue

            if page_file.stem == 'home':
                page_data['url'] = '/'
            else:
                page_data['url'] = f"{page_file.stem}/"
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
            'asset': "./assets",
            'css': "./assets/codeCraft.css",
            'js': "./assets/codeCraft.js",
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
        print("Building site...")

        self.clean_output_dir()
        print("✓ Cleaned output directory")

        self.collect_posts()
        self.collect_pages()
        print("✓ Collected posts and pages")

        total_posts = sum(len(posts) for posts in self.posts.values())
        if total_posts > 0:
            for collection_name, posts in self.posts.items():
                for post in posts:
                    output_path = normalize_url_path(post['url'])
                    self.render_page(post, output_path)
        print("✓ Rendered posts")

        for page in self.pages:
            if page['url'] == '/':
                output_path = ''
            else:
                output_path = normalize_url_path(page['url'])
            self.render_page(page, output_path)
        print("✓ Rendered pages")

        self.generate_feed()
        self.generate_search_index()
        print("✓ Generated feed & search")

        self.copy_static_files()
        print("✓ Copied static assets")

        print(f"\n✓ Build complete! Output in build/")
        print(f"   Posts: {total_posts}, Pages: {len(self.pages)}")


if __name__ == '__main__':
    builder = SiteBuilder()
    builder.build()
