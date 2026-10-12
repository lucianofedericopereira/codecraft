{% autoescape false %}{% for item in all_posts %}
### [{{ item.title }}]({{ base_url }}/{{ item.md_url }})

{{ item.date|date_full }} · {{ item.collection }}

{{ item.description }}
{% endfor %}{% endautoescape %}
