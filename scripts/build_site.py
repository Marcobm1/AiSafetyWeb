"""Build the static website into _site/ from the templates and the data files.

What one build does:
  1. Read config/site.yaml, config/sources.yaml and the data files.
  2. Delete _site/ and create it again (it's always rebuilt from scratch).
  3. Copy static/ (CSS, JS) to _site/static/.
  4. Render every page with Jinja2:
       index.html               Today in AI Safety (the home page)
       news/index.html          the news archive: one line per month
       news/YYYY-MM/index.html  all entries of one month
       about/index.html         what the site is + status of the last fetch
       404.html                 "page not found" (GitHub Pages serves it)
  5. Check every internal link and asset: it must start with the base path
     (/AiSafetyWeb/) and point to a file that exists. Otherwise the build fails.

Usage (from the repository root, with the venv active):
    python scripts/build_site.py            # build into _site/
    python scripts/build_site.py --serve    # build, then preview on localhost
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import re
import shutil
import sys
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
SITE_CONFIG = ROOT / "config" / "site.yaml"
SOURCES_CONFIG = ROOT / "config" / "sources.yaml"
NEWS_DIR = ROOT / "data" / "news"
STATUS_FILE = ROOT / "data" / "status.json"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "_site"


class BuildError(Exception):
    """A problem in the config or data that must be fixed before publishing."""


# ---------------------------------------------------------------------------
# Loading data
# ---------------------------------------------------------------------------

def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_time(value: str | None) -> datetime | None:
    """'2026-09-23T10:45:44Z' -> timezone-aware datetime (None stays None)."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_site_config() -> dict:
    config = load_yaml(SITE_CONFIG)
    base = config.get("base_path", "")
    if not (base.startswith("/") and base.endswith("/")):
        raise BuildError(f"config/site.yaml: base_path must start and end with '/', got {base!r}")
    return config


def load_news() -> list[dict]:
    """Every saved news entry, newest first, with `published` as a datetime."""
    entries = []
    for path in sorted(NEWS_DIR.glob("*.json")):
        for entry in load_json(path, []):
            entry = dict(entry)
            entry["published_dt"] = parse_time(entry["published"])
            entries.append(entry)
    entries.sort(key=lambda e: e["published_dt"], reverse=True)
    return entries


# ---------------------------------------------------------------------------
# Template helpers (available inside every template)
# ---------------------------------------------------------------------------

def make_url(base_path: str, path: str = "") -> str:
    """Internal link with the base path: url('news/') -> '/AiSafetyWeb/news/'."""
    return base_path + path.lstrip("/")


def safe_external_url(url: str | None) -> str:
    """Only allow http(s) links from feeds.

    A malicious feed could send a `javascript:` URL; on a link, that would run
    code in the visitor's browser. Anything that isn't http(s) becomes '#'.
    """
    if url and urlsplit(url).scheme in ("http", "https"):
        return url
    return "#"


def format_date(dt: datetime | None, fmt: str = "%d %b %Y") -> str:
    """Dates are shown in UTC, e.g. '23 Sep 2026'."""
    return dt.astimezone(timezone.utc).strftime(fmt) if dt else ""


def month_label(month: str) -> str:
    """'2026-09' -> 'September 2026'."""
    return datetime.strptime(month, "%Y-%m").strftime("%B %Y")


def make_env(site: dict, status: dict) -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        # Escape every value inserted into HTML: a title like "<script>" is
        # shown as text, never run.
        autoescape=select_autoescape(["html"]),
        # Fail loudly on a typo like {{ entyr.title }} instead of printing nothing.
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(
        site=site,
        status=status,
        last_run=parse_time(status.get("last_run")),
        url=functools.partial(make_url, site["base_path"]),
        topic_label=lambda topic: site["topics"].get(topic, topic.title()),
    )
    env.filters.update(
        safe_url=safe_external_url,
        date=format_date,
        month_label=month_label,
    )
    return env


# ---------------------------------------------------------------------------
# Building the pages
# ---------------------------------------------------------------------------

def group_by(entries: list[dict], key) -> "OrderedDict[str, list[dict]]":
    """Group entries (already sorted) by key(entry), keeping the order."""
    groups: OrderedDict[str, list[dict]] = OrderedDict()
    for entry in entries:
        groups.setdefault(key(entry), []).append(entry)
    return groups


def render(env: Environment, template: str, out_path: str, **context) -> None:
    """Render one template to _site/<out_path>."""
    target = OUTPUT_DIR / out_path
    target.parent.mkdir(parents=True, exist_ok=True)
    context.setdefault("current_path", out_path.removesuffix("index.html"))
    html = env.get_template(template).render(**context)
    target.write_text(html, encoding="utf-8", newline="\n")


def filter_options(entries: list[dict]) -> dict:
    """Sources and topics present in a list of entries, for the filter menus."""
    return {
        "sources": sorted({e["source"] for e in entries}),
        "topics": sorted({t for e in entries for t in e["topics"]}),
    }


def build() -> None:
    site = load_site_config()
    sources = load_yaml(SOURCES_CONFIG)
    status = load_json(STATUS_FILE, {})
    entries = load_news()
    env = make_env(site, status)

    # Start from an empty _site/ so deleted pages don't linger.
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()
    shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static")
    # Tells GitHub Pages not to run its own (Jekyll) processing on our files.
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    # --- Home: the last `window_hours` before the last fetch run ------------
    reference = parse_time(status.get("last_run")) or datetime.now(timezone.utc)
    since = reference - timedelta(hours=site["home"]["window_hours"])
    recent = [e for e in entries if e["published_dt"] >= since]
    recent_posts = [e for e in recent if e["source_id"] != "arxiv"]
    recent_papers = [e for e in recent if e["source_id"] == "arxiv"]
    # One group per source, the source with the newest post first.
    by_source = group_by(recent_posts, key=lambda e: e["source"])
    render(env, "index.html", "index.html",
           by_source=by_source, papers=recent_papers,
           window_hours=site["home"]["window_hours"], latest=entries[:10])

    # --- News archive: one page per month ------------------------------------
    by_month = group_by(entries, key=lambda e: e["published"][:7])
    render(env, "news_index.html", "news/index.html",
           months=[(month, len(items)) for month, items in by_month.items()])
    months = list(by_month)
    for i, (month, items) in enumerate(by_month.items()):
        by_day = group_by(items, key=lambda e: e["published"][:10])
        render(env, "news_month.html", f"news/{month}/index.html",
               month=month, by_day=by_day, count=len(items),
               filters=filter_options(items),
               newer=months[i - 1] if i > 0 else None,
               older=months[i + 1] if i + 1 < len(months) else None)

    # --- About and 404 --------------------------------------------------------
    render(env, "about.html", "about/index.html",
           sources=sources["sources"], arxiv=sources.get("arxiv", {}))
    render(env, "404.html", "404.html")

    check_internal_links(site["base_path"])
    pages = sum(1 for _ in OUTPUT_DIR.rglob("*.html"))
    print(f"Built {pages} pages from {len(entries)} news entries into {OUTPUT_DIR.name}/"
          " (internal links OK)")


# ---------------------------------------------------------------------------
# Link check
# ---------------------------------------------------------------------------

LINK_RE = re.compile(r'(?:href|src)="([^"#?]*)[^"]*"')


def check_internal_links(base_path: str) -> None:
    """Fail the build if an internal link or asset is broken.

    Internal = starts with '/'. It must start with the base path (a link like
    '/static/css/style.css' works locally without a base path but 404s on GitHub
    Pages) and must point to a file in _site/ ('.../news/' means '.../news/index.html').
    """
    problems = []
    for page in sorted(OUTPUT_DIR.rglob("*.html")):
        for target in LINK_RE.findall(page.read_text(encoding="utf-8")):
            if not target.startswith("/"):
                continue  # external (https://...) or empty '#'
            where = page.relative_to(OUTPUT_DIR).as_posix()
            if not target.startswith(base_path):
                problems.append(f"{where}: {target} (missing base path {base_path})")
                continue
            file = OUTPUT_DIR / target[len(base_path):]
            if target.endswith("/"):
                file = file / "index.html"
            if not file.is_file():
                problems.append(f"{where}: {target} (no such file)")
    if problems:
        raise BuildError("broken internal links:\n  " + "\n  ".join(problems))


# ---------------------------------------------------------------------------
# Local preview server
# ---------------------------------------------------------------------------

def serve(base_path: str, port: int) -> None:
    """Serve _site/ at http://localhost:<port><base_path>, like GitHub Pages.

    The real site lives under /AiSafetyWeb/, so the preview does too: that way
    a link that forgets the base path breaks here as well, not only online.
    """

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(OUTPUT_DIR), **kwargs)

        def translate_path(self, path: str) -> str:
            # Strip the base path; anything outside it doesn't exist.
            if path.startswith(base_path):
                return super().translate_path("/" + path[len(base_path):])
            return str(OUTPUT_DIR / "__outside_base_path__")

        def do_GET(self):
            if self.path in ("/", ""):
                self.send_response(302)
                self.send_header("Location", base_path)
                self.end_headers()
                return
            super().do_GET()

        def send_error(self, code, message=None, explain=None):
            # Like GitHub Pages: unknown pages get our 404.html.
            page = OUTPUT_DIR / "404.html"
            if code == 404 and page.exists():
                body = page.read_bytes()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().send_error(code, message, explain)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Preview: http://localhost:{port}{base_path}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--serve", action="store_true",
                        help="after building, preview the site on localhost")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        build()
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    if args.serve:
        serve(load_site_config()["base_path"], args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
