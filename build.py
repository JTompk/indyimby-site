#!/usr/bin/env python3
"""
IndyIMBY static site builder.

Content model:
  content/posts/YYYY-MM-DD-slug.md   -> docs/digest/YYYY-MM-DD-slug/index.html
  content/pages/slug.md              -> docs/slug/index.html

Front matter (simple key: value block between --- lines):
  title:   Post title
  date:    2026-07-06
  summary: One-sentence deck shown on the homepage.

Post slugs keep the full filename (date included) so weekly digests named
"YYYY-MM-DD-this-week.md" never collide at the same URL.

REDIRECTS below regenerates stubs for old URLs on every build — necessary
because docs/ is wiped each build, so hand-placed files there don't survive.

Build:  python build.py
Output: docs/  (served by GitHub Pages)
"""

import html
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
DOCS = ROOT / "docs"

SITE = {
    "name": "IndyIMBY",
    "url": "https://indyimby.com",          # change if using a different domain
    # base: subpath the site is served from. "/indyimby-site" while on
    # jtompk.github.io/indyimby-site; change to "" when indyimby.com is live.
    "base": "",
    "map_url": "https://map.indyimby.com",  # the entitlement tracker
    "tagline": "Yes. In my back yard. In Indy.",
    "description": "Tracking every development filing in Indianapolis — and helping neighbors say yes.",
    # default og_description; per-page ctx overrides (posts pass their summary)
    "og_description": "Tracking every development filing in Indianapolis — and helping neighbors say yes.",
    "og_url": "https://indyimby.com/",
}

# Old URL path -> new URL path. Stubs are regenerated every build.
# Add entries here whenever a published URL changes.
REDIRECTS = {
    "digest/welcome-back": "digest/2026-07-06-welcome-back",
    "digest/this-week": "digest/2026-07-13-this-week",
}

MD = markdown.Markdown(extensions=["tables", "fenced_code", "smarty"])


def parse(path: Path):
    raw = path.read_text(encoding="utf-8")
    meta = {}
    body = raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        body = raw[m.end():]
    MD.reset()
    meta["html"] = MD.convert(body)
    meta.setdefault("title", path.stem)
    return meta


def render(template: str, **ctx) -> str:
    out = (TEMPLATES / template).read_text(encoding="utf-8")
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    for k, v in ctx.items():
        out = out.replace("{{" + k + "}}", str(v))
    page = base.replace("{{content}}", out)
    for k, v in {**SITE, **ctx}.items():
        page = page.replace("{{" + k + "}}", str(v))
    # prefix internal absolute links with the base subpath (no-op when base="")
    page = page.replace('href="/', 'href="' + SITE["base"] + '/')
    page = page.replace('src="/', 'src="' + SITE["base"] + '/')
    return page


def write(relpath: str, html_text: str):
    out = DOCS / relpath
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")
    print(f"  built {relpath}")


def redirect_stub(target_path: str) -> str:
    url = f"{SITE['url']}/{target_path}/"
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<title>Redirecting — {SITE["name"]}</title>\n'
        f'<meta http-equiv="refresh" content="0;url={url}">\n'
        f'<link rel="canonical" href="{url}">\n</head>\n<body>\n'
        f'<p>This page has moved. If you are not redirected automatically, '
        f'<a href="{url}">continue here</a>.</p>\n</body>\n</html>\n'
    )


def main():
    # fresh docs/, preserving CNAME if present
    cname = (DOCS / "CNAME").read_text(encoding="utf-8") if (DOCS / "CNAME").exists() else None
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    if cname:
        (DOCS / "CNAME").write_text(cname, encoding="utf-8")
    shutil.copytree(STATIC, DOCS / "static")

    # posts — slug keeps the full dated filename so weekly digests never collide
    posts = []
    for p in sorted((CONTENT / "posts").glob("*.md"), reverse=True):
        meta = parse(p)
        slug = p.stem
        meta["slug"] = slug
        meta.setdefault("date", p.stem[:10])
        posts.append(meta)
        write(f"digest/{slug}/index.html",
              render("post.html", title=meta["title"], date=meta["date"],
                     body=meta["html"],
                     og_description=html.escape(meta.get("summary", SITE["og_description"])),
                     og_url=f'{SITE["url"]}/digest/{slug}/',
                     page_title=f'{meta["title"]} — {SITE["name"]}'))

    # pages
    for p in sorted((CONTENT / "pages").glob("*.md")):
        meta = parse(p)
        write(f"{p.stem}/index.html",
              render("page.html", title=meta["title"], body=meta["html"],
                     og_url=f'{SITE["url"]}/{p.stem}/',
                     page_title=f'{meta["title"]} — {SITE["name"]}'))

    # redirect stubs for moved URLs (regenerated every build; docs/ is wiped)
    for old, new in REDIRECTS.items():
        if old.strip("/") == new.strip("/"):
            continue
        write(f"{old.strip('/')}/index.html", redirect_stub(new.strip("/")))

    # homepage: latest 5 posts
    cards = "\n".join(
        f'<a class="post-card" href="/digest/{m["slug"]}/">'
        f'<span class="post-date">{m["date"]}</span>'
        f'<h3>{html.escape(m["title"])}</h3>'
        f'<p>{html.escape(m.get("summary", ""))}</p></a>'
        for m in posts[:5]
    ) or '<p class="muted">First digest drops Monday.</p>'
    latest = posts[0] if posts else {}
    write("index.html", render("index.html", post_cards=cards,
                               latest_title=latest.get("title", "The Monday digest"),
                               latest_summary=latest.get("summary", ""),
                               latest_url=f'/digest/{latest["slug"]}/' if latest else "/digest/",
                               page_title=f'{SITE["name"]} — {SITE["tagline"]}'))

    # digest archive
    all_cards = "\n".join(
        f'<a class="post-card" href="/digest/{m["slug"]}/">'
        f'<span class="post-date">{m["date"]}</span>'
        f'<h3>{html.escape(m["title"])}</h3>'
        f'<p>{html.escape(m.get("summary", ""))}</p></a>'
        for m in posts
    ) or '<p class="muted">First digest drops Monday.</p>'
    write("digest/index.html",
          render("page.html", title="The Weekly Digest",
                 body=f'<div class="post-grid">{all_cards}</div>',
                 page_title=f'Digest archive — {SITE["name"]}'))

    # RSS
    items = "\n".join(
        f"<item><title>{html.escape(m['title'])}</title>"
        f"<link>{SITE['url']}/digest/{m['slug']}/</link>"
        f"<guid>{SITE['url']}/digest/{m['slug']}/</guid>"
        f"<pubDate>{m['date']}</pubDate>"
        f"<description>{html.escape(m.get('summary', ''))}</description></item>"
        for m in posts[:20]
    )
    write("feed.xml",
          f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
          f'<title>{SITE["name"]}</title><link>{SITE["url"]}</link>'
          f'<description>{SITE["description"]}</description>'
          f'<lastBuildDate>{datetime.now(timezone.utc).isoformat()}</lastBuildDate>'
          f'{items}</channel></rss>')

    print(f"[done] {len(posts)} post(s), {len(REDIRECTS)} redirect(s), site in docs/")


if __name__ == "__main__":
    main()
