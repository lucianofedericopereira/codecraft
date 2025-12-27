# Examples Directory

This directory contains interactive code examples that can be embedded in blog posts.

## How to Use

### 1. Create an Example File

Create an HTML file in this directory (e.g., `1.html`, `2.html`, etc.) with the following structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Example Title</title>
  <style id="example-css">
    /* Your CSS here */
  </style>
</head>
<body>
  <!-- Your HTML here -->

  <script id="example-js">
    // Your JavaScript here
  </script>
</body>
</html>
```

**Important:**
- Use `id="example-css"` for the style tag
- Use `id="example-js"` for the script tag
- These IDs are required for the parser to extract the code

### 2. Reference in Your Blog Post

In your markdown file, simply write:

```markdown
[example:1]
```

This will render an interactive viewer with:
- **Left side:** Three tabs (HTML, CSS, JavaScript) showing the source code
- **Right side:** Live preview of the example running in an iframe

### 3. Build and Preview

```bash
python codecraft.py build
python codecraft.py serve
```

Then navigate to your post to see the interactive example viewer.

## Example Structure

See `1.html` for a working example of a gradient button.

## Features

- **Split-pane layout:** Code on the left, preview on the right
- **Tabbed interface:** Switch between HTML, CSS, and JavaScript
- **Live preview:** Changes are immediately visible
- **Responsive:** Adapts to mobile devices
- **Syntax highlighting:** Code is displayed with proper formatting
- **Isolated execution:** Each example runs in its own iframe

## Tips

- Keep examples focused and simple
- Test your examples by opening the HTML file directly in a browser first
- Use meaningful titles in the `<title>` tag
- Examples are copied to `/build/examples/` during the build process
