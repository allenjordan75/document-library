# Document publishing agent

This repository is a personal document library hosted on GitHub Pages. Its primary workflow is: accept text or a file, turn it into a clean web document, publish it, update the landing page, and return the live URL.

## Default behavior

When the user provides text or a file to publish:

1. Read the material completely and preserve its meaning, facts, links, and intentional structure.
2. Lightly edit for web readability unless the user asks for a verbatim conversion. Add a clear title, short description, headings, lists, and links where they improve scanning. Never invent facts.
3. Run `python3 scripts/publish.py <file> --title "..." --description "..."`. For pasted text, use a temporary source file or the `--text` option. Use a short, stable, lowercase URL slug.
4. Inspect the generated page in `public/documents/<slug>/index.html` and confirm that `public/index.html` includes the new item.
5. Run `python3 scripts/build.py --check` before committing.
6. Commit only the files relevant to the publication and push to `main`.
7. Wait for the GitHub Pages deployment when possible, then return the exact public document URL and the landing-page URL.

## Presentation standards

- Prefer semantic HTML and accessible structure.
- Keep the existing visual system; do not hand-style individual pages unless the content requires a special layout.
- Preserve source attribution and external links.
- Copy referenced local assets into `public/assets/documents/<slug>/` and use relative URLs.
- Do not publish secrets, private identifiers, or obviously confidential material. Pause and flag them.
- Avoid changing an existing slug after publication because it breaks shared links.
- Treat `content/` as the source of truth and `public/` as generated output.

## Automation contract

Every non-draft item with valid front matter in `content/` must appear on the landing page. The build must remain deterministic and dependency-free. A push to `main` must be sufficient to deploy the contents of `public/` through GitHub Actions.

