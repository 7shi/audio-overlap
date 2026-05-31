# url2md

URL analysis and classification tool - Generate Markdown reports from URLs through AI-powered content analysis, summarization, and classification.

For output examples, see the [Wiki](https://github.com/7shi/url2md/wiki).

## Features

- **URL Fetching**: Download and cache web content with support for dynamic rendering via Playwright
- **AI Summarization**: Generate structured summaries using Gemini API with thinking process visualization
- **Content Classification**: Automatically classify and tag content by topic with AI reasoning insights
- **AI Thinking Process**: Real-time display of Gemini 2.5's internal reasoning for complex analysis tasks
- **Markdown Reports**: Generate comprehensive reports in Markdown format
- **Pipeline Processing**: Complete workflow from URLs to final report

## Requirements

- Python 3.10 or higher
- Internet connection for AI operations
- **GEMINI_API_KEY**: Google Gemini API key for AI summarization and classification operations

```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Note**: API key not required for `--extract-tags` or `--show-prompt` operations.

### Optional Dependencies
- Playwright for dynamic rendering support

## Installation

### As a tool (recommended)

```bash
# Install as a tool
uv tool install https://github.com/7shi/url2md.git

# Add ~/.local/bin to PATH if not already added
export PATH="$HOME/.local/bin:$PATH"

# Optional for dynamic rendering
playwright install
```

### From source

```bash
# Source installation with uv
git clone https://github.com/7shi/url2md.git
cd url2md
uv sync

# Optional for dynamic rendering
uv run playwright install
```

**Note**: When using source installation, prefix all commands with `uv run` (e.g., `uv run url2md init`).

## Workflow Overview

url2md follows a standard workflow to analyze URLs and generate reports:

1. **Initialize** → Create cache directory structure (one-time setup)
2. **Fetch** → Download and cache web content
3. **Summarize** → Generate AI-powered summaries  
4. **Classify** → Extract tags and categorize by themes
5. **Report** → Create comprehensive Markdown reports

### Quick Examples

Here are the standard workflow commands (same as shown by `url2md`):

```bash
# Initialize cache directory (required first step, creates `url2md-cache/`)
url2md init

# Step-by-step workflow
url2md fetch -u urls.txt --playwright
url2md summarize -u urls.txt
url2md classify -u urls.txt -o class.json
url2md report -u urls.txt -c class.json -o report.md

# Complete workflow in one command (fetch → summarize → classify → report)
url2md workflow -u urls.txt --playwright -c class.json -o report.md

# With Japanese language output for AI operations
url2md summarize -u urls.txt -l Japanese
url2md classify -u urls.txt -o class.json -l Japanese
url2md workflow -u urls.txt -c class.json -o report.md -l Japanese
```

For more command details, use `url2md <command> --help`.

## Global Options

These options must be specified before the subcommand:

```bash
# Cache directory (applies to all commands)
url2md --cache-dir /custom/cache <command> [options]

# Examples
url2md --cache-dir /tmp/cache fetch -u urls.txt
```

### Cache Directory Detection

url2md automatically detects cache directories by looking for `cache.tsv` files in parent directories, similar to how git finds `.git` directories:

1. **Priority**: If `url2md-cache/cache.tsv` exists in the current directory, it uses `url2md-cache` (relative path)
2. **Parent Search**: Otherwise, searches for any directory containing `cache.tsv` in current and parent directories
3. **Initialization Required**: If no `cache.tsv` is found, you must run `url2md init` to create a cache

This allows you to run url2md commands from any subdirectory within your project, and it will automatically find and use the appropriate cache directory.

```bash
# Running from project root
project/
├── url2md-cache/
│   └── cache.tsv    # Uses this cache
└── subdir/
    └── (working here) # Automatically finds ../url2md-cache

# Custom cache directory names are supported
project/
├── my_url_cache/
│   └── cache.tsv    # Uses this cache (directory name is flexible)
└── src/
```

## Command Reference

### `init` - Initialize cache directory

**Required first step**: Creates cache directory structure with `cache.tsv` file.

```bash
# Initialize cache in current directory (creates ./url2md-cache/)
url2md init

# Initialize with custom directory name
url2md init my_cache

# Initialize with custom path (global option)
url2md --cache-dir /path/to/cache init

# Note: Cannot specify both --cache-dir and directory argument
# url2md --cache-dir foo init bar  # Error: conflicting arguments
```

### `fetch` - Download and cache URLs

**Default behavior**: Skip previously failed URLs and show count. Use `--retry` to retry errors.

```bash
# Basic usage (skips errors by default)
url2md fetch "https://example.com"

# Multiple URLs
url2md fetch "https://example.com" "https://another-site.com"

# From file
url2md fetch -u urls.txt

# Retry failed URLs explicitly
url2md fetch -r -u urls.txt

# With dynamic rendering
url2md fetch --playwright -u urls.txt

# Custom cache directory (global option)
url2md --cache-dir /path/to/cache fetch -u urls.txt

# Force re-fetch all URLs
url2md fetch --force "https://example.com"
```

### `summarize` - Generate AI summaries

```bash
# Summarize all cached content
url2md summarize

# Summarize specific URLs
url2md summarize "https://example.com"

# Summarize URLs from file
url2md summarize -u urls.txt

# Show summary file paths and contents for specified URLs
url2md summarize --show-summary "https://example.com"
url2md summarize --show-summary -u urls.txt

# Limit number of summaries
url2md summarize --limit 10

# Force re-summarize
url2md summarize --force

# Generate summaries in Japanese
url2md summarize -u urls.txt -l Japanese

# Generate summaries in Chinese
url2md summarize -u urls.txt -l Chinese
```

### `classify` - Classify content by topic

```bash
# Extract and show tag statistics for all cached content
url2md classify --extract-tags

# Classify specific URLs with LLM (output file required)
url2md classify "https://example.com" -o classification.json

# Classify URLs from file (output file required)
url2md classify -u urls.txt -o classification.json

# Show classification prompt only (no LLM call)
url2md classify --show-prompt

# Classify with Japanese theme names and descriptions
url2md classify -u urls.txt -o classification.json -l Japanese

# Show classification and translation prompts in specified language
url2md classify --show-prompt -l Japanese
```

### `report` - Generate Markdown reports

```bash
# Generate report from classification
url2md report -c classification.json

# Save to file
url2md report -c classification.json -o report.md

# Specify URL subset
url2md report -c classification.json -u urls.txt

# Include specific URLs in report
url2md report "https://example.com" -c classification.json -o report.md

# Adjust theme weights for classification
url2md report -c classification.json -t "Programming:1.5" -t "Education:0.8"

# Create tag subsections within themes (add $ suffix)
url2md report -c classification.json -t "Programming:1.5$" -t "Education:0.8"

# Load theme weights from file
url2md report -c classification.json -T theme-weights.txt

# Mix file and command-line theme weights
url2md report -c classification.json -T theme-weights.txt -t "Emergency:2.0$"
```

**Translation Support:**
- Reports automatically use translated headers and UI terms from translation cache when available
- Translation terms include: "Summary", "Themes", "Total URLs", "Classified", "Unclassified", "URLs", "Other"
- If classification was generated with language option (`-l`), translations are cached and used in reports
- Cache-first approach: subsequent runs with same language use cached translations for instant performance
- Falls back to English terms when translations are not available in cache

### `workflow` - Complete workflow

```bash
# Run complete workflow (classification file required)
url2md workflow -u urls.txt -c classification.json -o final-report.md

# With custom settings
url2md --cache-dir url2md-cache workflow \
    -u urls.txt \
    --playwright \
    -c classification.json \
    -o report.md

# With theme weight adjustments
url2md workflow \
    -u urls.txt \
    -c classification.json \
    -t "Programming:1.5" \
    -t "Education:0.8" \
    -o report.md

# With tag subsections and theme weight file
url2md workflow \
    -u urls.txt \
    -c classification.json \
    -T theme-weights.txt \
    -t "Emergency:2.0$" \
    -o report.md

# With Japanese language output for AI operations
url2md workflow \
    -u urls.txt \
    -c classification.json \
    -o report.md \
    -l Japanese
```

## Language Support

url2md supports multi-language output for AI operations (summarize and classify commands):

```bash
# Supported languages (examples)
url2md summarize -u urls.txt -l Japanese
url2md summarize -u urls.txt -l Chinese
url2md summarize -u urls.txt -l French
url2md summarize -u urls.txt -l Spanish

# Apply to classification as well
url2md classify -u urls.txt -o class.json -l Japanese

# Use in complete workflow
url2md workflow -u urls.txt -c class.json -o report.md -l Japanese
```

**Language Support Features:**
- **Summarize**: Generates titles, summaries, and tags in specified language
- **Classify**: Creates theme names and descriptions in specified language, automatically generates and caches report term translations
- **Report**: Uses translated headers and UI terms from translation cache when available
- **Workflow**: Applies language setting to both summarize and classify steps, generating fully translated reports
- **Translation Caching**: Translations are cached in `terms.tsv` to avoid repeated LLM calls for same language
- **Prompts**: Use `--show-prompt -l LANGUAGE` to see localized classification and translation prompts

**Notes:**
- Language setting only affects AI-generated content (summaries, themes)
- Original URLs and technical metadata remain unchanged
- Any language name can be specified (e.g., "Japanese", "中文", "Français")
- Translation cache persists across sessions for improved performance


## File Formats

### URL List File
```
# Comments start with #
https://example.com
https://another-site.com
# Empty lines are ignored

https://third-site.com
```

### Cache Structure
```
url2md-cache/
├── cache.tsv              # Metadata index
├── terms.tsv              # Translation cache (English/Language/Translation)
├── content/               # Downloaded content
│   ├── abc123.html
│   ├── def456.pdf
│   └── ...
└── summary/               # AI-generated summaries
    ├── abc123.json
    ├── def456.json
    └── ...
```

### Summary JSON Format
```json
{
  "title": ["HTML Title", "AI-generated Title"],
  "summary_one_line": "Brief one-line summary",
  "summary_detailed": "Detailed summary with key points...",
  "tags": ["programming", "python", "tutorial"],
  "is_valid_content": true
}
```

### Classification JSON Format
```json
{
  "themes": [
    {
      "theme_name": "Programming",
      "theme_description": "Programming and software development content",
      "tags": ["programming", "coding", "development"]
    },
    {
      "theme_name": "Education", 
      "theme_description": "Educational and learning content",
      "tags": ["tutorial", "learning", "course"]
    }
  ],
  "classification_summary": {
    "total_tags_processed": 35,
    "total_themes_created": 2,
    "classification_approach": "Grouped related tags into thematic categories"
  },
  "language": "Japanese"
}
```

### Theme Weight File Format
```
# Comments start with #
Programming:1.5
Education:0.8

# Add $ suffix to create tag subsections
Research:1.2$
Technology:0.9$

# Empty lines are ignored
Business:1.0
```

## Testing

```bash
# Quick test commands
uv sync --dev       # Install development dependencies
uv run pytest       # Run all tests
```

For comprehensive testing documentation including test coverage, categories, development workflows, and contributing guidelines, see **[tests/README.md](tests/README.md)**.

## Documentation

- **[README.md](README.md)** - User documentation and command reference
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and workflow
- **[NOTES.md](NOTES.md)** - Development philosophy and key lessons
- **[url2md/README.md](url2md/README.md)** - Package architecture and module documentation
- **[tests/README.md](tests/README.md)** - Test suite documentation and coverage overview
- **[docs/README.md](docs/README.md)** - Specialized documentation for architecture, testing, troubleshooting, and detailed development guidance
