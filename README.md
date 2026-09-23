# Jordan's Document Library

A lightweight publishing system for turning text, Markdown, or HTML files into polished pages on GitHub Pages.

## Publish a document

```bash
python3 scripts/publish.py path/to/file.md --title "Document title"
```

Or publish text directly:

```bash
python3 scripts/publish.py --title "Document title" --text "Your text here"
```

The command creates a source file in `content/` and rebuilds `public/`. Commit and push the result; GitHub Actions deploys it automatically.

Useful options:

- `--slug custom-url` controls the final URL.
- `--description "Short summary"` controls the landing-page summary.
- `--date YYYY-MM-DD` controls publication date.
- `--draft` saves the source without listing or publishing it.
- `--no-build` saves the source without rebuilding.

To rebuild everything manually:

```bash
python3 scripts/build.py
```

## Project layout

- `content/` — canonical source documents and metadata
- `public/` — generated GitHub Pages site
- `scripts/` — dependency-free publishing and build automation
- `.github/workflows/deploy.yml` — automatic GitHub Pages deployment
- `AGENTS.md` — operating prompt for Codex and other coding agents

## Local preview

```bash
python3 -m http.server 8000 --directory public
```

Then visit <http://localhost:8000>.

