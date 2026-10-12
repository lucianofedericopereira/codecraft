{% autoescape false %}{% set ns = namespace(current_year='') %}{% for item in all_posts %}{% set year = item.date|year %}{% if year != ns.current_year %}
## {{ year }}

{% set ns.current_year = year %}{% endif %}- {{ item.date|date_archive }} · [{{ item.title }}]({{ base_url }}/{{ item.md_url }}) · {{ item.collection }}
{% endfor %}{% endautoescape %}
