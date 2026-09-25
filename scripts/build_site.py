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
       start-here/index.html    the Start Here reading path (start_here blocks in papers.yaml)
       my-path/index.html       My Own Path: timeline, bookshelf, journal (data/my_path/)
       my-shelf/index.html      the visitor's own "to read" / "read" marks
       about/index.html         what the site is + status of the last fetch
       404.html                 "page not found" (GitHub Pages serves it)
     Entries in data/papers.yaml and data/books.yaml are validated first; an
     entry without a synopsis (or with a TODO in a required field) is skipped
     with a warning.
  5. Check every internal link and asset: it must start with the base path
     (/AiSafetyWeb/) and point to a file that exists. Otherwise the build fails.
  6. Check that nothing from the local-only "Add entry" form (local_form.py)
     is in _site/. Otherwise the build fails.

Usage (from the repository root, with the venv active):
    python scripts/build_site.py            # build into _site/
    python scripts/build_site.py --serve    # build, then preview on localhost
                                            # (with the local "Add entry" form)
"""

from __future__ import annotations

import argparse
import datetime as dt
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
TIMELINE_FILE = ROOT / "data" / "my_path" / "timeline.yaml"
READING_LOG_FILE = ROOT / "data" / "my_path" / "reading_log.yaml"
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
            entry.setdefault("date_only", False)
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
# Start Here (the start_here blocks in data/papers.yaml)
# ---------------------------------------------------------------------------

def build_start_here(stages: list[dict], papers: list[dict]) -> list[dict]:
    """The Start Here path: each stage with its published papers, in order.

    A paper joins a stage through its own `start_here: {stage, order, note}`
    block (the stage id is already checked in load_papers). A block whose
    note is missing or still has a TODO is left out of the path (the paper
    stays in Papers).
    """
    path = [dict(stage, entries=[]) for stage in stages]
    by_id = {stage["id"]: stage for stage in path}
    for paper in papers:
        block = paper.get("start_here")
        if not block:
            continue
        where = f"data/papers.yaml ({paper['id']}): start_here"
        if not block.get("note") or has_todo(block["note"]) or has_todo(by_id[block["stage"]].get("intro")):
            print(f"  warning: {where} not in the path (no note yet)")
            continue
        if not isinstance(block.get("order"), int):
            raise BuildError(f"{where}: order must be a whole number")
        stage = by_id[block["stage"]]
        if any(e["start_here"]["order"] == block["order"] for e in stage["entries"]):
            raise BuildError(f"{where}: two entries with order {block['order']} in stage {stage['id']!r}")
        stage["entries"].append(paper)
    for stage in path:
        stage["entries"].sort(key=lambda p: p["start_here"]["order"])
    return [stage for stage in path if stage["entries"]]


# ---------------------------------------------------------------------------
# My Own Path (data/my_path/): timeline, reading log, bookshelf, journal
# ---------------------------------------------------------------------------

TIMELINE_TYPES = {"course": "Course", "project": "Project", "milestone": "Milestone"}
TIMELINE_STATUSES = {"in-progress": "In progress", "completed": "Completed"}
READING_TYPES = {"paper": "Paper", "report": "Report", "essay": "Essay",
                 "article": "Article", "book": "Book", "resource": "Resource",
                 "podcast-video": "Podcast / video"}
# Group headings in the Journal ("3 essays", "Podcasts / videos").
PLURALS = {"course": "Courses", "project": "Projects", "milestone": "Milestones",
           "paper": "Papers", "report": "Reports", "essay": "Essays",
           "article": "Articles", "book": "Books", "resource": "Resources",
           "podcast-video": "Podcasts / videos"}
BOOK_STATUSES = ("reading", "finished")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Problems:
    """Collects validation problems for one entry, each tied to a field.

    The build stops at the first one (BuildError, same messages as always);
    the local "Add entry" form shows all of them next to their fields.
    """

    def __init__(self, where: str):
        self.where = where
        self.items: list[tuple[str, str]] = []   # (field, message)

    def add(self, field: str, message: str) -> None:
        self.items.append((field, message))

    def __bool__(self) -> bool:
        return bool(self.items)

    def raise_first(self) -> None:
        if self.items:
            raise BuildError(f"{self.where}: {self.items[0][1]}")


def url_problem(url) -> str | None:
    """The check_url rule, as a message instead of an exception."""
    try:
        check_url(url, "")
    except BuildError as exc:
        return str(exc).removeprefix(": ")
    return None


def as_date(value, where: str, field: str) -> dt.date:
    """YAML reads 2026-09-07 as a date; anything else is a mistake."""
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and DATE_RE.match(value):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            pass
    raise BuildError(f"{where}: {field} must be a date like 2026-09-07, got {value!r}")


def as_month(value, where: str, field: str) -> str:
    """Months are written in quotes ("2026-09"); unquoted YAML may turn them into numbers."""
    if not isinstance(value, str) or not MONTH_RE.match(value):
        raise BuildError(f'{where}: {field} must be a month in quotes like "2026-09", got {value!r}')
    return value


def check_timeline_item(item: dict, seen_ids: set, p: Problems) -> None:
    """Every rule for one timeline.yaml entry. Adds problems to `p`."""
    for key in ("id", "type", "date", "title", "status"):
        if not item.get(key):
            p.add(key, f"missing {key}")
    if item.get("id") and (not ID_RE.match(str(item["id"])) or item["id"] in seen_ids):
        p.add("id", "id must be a unique lowercase slug")
    if item.get("type") and item["type"] not in TIMELINE_TYPES:
        p.add("type", f"type must be one of {', '.join(TIMELINE_TYPES)}")
    if item.get("status") and item["status"] not in TIMELINE_STATUSES:
        p.add("status", f"status must be one of {', '.join(TIMELINE_STATUSES)}")
    start = end = None
    for key in ("date", "completed"):
        if item.get(key):
            try:
                value = as_date(item[key], "", key)
            except BuildError as exc:
                p.add(key, str(exc).removeprefix(": "))
                continue
            start, end = (value, end) if key == "date" else (start, value)
    if start and end and end < start:
        p.add("completed", "completed is before date")
    if item.get("status") == "completed" and not item.get("completed") and item.get("type") != "milestone":
        p.add("completed", "a completed stage needs `completed:`")
    if item.get("status") == "in-progress" and item.get("completed"):
        p.add("status", "a stage with `completed:` must have status: completed")
    if item.get("url") and url_problem(item["url"]):
        p.add("url", url_problem(item["url"]))


def load_timeline(today: dt.date, path: Path = TIMELINE_FILE) -> list[dict]:
    """Validate timeline.yaml; newest first, each stage with its duration in days.

    Notes that still contain a TODO placeholder are not shown.
    """
    items = load_yaml(path) or []
    seen, timeline = set(), []
    for n, item in enumerate(items, start=1):
        where = f"data/my_path/timeline.yaml entry {n} ({item.get('id', 'no id')})"
        problems = Problems(where)
        check_timeline_item(item, seen, problems)
        problems.raise_first()
        seen.add(item["id"])
        start = as_date(item["date"], where, "date")
        end = as_date(item["completed"], where, "completed") if item.get("completed") else None
        stage = dict(item, start=start, end=end)
        stage["days"] = ((end or max(today, start)) - start).days + 1
        stage.setdefault("provider", None)
        stage.setdefault("url", None)
        stage["notes"] = None if has_todo(item.get("notes")) else item.get("notes")
        if has_todo(item.get("notes")):
            print(f"  warning: {where}: notes still have a TODO, not shown")
        timeline.append(stage)
    timeline.sort(key=lambda t: t["start"], reverse=True)
    longest = max((t["days"] for t in timeline if t["type"] != "milestone"), default=1)
    for stage in timeline:
        # Width of the duration bar, relative to the longest stage (never invisible).
        stage["bar"] = max(3, round(100 * stage["days"] / longest))
    return timeline


def check_log_entry(item: dict, timeline_ids: set, paper_ids: set, book_ids: set,
                    p: Problems) -> None:
    """Every rule for one reading_log.yaml entry. Adds problems to `p`."""
    kind = item.get("type")
    if kind not in READING_TYPES:
        p.add("type", f"type must be one of {', '.join(READING_TYPES)}")
    is_book = kind == "book"
    if is_book:
        if item.get("status") not in BOOK_STATUSES:
            p.add("status", "a book needs status: reading or finished")
        if item.get("status") == "finished" and not item.get("month"):
            p.add("month", "a finished book needs month: (the month I finished it)")
        if item.get("status") == "reading" and item.get("month"):
            p.add("month", "a book I'm still reading has no month: (add it when I finish)")
        if item.get("started"):
            try:
                as_month(item["started"], "", "started")
            except BuildError as exc:
                p.add("started", str(exc).removeprefix(": "))
    elif item.get("status") or item.get("started"):
        p.add("status" if item.get("status") else "started", "status/started are only for books")
    if item.get("month") is not None:
        try:
            as_month(item["month"], "", "month")
        except BuildError as exc:
            p.add("month", str(exc).removeprefix(": "))
    elif not is_book:
        p.add("month", "missing month")
    if (is_book and item.get("started") and item.get("month") and MONTH_RE.match(str(item["started"]))
            and MONTH_RE.match(str(item["month"])) and item["started"] > item["month"]):
        p.add("started", "started is after the month I finished it")

    if item.get("via") and item["via"] not in timeline_ids:
        p.add("via", f"via {item['via']!r} is not an id in timeline.yaml")
    if item.get("paper_ref") and item.get("book_ref"):
        p.add("book_ref", "use paper_ref or book_ref, not both")
    if item.get("paper_ref"):
        if item["paper_ref"] not in paper_ids:
            p.add("paper_ref", f"paper_ref {item['paper_ref']!r} is not a published entry of papers.yaml")
    elif item.get("book_ref"):
        if not is_book:
            p.add("book_ref", "book_ref is only for type: book")
        elif item["book_ref"] not in book_ids:
            p.add("book_ref", f"book_ref {item['book_ref']!r} is not a published book of books.yaml")
    else:
        for key in ("title", "source", "url"):
            if not item.get(key):
                p.add(key, f"missing {key} (or a paper_ref / book_ref)")
    for key in ("url", "archive_url"):
        if item.get(key) and url_problem(item[key]):
            p.add(key, url_problem(item[key]))
    cover_id = item.get("cover_id")
    if cover_id is not None and cover_id != "":
        if not is_book:
            p.add("cover_id", "cover_id is only for books")
        elif not str(cover_id).isdigit():
            p.add("cover_id", "cover_id must be a number (the Open Library cover id)")


def load_reading_log(timeline: list[dict], papers: list[dict], books: list[dict],
                     path: Path = READING_LOG_FILE) -> list[dict]:
    """Validate reading_log.yaml and resolve paper_ref / book_ref.

    Every entry comes out with title, author (may be empty), source and url,
    taken from papers.yaml / books.yaml when it has a ref, plus `ref_link`
    (the entry on this site) and `via_title`.
    """
    data = load_yaml(path) or {}
    timeline_by_id = {t["id"]: t for t in timeline}
    papers_by_id = {p["id"]: p for p in papers}
    books_by_id = {b["id"]: b for b in books}
    log = []
    for n, item in enumerate(data.get("entries") or [], start=1):
        where = f"data/my_path/reading_log.yaml entry {n} ({item.get('title') or item.get('paper_ref') or item.get('book_ref') or '?'})"
        problems = Problems(where)
        check_log_entry(item, set(timeline_by_id), set(papers_by_id), set(books_by_id), problems)
        problems.raise_first()
        entry = dict(item)
        entry["via_title"] = timeline_by_id[entry["via"]]["title"] if entry.get("via") else None
        entry["ref_link"], entry["book"] = None, None
        if entry.get("paper_ref"):
            paper = papers_by_id[entry["paper_ref"]]
            entry.update(title=paper["title"], author=", ".join(paper["authors"]),
                         source=None, url=paper["url"], ref_link=f"papers/#paper-{paper['id']}")
        elif entry.get("book_ref"):
            book = books_by_id[entry["book_ref"]]
            entry.update(title=book["title"], author=", ".join(book["authors"]),
                         source=book["publisher"], url=book["url"],
                         ref_link=f"library/{book['id']}/", book=book)
        for key in ("author", "archive_url", "via", "cover_id", "month", "started", "status"):
            entry.setdefault(key, None)
        entry["notes"] = None if has_todo(entry.get("notes")) else entry.get("notes")
        if entry["type"] == "book" and not entry["book"]:
            # A book that is not in the Library: its own (optional) cover id.
            cover_id = entry.get("cover_id")
            entry["cover"] = COVERS_URL.format(cover_id=cover_id, size="M") if cover_id else None
        log.append(entry)
    return log


def month_range(first: str, last: str) -> list[str]:
    """Every month from first to last, inclusive: ['2026-08', '2026-09', ...]."""
    year, month = map(int, first.split("-"))
    months = []
    while f"{year:04d}-{month:02d}" <= last:
        months.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def build_journal(timeline: list[dict], log: list[dict], today: dt.date, person: dict) -> dict:
    """The Journal: for every month, everything I did in it, grouped by type.

    A month shows:
    - the readings and resources of that month (`month` in reading_log.yaml);
    - timeline stages that started, were in progress or were completed in it
      (a stage still in progress runs until the current month);
    - books I started (`started`), was still reading, or finished (`month`).
    The chart counts, per month, the readings (finished books included) plus
    the timeline stages that started or ended in it, each stage once: a stage
    that is merely still in progress doesn't add to the bar.
    """
    this_month = today.strftime("%Y-%m")
    months: dict[str, dict[str, list]] = {}
    counts: dict[str, int] = {}

    def add(month: str, kind: str, item: dict) -> None:
        months.setdefault(month, {}).setdefault(kind, []).append(item)

    for t in timeline:
        first = t["start"].strftime("%Y-%m")
        last = t["end"].strftime("%Y-%m") if t["end"] else (first if t["type"] == "milestone" else this_month)
        for m in month_range(first, max(first, last)):
            if t["type"] == "milestone":
                state = "Milestone"
            elif m == first and t["end"] and m == last:
                state = "Started and completed"
            elif m == first:
                state = "Started"
            elif t["end"] and m == last:
                state = "Completed"
            else:
                state = "In progress"
            add(m, t["type"], {"kind": "timeline", "item": t, "state": state})
            if m in (first, last) and (m == first or t["end"]):
                counts[m] = counts.get(m, 0) + 1

    for e in log:
        if e["type"] != "book":
            add(e["month"], e["type"], {"kind": "reading", "item": e, "state": None})
            counts[e["month"]] = counts.get(e["month"], 0) + 1
            continue
        # Books: only with a known month (started and/or finished).
        first = e["started"] or e["month"]
        if not first:
            continue   # still reading, no start month: only on the Bookshelf
        last = e["month"] or this_month
        for m in month_range(first, max(first, last)):
            if e["month"] and m == e["month"]:
                state = "Started and finished" if m == e["started"] else "Finished"
            elif m == e["started"]:
                state = "Started"
            else:
                state = "Reading"
            add(m, "book", {"kind": "reading", "item": e, "state": state})
        if e["month"]:
            counts[e["month"]] = counts.get(e["month"], 0) + 1

    order = list(TIMELINE_TYPES) + ["book"] + [t for t in READING_TYPES if t != "book"]
    journal_months = []
    for month in sorted(months, reverse=True):
        groups = [{"type": kind, "label": PLURALS[kind], "entries": months[month][kind]}
                  for kind in order if kind in months[month]]
        for g in groups:
            if g["type"] in TIMELINE_TYPES:
                g["entries"].sort(key=lambda x: x["item"]["start"], reverse=True)
        journal_months.append({"month": month, "groups": groups,
                               "total": sum(len(g["entries"]) for g in groups)})

    chart = []
    if months:
        top = max(counts.values(), default=0) or 1
        for m in month_range(min(months), max(months)):
            n = counts.get(m, 0)
            chart.append({"month": m, "count": n, "bar": round(100 * n / top),
                          "has_entries": m in months})
    return {"person": person, "months": journal_months, "chart": chart}


def build_my_path(timeline: list[dict], log: list[dict], today: dt.date, person: dict) -> dict:
    """Everything the My Own Path page needs, already grouped and counted."""
    readings = [e for e in log if e["type"] != "book"]
    for stage in timeline:
        stage["readings"] = sum(1 for e in readings if e.get("via") == stage["id"])
    books = [e for e in log if e["type"] == "book"]
    return {
        "timeline": timeline,
        "journal": build_journal(timeline, log, today, person),
        "reading_now": [e for e in books if e["status"] == "reading"],
        "finished": sorted((e for e in books if e["status"] == "finished"),
                           key=lambda e: e["month"], reverse=True),
    }


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


def entry_when(e: dict, today: dt.date | None = None) -> str:
    """The date shown on a news entry, always in UTC and always saying so.

    '24 Sep 2026, 00:39 UTC', or '24 Sep 2026' when the feed gives only a day
    (`date_only`). With `today` (the home page), the day becomes relative:
    'Today, 00:39 UTC', 'Yesterday, 21:09 UTC'. Its day is always the first
    10 characters of `published`, the same key the day groups use.
    """
    day = dt.date.fromisoformat(e["published"][:10])
    time_part = "" if e["date_only"] else e["published_dt"].astimezone(timezone.utc).strftime(", %H:%M UTC")
    if today is not None and (today - day).days in (0, 1):
        return ("Today" if day == today else "Yesterday") + time_part
    return day.strftime("%d %b %Y") + time_part


def month_label(month: str) -> str:
    """'2026-09' -> 'September 2026'."""
    return datetime.strptime(month, "%Y-%m").strftime("%B %Y")


def month_short(month: str) -> str:
    """'2026-09' -> 'Sep 2026' (for the chart, where space is short on phones)."""
    return datetime.strptime(month, "%Y-%m").strftime("%b %Y")


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
        reading_types=READING_TYPES,
        plurals=PLURALS,
        timeline_types=TIMELINE_TYPES,
        timeline_statuses=TIMELINE_STATUSES,
    )
    env.filters.update(
        safe_url=safe_external_url,
        date=format_date,
        month_label=month_label,
        when=entry_when,
        month_short=month_short,
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
    papers, start_here_stages = load_papers(set(sources["topics"]))
    shelves = load_books()
    books = [book for shelf in shelves for book in shelf["books"]]
    start_here = build_start_here(start_here_stages, papers)
    today = dt.datetime.now(timezone.utc).date()
    timeline = load_timeline(today)
    my_path = build_my_path(timeline, load_reading_log(timeline, papers, books),
                            today, site["my_path"]["person"])
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
    render(env, "index.html", "index.html", today=today,
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

    # --- Start Here and My Own Path --------------------------------------------
    render(env, "start_here.html", "start-here/index.html", stages=start_here)
    # Library books on my Bookshelf open the same card as in the Library.
    shelf_books = [e["book"] for e in my_path["reading_now"] + my_path["finished"] if e["book"]]
    render(env, "my_path.html", "my-path/index.html", path=my_path, card_books=shelf_books)

    # --- About and 404 --------------------------------------------------------
    render(env, "about.html", "about/index.html",
           sources=[s for s in sources["sources"] if s.get("enabled", True)],
           arxiv=sources.get("arxiv", {}))
    render(env, "404.html", "404.html")

    check_internal_links(site["base_path"])
    check_no_local_tools()
    check_entry_dates()
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
# Date check: the date shown on a news entry and its day group always agree
# ---------------------------------------------------------------------------

TIME_RE = re.compile(r'<time class="entry-time" datetime="([^"]+)" data-day="([^"]+)"([^>]*)>([^<]*)</time>')
GROUP_RE = re.compile(r'<section class="day-group"[^>]*data-day="([^"]+)"[^>]*>(.*?)</section>', re.S)
TODAY_RE = re.compile(r'<time datetime="([^"]+)" data-today>')


def check_entry_dates() -> None:
    """Fail the build if any news entry's shown date disagrees with its data.

    For every entry date in _site/: `data-day` is the UTC day of `datetime`;
    the text shows that day ("24 Sep 2026", or Today / Yesterday relative to
    the page's stated "today") and, unless the feed gave only a day, that UTC
    time ("00:39 UTC"); and an entry inside a day group has the group's day.
    """
    problems = []
    for page in sorted(OUTPUT_DIR.rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        where = page.relative_to(OUTPUT_DIR).as_posix()
        anchor = TODAY_RE.search(html)
        today = dt.date.fromisoformat(anchor.group(1)) if anchor else None
        for stamp, day, attrs, text in TIME_RE.findall(html):
            instant = parse_time(stamp).astimezone(timezone.utc)
            shown_day = dt.date.fromisoformat(day)
            expected = []
            if "data-relative" in attrs and today and (today - shown_day).days in (0, 1):
                expected.append("Today" if shown_day == today else "Yesterday")
            else:
                expected.append(shown_day.strftime("%d %b %Y"))
            if "data-date-only" not in attrs:
                expected.append(instant.strftime("%H:%M UTC"))
            if instant.date() != shown_day or not all(part in text for part in expected):
                problems.append(f"{where}: '{text}' for {stamp} (day {day})")
        for group_day, body in GROUP_RE.findall(html):
            for _, day, _, text in TIME_RE.findall(body):
                if day != group_day:
                    problems.append(f"{where}: '{text}' is in the day group {group_day}")
    if problems:
        raise BuildError("news dates that don't match their day:\n  " + "\n  ".join(problems[:20]))


# The local "Add entry" form (scripts/local_form.py) is only ever generated by
# the preview server, in memory. These markers must never reach _site/: if a
# template or static file ever carries them, the build fails, so the form can't
# be published by mistake (on GitHub Pages it would be a dead, confusing page).
LOCAL_ONLY_MARKERS = ("data-local-only", "/_local/")


def check_no_local_tools() -> None:
    """Fail the build if anything from the local-only form ended up in _site/."""
    found = []
    for file in sorted(OUTPUT_DIR.rglob("*")):
        if file.suffix not in (".html", ".js", ".css", ".json", ".txt", ".xml"):
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        found += [f"{file.relative_to(OUTPUT_DIR).as_posix()}: {m}" for m in LOCAL_ONLY_MARKERS if m in text]
    if found:
        raise BuildError("local-only form code found in the output (it must never be "
                         "published):\n  " + "\n  ".join(found))


# ---------------------------------------------------------------------------
# Local preview server
# ---------------------------------------------------------------------------

def serve(base_path: str, port: int) -> None:
    """Serve _site/ at http://localhost:<port><base_path>, like GitHub Pages.

    The real site lives under /AiSafetyWeb/, so the preview does too: that way
    a link that forgets the base path breaks here as well, not only online.

    The preview also serves my local-only "Add entry" form (scripts/local_form.py)
    at <base_path>_local/add-entry/, generated in memory, and adds a link to it
    on My Own Path while serving that page. Neither is ever written to _site/.
    It listens on 127.0.0.1 only, so nothing else on the network can reach it.
    """
    import local_form   # only the preview needs it (scripts/ is on the import path)
    form = local_form.LocalForm(sys.modules[__name__], base_path, port)
    my_path_page = base_path + "my-path/"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(OUTPUT_DIR), **kwargs)

        def translate_path(self, path: str) -> str:
            # Strip the base path; anything outside it doesn't exist.
            if path.startswith(base_path):
                return super().translate_path("/" + path[len(base_path):])
            return str(OUTPUT_DIR / "__outside_base_path__")

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == form.path:
                return form.handle_get(self)
            if path in (my_path_page, my_path_page + "index.html"):
                return self.send_my_path()
            if self.path in ("/", ""):
                self.send_response(302)
                self.send_header("Location", base_path)
                self.end_headers()
                return
            super().do_GET()

        def do_POST(self):
            if urlsplit(self.path).path == form.path:
                return form.handle_post(self)
            self.send_error(405)

        def send_my_path(self):
            """My Own Path with the local "Add entry" link added (in memory only)."""
            page = (OUTPUT_DIR / "my-path" / "index.html").read_text(encoding="utf-8")
            body = form.inject_link(page).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

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
    print(f"Add entry (local only): http://localhost:{port}{form.path}")
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
