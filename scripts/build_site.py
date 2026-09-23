"""Build the static website into _site/ from the templates and the data files.

What one build does:
  1. Read config/site.yaml, config/sources.yaml and the data files.
  2. Delete _site/ and create it again (it's always rebuilt from scratch).
  3. Copy static/ (CSS, JS) to _site/static/.
  4. Render every page with Jinja2:
       index.html               Today in AI Safety (the home page)
       news/index.html          the news archive: one line per month
       news/YYYY-MM/index.html  all entries of one month
       papers/index.html        my curated papers, essays, reports... (data/papers.yaml)
       library/index.html       the Library: books on shelves (data/books.yaml)
       library/<id>/index.html  one page per book (the card, for visitors without JS)
       my-shelf/index.html      the visitor's own "to read" / "read" marks
       about/index.html         what the site is + status of the last fetch
       404.html                 "page not found" (GitHub Pages serves it)
     Entries in data/papers.yaml and data/books.yaml are validated first; an
     entry without a synopsis (or with a TODO in a required field) is skipped
     with a warning.
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
PAPERS_FILE = ROOT / "data" / "papers.yaml"
BOOKS_FILE = ROOT / "data" / "books.yaml"
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
# Papers (data/papers.yaml): validation and the publishing rule
# ---------------------------------------------------------------------------

PAPER_TYPES = {"paper": "Paper", "essay": "Essay", "report": "Report",
               "scenario": "Scenario", "blog-post": "Blog post"}
DIFFICULTIES = {"intro": "Intro", "intermediate": "Intermediate", "advanced": "Advanced"}
PAPER_REQUIRED = ("id", "title", "authors", "year", "type", "url", "tags",
                  "difficulty", "added")
OPTIONAL_TEXT = ("why_it_matters", "my_opinion")
BOOK_REQUIRED = ("id", "title", "authors", "year", "publisher", "shelf", "olid",
                 "url", "added")
OLID_RE = re.compile(r"^OL\d+M$")
COVERS_URL = "https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def has_todo(value) -> bool:
    """True if a field (or anything inside it) still contains a TODO placeholder."""
    return "TODO" in str(value)


def check_url(url, where: str) -> None:
    """Hand-written URLs must be http(s) and carry no tracking parameters."""
    parts = urlsplit(str(url))
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise BuildError(f"{where}: url must start with http:// or https://, got {url!r}")
    if "utm_" in parts.query.lower():
        raise BuildError(f"{where}: remove the tracking parameters (utm_...) from {url}")


def publishable(entry: dict, required: tuple, where: str) -> bool:
    """The publishing rule, shared by papers and books.

    Missing required fields stop the build. An entry without a synopsis (or
    with TODO in it or in a required field) is skipped with a warning.
    """
    missing = [key for key in required if entry.get(key) in (None, "", [])]
    if missing:
        raise BuildError(f"{where}: missing {', '.join(missing)}")
    synopsis = entry.get("synopsis")
    if not synopsis or has_todo(synopsis):
        print(f"  warning: {where} not published (no synopsis yet)")
        return False
    todo_fields = [key for key in required if has_todo(entry[key])]
    if todo_fields:
        print(f"  warning: {where} not published (TODO in {', '.join(todo_fields)})")
        return False
    if not ID_RE.match(str(entry["id"])):
        raise BuildError(f"{where}: id must be a lowercase slug like 'sleeper-agents'")
    return True


def hide_todo_texts(entry: dict, where: str) -> dict:
    """Optional texts (why_it_matters, my_opinion) are hidden while they hold a TODO."""
    entry = dict(entry)
    for key in OPTIONAL_TEXT:
        if has_todo(entry.get(key)):
            print(f"  warning: {where}: {key} still has a TODO, not shown")
            entry[key] = None
        else:
            entry.setdefault(key, None)
    return entry


def load_entry_ids(path: Path) -> list[str]:
    """Ids of all entries in a YAML data file (empty list if it doesn't exist)."""
    if not path.exists():
        return []
    data = load_yaml(path) or {}
    return [str(e.get("id")) for e in (data.get("entries") or [])]


def load_papers(topics: set[str]) -> tuple[list[dict], list[dict]]:
    """Validate data/papers.yaml and return (published entries, Start Here stages).

    Publishing rule: an entry is published only if it has a synopsis without
    TODO and no required field contains TODO. Optional texts (why_it_matters,
    my_opinion) that still contain TODO are simply not shown. Malformed data
    (unknown type or topic, bad URL, duplicate id...) stops the build.
    """
    data = load_yaml(PAPERS_FILE) or {}
    stages = data.get("start_here_stages") or []
    stage_ids = {stage["id"] for stage in stages}
    entries = data.get("entries") or []

    # Ids must be unique across papers.yaml AND books.yaml: the reading tracker
    # keys every mark by id alone.
    ids = [str(e.get("id")) for e in entries] + load_entry_ids(BOOKS_FILE)
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise BuildError("duplicate id(s) across papers.yaml/books.yaml: " + ", ".join(duplicates))

    published = []
    for n, entry in enumerate(entries, start=1):
        where = f"data/papers.yaml entry {n} ({entry.get('id', 'no id')})"
        if not publishable(entry, PAPER_REQUIRED, where):
            continue
        if entry["type"] not in PAPER_TYPES:
            raise BuildError(f"{where}: type must be one of {', '.join(PAPER_TYPES)}")
        if entry["difficulty"] not in DIFFICULTIES:
            raise BuildError(f"{where}: difficulty must be one of {', '.join(DIFFICULTIES)}")
        unknown = [t for t in entry["tags"] if t not in topics]
        if unknown:
            raise BuildError(f"{where}: unknown topic(s) {', '.join(unknown)} "
                             f"(allowed: {', '.join(sorted(topics))})")
        check_url(entry["url"], where)
        start_here = entry.get("start_here")
        if start_here and start_here.get("stage") not in stage_ids:
            raise BuildError(f"{where}: start_here.stage {start_here.get('stage')!r} "
                             "is not in start_here_stages")

        paper = hide_todo_texts(entry, where)
        paper["year"] = int(paper["year"])
        published.append(paper)

    # Newest first; alphabetical within a year.
    published.sort(key=lambda p: (-p["year"], p["title"].lower()))
    return published, stages


def load_books() -> list[dict]:
    """Validate data/books.yaml and return the shelves, each with its published books.

    Same publishing rule as papers. Covers: `cover_id` becomes an image URL on
    covers.openlibrary.org (by id, never by ISBN); without it the templates
    draw a typographic cover. (Id uniqueness across both files is checked in
    load_papers.)
    """
    if not BOOKS_FILE.exists():
        return []
    data = load_yaml(BOOKS_FILE) or {}
    shelves = [dict(shelf, books=[]) for shelf in (data.get("shelves") or [])]
    by_id = {shelf["id"]: shelf for shelf in shelves}

    for n, entry in enumerate(data.get("entries") or [], start=1):
        where = f"data/books.yaml entry {n} ({entry.get('id', 'no id')})"
        if not publishable(entry, BOOK_REQUIRED, where):
            continue
        if entry["shelf"] not in by_id:
            raise BuildError(f"{where}: shelf {entry['shelf']!r} is not in `shelves`")
        if not OLID_RE.match(str(entry["olid"])):
            raise BuildError(f"{where}: olid must be an Open Library edition id like OL12345678M")
        check_url(entry["url"], where)
        if entry.get("free_url"):
            check_url(entry["free_url"], where)
        cover_id = entry.get("cover_id")
        if cover_id is not None and not str(cover_id).isdigit():
            raise BuildError(f"{where}: cover_id must be a number (the Open Library cover id)")

        book = hide_todo_texts(entry, where)
        book["year"] = int(book["year"])
        book.setdefault("subtitle", None)
        book.setdefault("edition", None)
        book.setdefault("free_url", None)
        book["cover"] = (COVERS_URL.format(cover_id=cover_id, size="M") if cover_id else None)
        book["cover_large"] = (COVERS_URL.format(cover_id=cover_id, size="L") if cover_id else None)
        book["shelf_title"] = by_id[entry["shelf"]]["title"]
        book["shelf_index"] = shelves.index(by_id[entry["shelf"]])
        by_id[entry["shelf"]]["books"].append(book)
    return shelves


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
        paper_types=PAPER_TYPES,
        difficulties=DIFFICULTIES,
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
    """Sources and topics present in a list of news entries, for the filter menus.

    Sources are (source_id, name) pairs: the id is what the item's
    data-source attribute holds, the name is what the menu shows.
    """
    return {
        "sources": sorted({(e["source_id"], e["source"]) for e in entries},
                          key=lambda option: option[1].lower()),
        "topics": sorted({t for e in entries for t in e["topics"]}),
    }


def paper_filter_options(papers: list[dict]) -> dict:
    """Years, types, topics and difficulties present in the papers, for the filters."""
    return {
        "years": sorted({p["year"] for p in papers}, reverse=True),
        "types": [t for t in PAPER_TYPES if any(p["type"] == t for p in papers)],
        "topics": sorted({t for p in papers for t in p["tags"]}),
        "difficulties": [d for d in DIFFICULTIES if any(p["difficulty"] == d for p in papers)],
    }


def build() -> None:
    site = load_site_config()
    sources = load_yaml(SOURCES_CONFIG)
    status = load_json(STATUS_FILE, {})
    entries = load_news()
    papers, _start_here_stages = load_papers(set(sources["topics"]))
    shelves = load_books()
    books = [book for shelf in shelves for book in shelf["books"]]
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

    # --- Papers and the visitor's shelf ---------------------------------------
    render(env, "papers.html", "papers/index.html",
           papers=papers, filters=paper_filter_options(papers))
    render(env, "my_shelf.html", "my-shelf/index.html", papers=papers, books=books)

    # --- Library: the shelves, and one page per book --------------------------
    render(env, "library.html", "library/index.html", shelves=shelves, books=books)
    for book in books:
        render(env, "book.html", f"library/{book['id']}/index.html", book=book)

    # --- About and 404 --------------------------------------------------------
    render(env, "about.html", "about/index.html",
           sources=sources["sources"], arxiv=sources.get("arxiv", {}))
    render(env, "404.html", "404.html")

    check_internal_links(site["base_path"])
    pages = sum(1 for _ in OUTPUT_DIR.rglob("*.html"))
    print(f"Built {pages} pages from {len(entries)} news entries, {len(papers)} papers"
          f" and {len(books)} books into {OUTPUT_DIR.name}/ (internal links OK)")


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
