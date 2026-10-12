{% autoescape false %}# Sitemap

{{ entries|length }} pages and posts. The same list is published as [XML]({{ base_url }}/sitemap.xml) for search engines and as an [HTML page]({{ base_url }}/sitemap/).

| Page | Section | Last modified |
| --- | --- | --- |
{% for entry in entries %}| [{{ entry.title }}]({{ base_url }}/{{ entry.md_url }}) | {{ entry.section }} | {{ entry.lastmod|date_full }} |
{% endfor %}{% endautoescape %}
