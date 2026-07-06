# IndyIMBY — site framework

Static site for indyimby.com: placard-yellow homepage with the live
Entitlement Tracker embedded, a Monday digest, and participation guides.
No frameworks — a ~150-line Python builder turns markdown into HTML.

## Structure

- `content/posts/YYYY-MM-DD-slug.md` — digest posts (front matter: title, date, summary)
- `content/pages/slug.md` — evergreen pages (start-here, how-to-testify, about)
- `templates/` — base, index, post, page HTML
- `static/style.css` — the design system
- `build.py` — builds everything into `docs/` (homepage, archive, RSS)

## Setup

1. Push to a new GitHub repo. Settings → Pages → branch `main`, folder `/docs`.
2. Custom domain: add `indyimby.com` in Pages settings; at your registrar,
   point the apex A records at GitHub Pages and add a `www` CNAME to
   `YOURNAME.github.io`. Put the tracker repo on `map.indyimby.com` the same way.
3. Edit `SITE` at the top of `build.py` (URLs) and the Substack/Proformus
   links in `templates/base.html`.
4. Write: drop a markdown file in `content/posts/`, push. The GitHub Action
   rebuilds `docs/` automatically (or run `python build.py` locally).

## Publishing workflow (once the digest generator lands)

The digest generator in the tracker repo will draft each Monday's post as
markdown; you edit for voice, drop it in `content/posts/`, push. RSS at
`/feed.xml` feeds email via Buttondown/Substack.

## TODOs left in content (search for "TODO")

- Backfill observations in the welcome post
- HPM/UPS framework links on Start Here
- Remote-participation procedure + sample script on the testify page
- Contact info on About
