"""Fetch AI Safety news from RSS/Atom feeds and arXiv, and save it as JSON.

What one run does, in order:
  1. Read config/sources.yaml.
  2. Download every feed. A source that fails is recorded as an error and the
     others carry on.
  3. Ask the arXiv API (one request) for recent papers matching the configured
     phrases.
  4. Turn every item into the same entry format (see docs/HOW_THIS_SITE_WORKS.md
     section 3.1), assign topics by keyword and drop items that are too old or
     off-topic.
  5. Skip anything already saved (same normalised URL, or same title between two
     cross-posting sources) and add the rest to
     data/news/YYYY-MM.json (one file per month of publication).
  6. Add new arXiv papers to data/paper_candidates.json, unless they are already
     in data/papers.yaml, and delete candidates older than the retention period.
  7. Write data/status.json on every run, even when nothing is new.

Usage (from the repository root, with the venv active):
    python scripts/fetch_news.py            # fetch and save
    python scripts/fetch_news.py --dry-run  # fetch and report, write nothing
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import html
import json
import logging
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "sources.yaml"
NEWS_DIR = ROOT / "data" / "news"
STATUS_FILE = ROOT / "data" / "status.json"
CANDIDATES_FILE = ROOT / "data" / "paper_candidates.json"
PAPERS_FILE = ROOT / "data" / "papers.yaml"

ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_SOURCE = {"id": "arxiv", "name": "arXiv"}

EXCERPT_MAX_SENTENCES = 2
EXCERPT_MAX_CHARS = 320
# Topics are matched on the title plus the start of the text. Some feeds
# (LessWrong, the Alignment Forum) include the whole post, and a long post
# mentions every topic in passing.
TOPIC_TEXT_CHARS = 600

log = logging.getLogger("fetch_news")


# ---------------------------------------------------------------------------
# Small helpers: dates, text, URLs
# ---------------------------------------------------------------------------

def to_iso(dt: datetime) -> str:
    """Format a UTC datetime as '2026-09-23T06:00:00Z'."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def entry_date(item) -> datetime | None:
    """Publication date of a feed item, in UTC, or None if the feed has none."""
    for key in ("published_parsed", "updated_parsed"):
        parsed = item.get(key)
        if parsed:
            # feedparser gives a UTC time tuple; timegm turns it into a timestamp.
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
    return None


TAG_RE = re.compile(r"<[^>]+>")
SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[\"'“(\[A-Z0-9])")


def clean_text(raw: str | None) -> str:
    """Strip HTML tags and entities and collapse whitespace."""
    text = TAG_RE.sub(" ", raw or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def make_excerpt(text: str) -> str:
    """First two sentences, never longer than EXCERPT_MAX_CHARS.

    The site must never republish full articles, only a short excerpt.
    """
    sentences = SENTENCE_END_RE.split(text)
    excerpt = " ".join(sentences[:EXCERPT_MAX_SENTENCES]).strip()
    if len(excerpt) > EXCERPT_MAX_CHARS:
        cut = excerpt[:EXCERPT_MAX_CHARS].rsplit(" ", 1)[0]
        excerpt = cut.rstrip(" ,;:") + "…"
    return excerpt


ARXIV_PATH_RE = re.compile(r"^/(?:abs|pdf)/(.+?)(?:v\d+)?(?:\.pdf)?$")


def normalize_url(url: str) -> str:
    """Canonical form of a URL, so the same page is never saved twice.

    - always https, lowercase host, no #fragment, no trailing slash
    - tracking parameters (utm_*) removed
    - arXiv: /pdf/ and versioned links (v1, v2...) all become /abs/<id>
    """
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    path = parts.path
    if host in ("arxiv.org", "www.arxiv.org", "export.arxiv.org"):
        host = "arxiv.org"
        match = ARXIV_PATH_RE.match(path)
        if match:
            path = f"/abs/{match.group(1)}"
    query = urlencode(
        [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
         if not k.lower().startswith("utm_")]
    )
    if len(path) > 1:
        path = path.rstrip("/")
    return urlunsplit(("https", host, path, query, ""))


LW_POST_RE = re.compile(r"^/posts/([A-Za-z0-9]+)")


def dedupe_key(url: str) -> str:
    """Key used to detect duplicates.

    Usually the normalised URL. LessWrong and the Alignment Forum share posts
    (same post id on both sites), so for them the key is the post id.
    """
    normalized = normalize_url(url)
    parts = urlsplit(normalized)
    if parts.netloc in ("www.lesswrong.com", "lesswrong.com",
                        "www.alignmentforum.org", "alignmentforum.org"):
        match = LW_POST_RE.match(parts.path)
        if match:
            return f"lw-post:{match.group(1)}"
    return normalized


TITLE_KEY_MIN_WORDS = 4


def title_key(title: str) -> str | None:
    """Second duplicate key: the title in lowercase, without punctuation.

    Only used between cross-posting sources (see SeenIndex). Short titles
    ("Funding update") are too generic to compare, so they get no title key.
    """
    words = re.sub(r"[^a-z0-9]+", " ", title.lower()).split()
    if len(words) < TITLE_KEY_MIN_WORDS:
        return None
    return " ".join(words)


class SeenIndex:
    """Everything already saved, for duplicate detection.

    Two checks:
      1. Same URL key (normalised URL, or LessWrong/AF post id): always a duplicate.
      2. Same normalised title: a duplicate ONLY if both entries come from
         two *different* sources marked `crossposts: true` in sources.yaml
         (e.g. a Redwood Research post also published on the Alignment Forum).
         Generic titles in unrelated sources, or two pages of the same source
         with the same title, are never merged by title.
    """

    def __init__(self, crosspost_sources: set[str]):
        self.crosspost_sources = crosspost_sources
        self.url_keys: set[str] = set()
        self.titles: dict[str, set[str]] = {}  # title key -> source ids that have it

    def _title(self, entry: dict) -> str | None:
        if entry["source_id"] not in self.crosspost_sources:
            return None
        return title_key(entry["title"])

    def is_duplicate(self, entry: dict) -> bool:
        if dedupe_key(entry["url"]) in self.url_keys:
            return True
        key = self._title(entry)
        return bool(key) and bool(self.titles.get(key, set()) - {entry["source_id"]})

    def add(self, entry: dict) -> None:
        self.url_keys.add(dedupe_key(entry["url"]))
        key = self._title(entry)
        if key:
            self.titles.setdefault(key, set()).add(entry["source_id"])


def entry_id(url: str) -> str:
    """Stable id for a news entry: first 16 hex chars of the SHA-1 of its URL."""
    return hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()[:16]


def arxiv_id_from_url(url: str) -> str | None:
    """'https://arxiv.org/abs/2401.05566v2' -> '2401.05566' (None if not arXiv)."""
    parts = urlsplit(normalize_url(url))
    if parts.netloc == "arxiv.org" and parts.path.startswith("/abs/"):
        return parts.path[len("/abs/"):]
    return None


def with_query_param(url: str, key: str, value) -> str:
    """Add or replace one query parameter in a URL."""
    parts = urlsplit(url)
    params = [(k, v) for k, v in parse_qsl(parts.query) if k != key]
    params.append((key, str(value)))
    return urlunsplit(parts._replace(query=urlencode(params)))


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

class TopicMatcher:
    """Assigns topics to a text using the keyword lists in sources.yaml.

    Keywords match whole words, case insensitive. A trailing * allows any
    ending ("misalign*" matches "misaligned" and "misalignment").
    """

    def __init__(self, topics: dict[str, list[str]]):
        self.patterns = {}
        for topic, keywords in topics.items():
            parts = []
            for keyword in keywords:
                prefix = keyword.endswith("*")
                word = re.escape(keyword.rstrip("*"))
                parts.append(rf"(?<!\w){word}" + ("" if prefix else r"(?!\w)"))
            self.patterns[topic] = re.compile("|".join(parts), re.IGNORECASE)

    def match(self, text: str) -> list[str]:
        """Topics whose keywords appear in the text, in config order."""
        return [topic for topic, pattern in self.patterns.items() if pattern.search(text)]


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------

# "Too many requests" / "service unavailable": the server asks us to slow down.
SLOW_DOWN_STATUSES = (429, 503)


def http_get(session: requests.Session, url: str, timeout: int,
             params: dict | None = None, retry_delay: float = 5) -> bytes:
    """GET a URL and return the body. Tries twice before giving up.

    If the server says "slow down" (429/503), the retry waits for as long as
    its Retry-After header asks, and at least 30 seconds.
    """
    for attempt in (1, 2):
        try:
            response = session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            if attempt == 2:
                raise
            delay = retry_delay
            status = exc.response.status_code if exc.response is not None else None
            if status in SLOW_DOWN_STATUSES:
                retry_after = exc.response.headers.get("Retry-After", "")
                delay = max(30, int(retry_after) if retry_after.isdigit() else 0)
            reason = f"HTTP {status}" if status else type(exc).__name__
            log.info("  %s, retrying in %d s", reason, delay)
            time.sleep(delay)
    raise AssertionError("unreachable")


def make_entry(url: str, title: str, source: dict, published: datetime,
               fetched_at: datetime, excerpt: str, topics: list[str],
               **extra) -> dict:
    """Build one news entry in the format documented in HOW_THIS_SITE_WORKS §3.1."""
    entry = {
        "id": entry_id(url),
        "url": normalize_url(url),
        "title": title,
        "source": source["name"],
        "source_id": source["id"],
        "published": to_iso(published),
        "fetched_at": to_iso(fetched_at),
        "excerpt": excerpt,
        "topics": topics,
    }
    entry.update(extra)
    entry["summary"] = None  # reserved for future AI summaries
    return entry


def fetch_feed(source: dict, session: requests.Session, settings: dict,
               matcher: TopicMatcher, cutoff: datetime,
               fetched_at: datetime) -> tuple[list[dict], int]:
    """Download one RSS/Atom source. Returns (kept entries, items in the feed)."""
    url = source["url"]
    if "karma_threshold" in source:
        url = with_query_param(url, "karmaThreshold", source["karma_threshold"])

    content = http_get(session, url, settings["timeout_seconds"])
    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        raise ValueError(f"not a valid RSS/Atom feed ({feed.bozo_exception})")

    kept = []
    for item in feed.entries:
        link = item.get("link")
        title = clean_text(item.get("title"))
        if not link or not title:
            continue
        published = entry_date(item) or fetched_at
        if published < cutoff:
            continue
        description = clean_text(item.get("summary"))
        topics = matcher.match(f"{title} {description[:TOPIC_TEXT_CHARS]}")
        for topic in source.get("default_topics", []):
            if topic not in topics:
                topics.append(topic)
        if source.get("require_topic") and not topics:
            continue
        kept.append(make_entry(link, title, source, published, fetched_at,
                               make_excerpt(description), topics))
    return kept, len(feed.entries)


def fetch_arxiv(config: dict, session: requests.Session, settings: dict,
                matcher: TopicMatcher, cutoff: datetime,
                fetched_at: datetime) -> tuple[list[dict], int]:
    """One request to the arXiv API. Returns (kept entries, items returned)."""
    def field(term: str) -> str:
        return f'ti:"{term}" OR abs:"{term}"'

    categories = " OR ".join(f"cat:{c}" for c in config["categories"])
    # Any phrase, OR all the terms of one combination together.
    alternatives = [field(p) for p in config["phrases"]]
    alternatives += [" AND ".join(f"({field(t)})" for t in combo)
                     for combo in config.get("combinations", [])]
    params = {
        "search_query": f"({categories}) AND ({' OR '.join(f'({a})' for a in alternatives)})",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": config["max_results"],
    }
    # A single request per run. If it fails, the retry waits at least the
    # pause arXiv asks for between requests.
    content = http_get(session, ARXIV_API, settings["timeout_seconds"], params=params,
                       retry_delay=max(config["pause_seconds"], 3))
    feed = feedparser.parse(content)
    if feed.entries and "api/errors" in feed.entries[0].get("id", ""):
        raise ValueError(f"arXiv API error: {clean_text(feed.entries[0].get('summary'))}")

    kept = []
    for item in feed.entries:
        url = normalize_url(item.get("id", ""))
        arxiv_id = arxiv_id_from_url(url)
        title = clean_text(item.get("title"))
        if not arxiv_id or not title:
            continue
        published = entry_date(item) or fetched_at
        if published < cutoff:
            continue
        abstract = clean_text(item.get("summary"))
        kept.append(make_entry(
            url, title, ARXIV_SOURCE, published, fetched_at,
            make_excerpt(abstract), matcher.match(f"{title} {abstract[:TOPIC_TEXT_CHARS]}"),
            authors=[a.get("name", "") for a in item.get("authors", [])],
            arxiv_id=arxiv_id,
        ))
    return kept, len(feed.entries)


# ---------------------------------------------------------------------------
# Reading and writing data files
# ---------------------------------------------------------------------------

def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data) -> None:
    """Write JSON atomically: to a temp file first, then rename over the target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(path)


def load_news() -> dict[str, list[dict]]:
    """All saved news, as {'2026-09': [entries...], ...}."""
    return {path.stem: load_json(path, [])
            for path in sorted(NEWS_DIR.glob("*.json"))}


def load_paper_refs() -> tuple[set[str], set[str]]:
    """arXiv ids and normalised URLs of everything already in data/papers.yaml."""
    if not PAPERS_FILE.exists():
        return set(), set()
    data = load_yaml(PAPERS_FILE) or {}
    entries = data.get("entries") or []
    arxiv_ids = {str(e["arxiv_id"]) for e in entries if e.get("arxiv_id")}
    urls = {normalize_url(e["url"]) for e in entries if e.get("url")}
    return arxiv_ids, urls


def update_candidates(new_papers: list[dict], today: datetime,
                      retention_days: int) -> tuple[dict, dict]:
    """Add new arXiv papers to the candidates and clean the file.

    Returns (all candidates, counters for status.json).
    """
    candidates = load_json(CANDIDATES_FILE, {})
    paper_arxiv_ids, paper_urls = load_paper_refs()

    def in_papers(arxiv_id: str, url: str) -> bool:
        return arxiv_id in paper_arxiv_ids or url in paper_urls

    # 1. Drop candidates I have promoted to papers.yaml since the last run.
    promoted = [cid for cid, c in candidates.items()
                if in_papers(cid.removeprefix("arxiv:"), c["url"])]
    for cid in promoted:
        del candidates[cid]

    # 2. Drop candidates older than the retention period.
    oldest_allowed = (today - timedelta(days=retention_days)).date().isoformat()
    expired = [cid for cid, c in candidates.items() if c["detected"] < oldest_allowed]
    for cid in expired:
        del candidates[cid]

    # 3. Add the new papers.
    added = 0
    for paper in new_papers:
        cid = f"arxiv:{paper['arxiv_id']}"
        if cid in candidates or in_papers(paper["arxiv_id"], paper["url"]):
            continue
        candidates[cid] = {
            "id": cid,
            "title": paper["title"],
            "authors": paper["authors"],
            "year": int(paper["published"][:4]),
            "url": paper["url"],
            "abstract": paper["excerpt"],
            "detected": today.date().isoformat(),
            "topics": paper["topics"],
        }
        added += 1

    # Newest first, so the file reads top-down like an inbox.
    ordered = dict(sorted(candidates.items(),
                          key=lambda kv: (kv[1]["detected"], kv[0]), reverse=True))
    counters = {"added": added, "removed_promoted": len(promoted),
                "pruned": len(expired), "total": len(ordered)}
    return ordered, counters


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_feed(url: str, config: dict) -> int:
    """Try one feed URL the way the daily run would, and report. Writes nothing.

    Used to test a new source (or one that fails from one network, like
    DeepMind's own feed from my work computer) before adding it to
    config/sources.yaml. From GitHub Actions: "Run workflow" with the
    `check_feed` field filled in.
    """
    settings = config["settings"]
    session = requests.Session()
    session.headers["User-Agent"] = settings["user_agent"]
    now = datetime.now(timezone.utc)
    source = {"id": "check", "name": "check", "url": url, "require_topic": True}
    try:
        kept, total = fetch_feed(source, session, settings, TopicMatcher(config["topics"]),
                                 now - timedelta(days=settings["max_age_days"]), now)
    except Exception as exc:  # noqa: BLE001 - report any failure, it's a check
        print(f"FEED CHECK FAILED for {url}: {type(exc).__name__}: {exc}")
        return 1
    print(f"FEED CHECK OK: {url}")
    print(f"  {total} items in the feed; {len(kept)} from the last "
          f"{settings['max_age_days']} days that match a topic (require_topic).")
    for entry in kept[:5]:
        print(f"  - {entry['published'][:10]}  {entry['title']}  [{', '.join(entry['topics'])}]")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch and report, but do not write any file")
    parser.add_argument("--check-feed", metavar="URL",
                        help="only try this one feed URL and report (writes nothing)")
    args = parser.parse_args()

    # Titles contain all kinds of characters; the Windows console may not.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    started = time.monotonic()
    config = load_yaml(CONFIG_FILE)
    if args.check_feed:
        return check_feed(args.check_feed, config)
    settings = config["settings"]
    matcher = TopicMatcher(config["topics"])
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=settings["max_age_days"])

    session = requests.Session()
    session.headers["User-Agent"] = settings["user_agent"]

    # --- 1. Fetch every source; one failure never stops the others ---------
    fetched: list[tuple[dict, list[dict]]] = []
    statuses = []
    jobs = [(s, fetch_feed, s) for s in config["sources"]]
    if config.get("arxiv", {}).get("enabled"):
        jobs.append((ARXIV_SOURCE, fetch_arxiv, config["arxiv"]))

    for source, fetch, source_config in jobs:
        status = {"id": source["id"], "name": source["name"], "status": "ok",
                  "items_in_feed": 0, "kept": 0, "new": 0, "error": None}
        try:
            entries, total = fetch(source_config, session, settings, matcher, cutoff, now)
            status.update(items_in_feed=total, kept=len(entries))
            fetched.append((source, entries))
            log.info("ok    %-22s %3d in feed, %3d kept", source["id"], total, len(entries))
        except Exception as exc:  # noqa: BLE001 - any failure is recorded, not fatal
            status.update(status="error", error=f"{type(exc).__name__}: {exc}")
            log.warning("ERROR %-22s %s", source["id"], status["error"])
        statuses.append(status)

    # --- 2. Merge into the monthly files, skipping duplicates ---------------
    news = load_news()
    seen = SeenIndex({s["id"] for s in config["sources"] if s.get("crossposts")})
    for month in news.values():
        for e in month:
            seen.add(e)
    new_by_source: dict[str, int] = {}
    new_papers = []
    changed_months = set()
    for source, entries in fetched:
        for entry in entries:
            if seen.is_duplicate(entry):
                continue
            seen.add(entry)
            month = entry["published"][:7]
            news.setdefault(month, []).append(entry)
            changed_months.add(month)
            new_by_source[source["id"]] = new_by_source.get(source["id"], 0) + 1
            if source is ARXIV_SOURCE:
                new_papers.append(entry)
    for status in statuses:
        status["new"] = new_by_source.get(status["id"], 0)
    total_new = sum(new_by_source.values())

    # --- 3. Paper candidates -----------------------------------------------
    candidates, candidate_counts = update_candidates(
        new_papers, now, config["candidates"]["retention_days"])

    # --- 4. Status ------------------------------------------------------------
    status_doc = {
        "last_run": to_iso(now),
        "duration_seconds": round(time.monotonic() - started, 1),
        "new_entries": total_new,
        "sources": statuses,
        "candidates": candidate_counts,
    }

    failed = [s["id"] for s in statuses if s["status"] == "error"]
    log.info("\n%d new entries in %s; %d/%d sources failed%s",
             total_new, ", ".join(sorted(changed_months)) or "no month",
             len(failed), len(statuses), f" ({', '.join(failed)})" if failed else "")
    log.info("candidates: %(added)d added, %(removed_promoted)d promoted, "
             "%(pruned)d pruned, %(total)d total", candidate_counts)

    if args.dry_run:
        log.info("--dry-run: nothing written")
    else:
        for month in changed_months:
            entries = sorted(news[month], key=lambda e: (e["published"], e["id"]), reverse=True)
            write_json(NEWS_DIR / f"{month}.json", entries)
        write_json(CANDIDATES_FILE, candidates)
        write_json(STATUS_FILE, status_doc)

    # Exit with an error only if *every* source failed: then something is wrong
    # on our side (network, config) and GitHub should email me.
    return 1 if statuses and len(failed) == len(statuses) else 0


if __name__ == "__main__":
    sys.exit(main())
