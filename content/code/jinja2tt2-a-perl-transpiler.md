---
title: "Jinja2TT2: A Perl Transpiler"
date: 2026-01-28
comments: true
---

**Jinja2::TT2**: A Perl transpiler that converts Jinja2 templates to Template Toolkit 2 (TT2) syntax. Now available on CPAN.

## The Migration Problem

Template migration is one of those tasks that nobody wants to do. You inherit a Python project with hundreds of Jinja2 templates, but your infrastructure runs on Perl. Or you're consolidating two codebases and need everything in one templating language. The manual approach means opening each file, mentally parsing the Jinja2 syntax, and rewriting it in TT2. It's tedious, error-prone, and soul-crushing.

I faced this exact situation. Rather than spend days doing mechanical find-and-replace operations, I wrote a transpiler to automate the conversion.

## Why This Works

At first glance, converting between template languages seems like it would require understanding the host language deeply. Jinja2 is Python's templating engine; Template Toolkit is Perl's. Different ecosystems, different philosophies.

But look closer at the syntax:

```
Jinja2:  {{ user.name|upper }}
TT2:     [% user.name.upper %]
```

```
Jinja2:  {% for item in items %}
TT2:     [% FOREACH item IN items %]
```

```
Jinja2:  {% if logged_in %}Welcome{% endif %}
TT2:     [% IF logged_in %]Welcome[% END %]
```

The patterns are remarkably similar. Both languages use delimiters to separate template code from literal text. Both support variables, loops, conditionals, filters, includes, blocks, and macros. The concepts map almost one-to-one; only the spelling differs.

This isn't a coincidence. Template Toolkit predates Jinja2 by several years, and Jinja2's creator Armin Ronacher was clearly influenced by existing template engines. The result is two languages that share enough DNA to make mechanical translation feasible.

## The Approach

Jinja2::TT2 follows a classic three-stage compiler architecture:

**Tokenization** breaks the input into meaningful chunks. A Jinja2 template is a mix of literal text and template directives. The tokenizer identifies each `{{ }}` variable block, each `{% %}` statement, each `{# #}` comment, and the raw text between them.

**Parsing** builds structure from the token stream. A `{% for %}` token isn't just text—it opens a loop that must eventually close with `{% endfor %}`. The parser constructs an Abstract Syntax Tree that represents these relationships. Nested loops, conditionals inside loops, macros containing blocks—all become nodes in the tree.

**Emission** walks the tree and generates TT2 code. Each node type has a corresponding output format. A for-loop node becomes `[% FOREACH ... %]`. A variable with filters becomes a chain of method calls. The tree structure ensures that nesting is preserved correctly.

This design makes the transpiler easy to extend. Adding support for a new Jinja2 construct means adding a token pattern, a parser rule, and an emitter method. The stages are independent.

## Practical Usage

The command-line interface handles the common cases:

```bash
# Convert a single file
jinja2tt2 template.j2 -o template.tt

# Convert in place (creates .tt alongside .j2)
jinja2tt2 -i template.j2

# Pipe from stdin
echo '{{ name|upper }}' | jinja2tt2
```

For batch conversion, combine with find:

```bash
find templates/ -name "*.j2" -exec jinja2tt2 -i {} \;
```

The programmatic API gives you more control:

```perl
use Jinja2::TT2;

my $transpiler = Jinja2::TT2->new();
my $tt2_code = $transpiler->transpile($jinja2_source);
```

Debug mode (`--debug`) dumps the token stream and AST, useful for understanding how a particular template gets parsed or for diagnosing conversion issues.

## What Converts Cleanly

Most Jinja2 templates convert without any manual intervention:

**Variables** translate directly. Dot notation, bracket notation, and nested access all work. `{{ user.profile.avatar }}` becomes `[% user.profile.avatar %]`.

**Filters** map to TT2 vmethods or operators. `{{ name|upper|trim }}` becomes `[% name.upper.trim %]`. Filter chaining is preserved. Filters with arguments like `{{ items|join(", ") }}` work correctly.

**Control structures** convert with keyword changes. `if`/`elif`/`else`/`endif` becomes `IF`/`ELSIF`/`ELSE`/`END`. `for`/`endfor` becomes `FOREACH`/`END`. The loop variable mappings (`loop.index` → `loop.count`, `loop.index0` → `loop.index`) are handled automatically.

**Macros and blocks** have direct equivalents. `{% macro button(text) %}` becomes `[% MACRO button(text) BLOCK %]`. Block definitions convert cleanly.

**Comments and whitespace control** work as expected. `{# comment #}` becomes `[%# comment %]`. The whitespace-stripping markers `{{-` and `-}}` become `[%-` and `-%]`.

## Where Manual Review Helps

Some Jinja2 features don't have direct TT2 equivalents:

**Template inheritance** with `{% extends %}` and `{% block %}` works differently in TT2. Jinja2 uses child-extends-parent; TT2 uses `WRAPPER` for similar effects. The transpiler converts the block definitions, but the extends relationship needs manual restructuring.

**Autoescape** is a Jinja2 concept without a TT2 equivalent. If your templates rely on automatic HTML escaping, you'll need to add explicit `| html_entity` filters where needed.

**Complex expressions** embedded in templates may need review. Jinja2 allows Python expressions; TT2 has its own expression syntax. Simple comparisons and boolean logic convert fine, but anything that relies on Python-specific behavior should be checked.

**Custom filters** in your Jinja2 environment won't exist in TT2. The transpiler converts the filter syntax, but you'll need to implement matching vmethods or plugins on the TT2 side.

## Installation

From CPAN:

```bash
cpanm Jinja2::TT2
```

No external dependencies beyond core Perl 5.20+. The distribution includes a test suite covering the tokenizer, parser, and emitter.

## The Perl Choice

A template transpiler is fundamentally a text processing tool. It reads text, transforms it according to rules, and writes text. This is Perl's home territory.

The implementation uses only core modules. No CPAN dependencies to install, no version conflicts to resolve. Copy the script to a server from 2010 and it runs. That kind of portability matters for system tools.

The three-stage architecture also fits Perl's strengths. Regular expressions handle tokenization elegantly. Recursive descent parsing is natural in Perl. String interpolation makes the emitter readable.

Could this be written in Python? Sure. But then you'd need Python installed to convert away from Python templates. There's a certain elegance in using Perl to migrate toward Perl.

## Links

- **CPAN**: [Jinja2::TT2](https://metacpan.org/pod/Jinja2::TT2)
- **GitHub**: [lucianofedericopereira/jinja2tt2](https://github.com/lucianofedericopereira/jinja2tt2)

## License

LGPL-2.1
