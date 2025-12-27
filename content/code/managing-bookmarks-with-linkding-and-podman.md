---
title: "Bash: Managing Bookmarks with Linkding and Podman"
date: 2025-11-09
comments: true
---

Managing personal bookmarks efficiently is essential for maintaining a clean and organized workflow, especially when working across multiple devices or projects. To achieve this, I use **Linkding**, a self-hosted bookmark manager, running inside a **Podman** container. This setup provides a lightweight, secure, and containerized way to manage and export my bookmarks.

## Why Self-Hosting Matters

Relying on third-party bookmark services or cloud sync platforms often means giving up control over your data. Many of these platforms are closed-source, can shut down without notice, or use your personal data for analytics or advertising. By **self-hosting** Linkding, I maintain complete ownership of my bookmarks, ensuring:

- **Privacy:** All data stays on my own server or machine — no tracking, no leaks.
- **Longevity:** I decide when to back up, migrate, or update my data.
- **Customization:** Full access to the backend and API lets me automate exports, tagging, or integration with other tools.
- **Offline access:** My bookmarks remain available even without internet connectivity.

Self-hosting isn’t just about independence; it’s about **digital resilience** — the ability to control and preserve your own information over time.

## Publishing My List

In addition to managing bookmarks privately, I like to **share curated resources publicly**. By exporting my bookmarks to a Markdown file using the Linkding API, I can push that file directly to **GitHub**, **GitLab**, or any static site generator.

This simple workflow turns a private bookmark collection into a **public knowledge resource** — a living, version-controlled list of tools, tutorials, and inspiration. Hosting the list on GitHub also makes it easy for others to discover new links, suggest additions via pull requests, or even fork the list for their own use.

Essentially, this setup transforms what used to be a personal browser feature into a **shareable knowledge hub** powered by open-source tools and automation.

## Why Podman?

[Podman](https://podman.io/) is a daemonless container engine designed to be a drop-in replacement for Docker. It offers several key advantages:

- **Rootless operation:** Podman can run containers without requiring root privileges, enhancing security.
- **Docker-compatible CLI:** It supports the same syntax and commands as Docker, making migration effortless.
- **Systemd integration:** Containers can easily be managed as system services.
- **OCI compliance:** Podman uses Open Container Initiative standards, ensuring portability and compatibility.

## Deploying Linkding with Podman

To deploy Linkding, I use the following `podman run` command:

```bash
podman run -d \
  --name linkding \
  -p 9090:9090 \
  -v linkding-data:/etc/linkding/data \
  ghcr.io/sissbruecker/linkding:latest
```
This command:
- Runs Linkding as a detached container (-d)
- Maps port **9090** on the host to **9090** inside the container
- Mounts a persistent Podman volume named linkding-data
- Uses the latest image from the GitHub Container Registry

### Creating the Superuser

After the container is up and running, I create an administrative account using:

```bash
podman exec -it linkding python manage.py createsuperuser
```

This command launches a shell inside the container and runs Django’s management command to create a superuser for the Linkding web interface.

## Managing API Access

To interact with Linkding’s REST API, an API key is required. Once generated from the web interface, I store it securely in my shell environment by adding the following line to my ~/.bashrc file:

```bash
export LINKDING_API_KEY="your_api_key"
```

After saving, I reload the configuration with:

```bash
source ~/.bashrc
```

This allows my export script to authenticate automatically when accessing the API.

## Exporting Bookmarks to Markdown

To keep my bookmarks portable and readable, I wrote a custom bash script that exports and categorizes bookmarks into a Markdown file (README.md). The script fetches data from Linkding’s API, sorts bookmarks by predefined categories, and formats them for easy sharing.

Here’s the complete script:


```bash
#!/bin/bash

# Ordered category names
ordered_categories=(
  "Design"
  "Code"
  "Linux - Free Software / Services"
  "Hardware"
  "Analog & Retro"
)

# Tags per category
declare -A category_tags=(
  ["Design"]="design"
  ["Code"]="code"
  ["Linux - Free Software / Services"]="linux"
  ["Hardware"]="hardware"
  ["Analog & Retro"]="retro analog"
)

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Message dictionary
declare -A MSG=(
  [missing_api_key]="ERROR: Environment variable LINKDING_API_KEY is not set."
  [set_api_key]="Hint: export LINKDING_API_KEY='your_api_key'"
  [missing_jq]="ERROR: 'jq' is not installed or not available in PATH."
  [install_jq]="Hint: Install it with: sudo apt install jq"
  [downloading]="Downloading bookmarks..."
  [done]="README.md successfully generated with sorted categories."
  [header_main]="# My Bookmarks\n\nMy personal bookmark list.\n"
  [footer]="_Last updated: %s • Total bookmarks: %s _\n"
  [exported]="Exported: %s bookmark(s)"
)

# Check for API key
if [ -z "$LINKDING_API_KEY" ]; then
  echo -e "${RED}${MSG[missing_api_key]}${NC}"
  echo -e "${YELLOW}${MSG[set_api_key]}${NC}"
  exit 1
fi

# Check for jq
if ! command -v jq &> /dev/null; then
  echo -e "${RED}${MSG[missing_jq]}${NC}"
  echo -e "${YELLOW}${MSG[install_jq]}${NC}"
  exit 1
fi

# Download bookmarks
echo -e "${GREEN}${MSG[downloading]}${NC}"
curl -s -H "Authorization: Token $LINKDING_API_KEY" http://localhost:9090/api/bookmarks/ > bookmarks.json

# Input and output files
INPUT="bookmarks.json"
OUTPUT="README.md"

# Write main header
echo -e "${MSG[header_main]}" > "$OUTPUT"

# Process each category in defined order
for category in "${ordered_categories[@]}"; do
  tags="${category_tags[$category]}"
  jq_expr=$(echo "$tags" | awk '{for(i=1;i<=NF;i++) printf "any(.tag_names[]; . == \"%s\") or ", $i}')
  jq_expr="${jq_expr% or }"
  matches=$(jq -r ".results[] | select($jq_expr) | \"[\(.title)](\(.url)) - \(.description)\"" "$INPUT" | sort)
  if [ -n "$matches" ]; then
    echo "## $category" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$matches" | sed 's/^/- /' >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
done

# Add summary
count=$(jq '.count' "$INPUT")
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
footer_text=---\\n$(printf "${MSG[footer]}" "$timestamp" "$count")
echo -e "$footer_text" >> "$OUTPUT"
formatted_count="${GREEN}${count}${NC}"
echo -e "$(printf "${MSG[exported]}" "$formatted_count")"
```

How It Works
- Checks for dependencies: Ensures that both the LINKDING_API_KEY and jq are available.
- Fetches bookmarks: Uses curl to query the Linkding API endpoint.
- Processes categories: Filters bookmarks by tags and writes them under corresponding headings.
- Generates Markdown: Creates a neatly formatted README.md file with categories, links, and descriptions.
- Adds metadata: Appends a summary including timestamp and total bookmark count.

Example Output

```markdown
# My Bookmarks

My personal bookmark list.

## Design

- [Luciano Pereira](https://github.com/lucianofedericopereira) - 


---
_Last updated: 2025-11-09 08:54:23 • Total bookmarks: 1 _
```


## Conclusion

By combining Podman and Linkding, I have a secure, self-hosted solution for managing bookmarks that integrates seamlessly with my shell environment. The export script adds an extra layer of utility, allowing me to maintain a readable, version-controlled list of bookmarks in Markdown format — perfect for sharing or archiving.


