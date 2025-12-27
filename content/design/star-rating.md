---
title: "CSS: Star Rating"
date: 2023-04-10
comments: true
toc: true
---

Learn how to create a simple **star rating** look with only CSS and minimum HTML. We are going to use the data attribute and the before and after selectors. Check this step-by-step guide.

## Goal

Create a rating system using minimum markup.

## HTML

In orther to specify a rating we will use a `span` with a `data attribute`<a href="#footnote1" aria-label="Footnote 1"></a> and a value from `1` to `5`.

```html
<span class="star" data-rating="3"></span>
```

## CSS

The whole purpose of this snippets it´s to try to practice selectors and how can we use CSS to represent information from a data attribute.

### The Content

We are going to use the `★` character for our rating system. 

1. <span style="color:#ffc700">★</span><span style="color:#dddad7">★★★★</span>

2. <span style="color:#ffc700">★★</span><span style="color:#dddad7">★★★</span>

3. <span style="color:#ffc700">★★★</span><span style="color:#dddad7">★★</span>

4. <span style="color:#ffc700">★★★★</span><span style="color:#dddad7">★</span>

5. <span style="color:#ffc700">★★★★★</span>

### The Logic

If you think about it we are always to show <strong>five stars</strong>, some will be <span style="color:#ffc700">★</span>, and others <span style="color:#dddad7">★</span>. 

In orther to show both types we will use the `::before` (<span style="color:#ffc700">★</span>) and `::after` (<span style="color:#dddad7">★</span>) selectors.

Rating | before | after
:----: | :-----:|:----:
1      | 1      | 4
2      | 2      | 3
3      | 3      | 2
4      | 4      | 1
5      | 5      | 0

### The Code

```css
.star[data-rating="1"]::before,
.star[data-rating="4"]::after {
  content: "★";
}
.star[data-rating="2"]::before,
.star[data-rating="3"]::after {
  content: "★★";
}
.star[data-rating="3"]::before,
.star[data-rating="2"]::after {
  content: "★★★";
}
.star[data-rating="4"]::before,
.star[data-rating="1"]::after {
  content: "★★★★";
}
.star[data-rating="5"]::before,
.star[data-rating="0"]::after {
  content: "★★★★★";
}
```

## Interactive Example

Try changing the rating value:

[example:2]

### Footnotes

<footer>
  <p id="footnote1"><a href="https://developer.mozilla.org/en-US/docs/Learn/HTML/Howto/Use_data_attributes">Using data attributes</a> - MDN Web Docs.</p>
</footer>