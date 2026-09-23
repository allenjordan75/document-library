#!/usr/bin/env python3
"""Build a dependency-free static document library."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"


def parse_front_matter(text: str, source: Path) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise ValueError(f"{source}: missing YAML-style front matter")
    try:
        raw, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError(f"{source}: unclosed front matter") from exc
    data: dict[str, object] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"{source}: invalid front matter line: {line}")
        value = value.strip()
        if value.lower() in {"true", "false"}:
            data[key.strip()] = value.lower() == "true"
        else:
            data[key.strip()] = value.strip('"\'')
    for field in ("title", "description", "date", "slug"):
        if not data.get(field):
            raise ValueError(f"{source}: missing {field}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(data["slug"])):
        raise ValueError(f"{source}: slug must be lowercase words separated by hyphens")
    return data, body.strip()


def inline_markup(value: str) -> str:
    value = html.escape(value, quote=False)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', value)
    return value


def markdown_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    in_code = False
    code: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            out.append("<p>" + inline_markup(" ".join(x.strip() for x in paragraph)) + "</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    for line in lines:
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        item = re.match(r"^\s*[-*]\s+(.+)$", line)
        numbered = re.match(r"^\s*\d+\.\s+(.+)$", line)
        quote = re.match(r"^>\s?(.*)$", line)
        if heading:
            flush_paragraph(); close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline_markup(heading.group(2))}</h{level}>")
        elif item or numbered:
            flush_paragraph()
            desired = "ul" if item else "ol"
            if list_type != desired:
                close_list(); list_type = desired; out.append(f"<{desired}>")
            out.append("<li>" + inline_markup((item or numbered).group(1)) + "</li>")
        elif quote:
            flush_paragraph(); close_list()
            out.append("<blockquote>" + inline_markup(quote.group(1)) + "</blockquote>")
        elif not line.strip():
            flush_paragraph(); close_list()
        elif re.fullmatch(r"-{3,}", line.strip()):
            flush_paragraph(); close_list(); out.append("<hr>")
        else:
            paragraph.append(line)
    flush_paragraph(); close_list()
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    return "\n".join(out)


def shell(title: str, description: str, body: str, config: dict, *, path_prefix: str = "") -> str:
    site_title = html.escape(config["title"])
    accent = html.escape(config.get("accent", "#6d5dfc"))
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="theme-color" content="{accent}">
  <title>{html.escape(title)} · {site_title}</title>
  <link rel="stylesheet" href="{path_prefix}assets/style.css">
</head>
<body style="--accent:{accent}">
  <header class="site-header"><a class="brand" href="{path_prefix}">{site_title}</a></header>
  {body}
  <footer><span>Curated by {html.escape(config['author'])}</span><span>Hosted on GitHub Pages</span></footer>
</body>
</html>
'''


def build(check: bool = False) -> int:
    config = json.loads((ROOT / "site.json").read_text())
    documents = []
    errors = []
    for source in sorted(CONTENT.glob("*")):
        if source.suffix.lower() not in {".md", ".txt", ".html"}:
            continue
        try:
            metadata, raw_body = parse_front_matter(source.read_text(), source)
            if metadata.get("draft", False):
                continue
            body = raw_body if source.suffix.lower() == ".html" else markdown_to_html(raw_body)
            documents.append({**metadata, "body": body, "source": source})
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    slugs = [str(d["slug"]) for d in documents]
    if len(slugs) != len(set(slugs)):
        errors.append("duplicate slugs found")
    if errors:
        print("\n".join(f"error: {error}" for error in errors), file=sys.stderr)
        return 1

    documents.sort(key=lambda d: (str(d["date"]), str(d["title"])), reverse=True)
    if check:
        print(f"Validated {len(documents)} published document(s).")
        return 0

    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "assets").mkdir(parents=True)
    shutil.copy2(ROOT / "static" / "style.css", PUBLIC / "assets" / "style.css")
    static_assets = ROOT / "static" / "assets"
    if static_assets.exists():
        shutil.copytree(static_assets, PUBLIC / "assets", dirs_exist_ok=True)

    cards = []
    for doc in documents:
        slug = html.escape(str(doc["slug"]), quote=True)
        cards.append(f'''<article class="card" data-search="{html.escape(str(doc['title']) + ' ' + str(doc['description']), quote=True).lower()}">
  <a href="documents/{slug}/"><time>{html.escape(str(doc['date']))}</time><h2>{html.escape(str(doc['title']))}</h2><p>{html.escape(str(doc['description']))}</p><span class="read">Read document →</span></a>
</article>''')
        article = f'''<main class="article-shell">
  <a class="back" href="../../">← All documents</a>
  <article class="document"><header><time>{html.escape(str(doc['date']))}</time><h1>{html.escape(str(doc['title']))}</h1><p class="dek">{html.escape(str(doc['description']))}</p></header>{doc['body']}</article>
</main>'''
        target = PUBLIC / "documents" / str(doc["slug"])
        target.mkdir(parents=True)
        (target / "index.html").write_text(shell(str(doc["title"]), str(doc["description"]), article, config, path_prefix="../../"))

    landing = f'''<main>
  <section class="hero"><p class="eyebrow">A growing personal archive</p><h1>{html.escape(config['title'])}</h1><p>{html.escape(config['description'])}</p></section>
  <section class="library"><div class="library-head"><h2>Latest additions</h2><label><span class="sr-only">Search documents</span><input id="search" type="search" placeholder="Search the library…"></label></div><div id="documents" class="grid">{''.join(cards)}</div><p id="empty" hidden>No matching documents.</p></section>
</main>
<script>
const input=document.querySelector('#search'),cards=[...document.querySelectorAll('.card')],empty=document.querySelector('#empty');
input.addEventListener('input',()=>{{const q=input.value.trim().toLowerCase();let shown=0;cards.forEach(card=>{{const show=card.dataset.search.includes(q);card.hidden=!show;shown+=show}});empty.hidden=shown>0}});
</script>'''
    (PUBLIC / "index.html").write_text(shell(config["title"], config["description"], landing, config))
    (PUBLIC / ".nojekyll").write_text("")
    base = str(config.get("base_url", "")).rstrip("/")
    if base:
        urls = [base + "/"] + [f"{base}/documents/{d['slug']}/" for d in documents]
        (PUBLIC / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f"<url><loc>{html.escape(url)}</loc></url>" for url in urls) + "</urlset>\n")
    print(f"Built {len(documents)} document(s) in {PUBLIC.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate content without writing output")
    args = parser.parse_args()
    raise SystemExit(build(args.check))

