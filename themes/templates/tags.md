{% autoescape false %}# Tags

{% for tag in tags %}- {% if tag.has_page %}[{{ tag.title }}]({{ base_url }}/{{ tag.md_url }}){% else %}{{ tag.title }}{% endif %} · {{ tag.posts|length }}
{% endfor %}{% endautoescape %}
