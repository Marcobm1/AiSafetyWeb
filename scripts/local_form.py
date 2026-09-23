"""The local "Add entry" form for My Own Path (preview only, never published).

Only `build_site.py --serve` loads this module. It adds one page to the local
preview server, /AiSafetyWeb/_local/add-entry/, generated in memory: it is
never written to _site/ (and build_site.check_no_local_tools() fails the
build if its markers ever appear there).

What it does:
  1. Shows a form for a new Timeline stage (course, project, milestone) or a
     new Journal entry (paper, essay, report, article, book, resource,
     podcast-video), with the fields of each type.
  2. Validates it with the SAME functions the build uses
     (check_timeline_item / check_log_entry), and shows every problem next
     to its field. Nothing is saved while there is a problem.
  3. Saves it by INSERTING text into the YAML file (the file is never
     re-dumped, so my comments stay), validates the whole new file, and only
     then replaces the old one. Timeline: appended at the end of
     timeline.yaml. Journal: inserted right under `entries:` in
     reading_log.yaml (newest at the top, like the rest of the file).
  4. Rebuilds the preview and shows which file changed and the block added.
     It never commits or pushes.

Protections (the server only listens on 127.0.0.1, and on top of that):
  - Host check: requests to the form must say Host: 127.0.0.1:<port> or
    localhost:<port>. That defeats DNS rebinding (a web page whose domain
    suddenly resolves to 127.0.0.1 would still send its own domain as Host).
  - Origin check: a save must come from http://127.0.0.1:<port> or
    http://localhost:<port> (Origin header, or Referer if there's no Origin),
    so another website open in my browser can't post to the form.
  - A random token, new every time the server starts, must come back with
    every save.
  - Small request limit (64 KB), no caching, and the page can't be framed.
"""

from __future__ import annotations

import html
import json
import os
import re
import secrets
import textwrap
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import yaml

FORM_PATH = "_local/add-entry/"
MAX_BODY = 64 * 1024

# Field order in the YAML files (the same order as the existing entries).
TIMELINE_KEYS = ("id", "type", "date", "completed", "title", "provider", "url", "status", "notes")
JOURNAL_KEYS = ("month", "type", "status", "started", "paper_ref", "book_ref", "title",
                "author", "source", "url", "archive_url", "via", "cover_id", "notes")
QUOTED = {"title", "author", "source", "provider", "month", "started"}


# ---------------------------------------------------------------------------
# Turning the form into YAML text
# ---------------------------------------------------------------------------

def yaml_scalar(key: str, value) -> str:
    """One value as YAML. Texts and months always in double quotes (JSON strings
    are valid YAML), numbers and dates bare, the rest (ids, URLs) plain unless
    YAML needs quotes."""
    if isinstance(value, int):
        return str(value)
    if key in ("date", "completed"):
        return value   # already validated as YYYY-MM-DD; bare, so YAML reads it as a date
    if key in QUOTED:
        return json.dumps(value, ensure_ascii=False)
    return yaml.safe_dump([value], allow_unicode=True, width=10**6)[2:].rstrip("\n")


def yaml_block(entry: dict, keys: tuple, indent: int) -> str:
    """The entry as a YAML list item, e.g. '  - month: "2026-09"\\n    type: essay\\n'."""
    pad = " " * indent
    lines = []
    for key in keys:
        if key not in entry:
            continue
        prefix = f"{pad}- " if not lines else f"{pad}  "
        if key == "notes":
            # A folded block (>): long text wrapped at ~76 columns, paragraphs kept.
            lines.append(f"{prefix}notes: >")
            paragraphs = [p for p in re.split(r"\n\s*\n", entry["notes"].strip()) if p.strip()]
            for i, paragraph in enumerate(paragraphs):
                if i:
                    lines.append("")
                lines += textwrap.wrap(" ".join(paragraph.split()), 76 - indent - 4,
                                       initial_indent=pad + "    ", subsequent_indent=pad + "    ")
        else:
            lines.append(f"{prefix}{key}: {yaml_scalar(key, entry[key])}")
    return "\n".join(lines) + "\n"


def insert_timeline(text: str, block: str) -> str:
    """timeline.yaml is a list: the new stage goes at the end."""
    return text.rstrip("\n") + "\n\n" + block


def insert_journal(text: str, block: str) -> str:
    """reading_log.yaml: the new entry goes right under `entries:`."""
    match = re.search(r"^entries:[ \t]*\n", text, re.M)
    if not match:
        raise ValueError("reading_log.yaml has no `entries:` line")
    return text[:match.end()] + "\n" + block + text[match.end():]


# ---------------------------------------------------------------------------
# The form
# ---------------------------------------------------------------------------

class LocalForm:
    def __init__(self, bs, base_path: str, port: int):
        self.bs = bs                    # the build_site module (its loaders, validators, build)
        self.base_path = base_path
        self.path = base_path + FORM_PATH
        self.port = port
        self.token = secrets.token_urlsafe(32)
        self.hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        self.origins = {f"http://{h}" for h in self.hosts}

    # --- request checks -------------------------------------------------------

    def host_ok(self, handler) -> bool:
        return handler.headers.get("Host", "") in self.hosts

    def origin_ok(self, handler) -> bool:
        origin = handler.headers.get("Origin")
        if origin:
            return origin in self.origins
        referer = urlsplit(handler.headers.get("Referer", ""))
        return f"{referer.scheme}://{referer.netloc}" in self.origins

    def refuse(self, handler, code: int, message: str) -> None:
        body = message.encode("utf-8")
        handler.send_response(code)
        handler.send_header("Content-Type", "text/plain; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def send_page(self, handler, page: str, code: int = 200) -> None:
        body = page.encode("utf-8")
        handler.send_response(code)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("X-Frame-Options", "DENY")
        handler.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        handler.send_header("Referrer-Policy", "same-origin")
        handler.end_headers()
        handler.wfile.write(body)

    # --- data the form needs --------------------------------------------------

    def load_context(self):
        bs = self.bs
        site = bs.load_site_config()
        sources = bs.load_yaml(bs.SOURCES_CONFIG)
        papers, _ = bs.load_papers(set(sources["topics"]))
        books = [b for shelf in bs.load_books() for b in shelf["books"]]
        today = bs.dt.datetime.now(bs.timezone.utc).date()
        timeline = bs.load_timeline(today)
        return site, papers, books, timeline, today

    def render(self, handler, values=None, errors=None, saved=None, fatal=None, code=200):
        bs = self.bs
        site, papers, books, timeline, _ = self.load_context()
        env = bs.make_env(site, bs.load_json(bs.STATUS_FILE, {}))
        page = env.get_template("local/add_entry.html").render(
            current_path=FORM_PATH, token=self.token, form_action=self.path,
            values=values or {}, errors=errors or {}, saved=saved, fatal=fatal,
            timeline_choices=[(t["id"], t["title"]) for t in timeline],
            paper_choices=[(p["id"], p["title"]) for p in papers],
            book_choices=[(b["id"], b["title"]) for b in books],
            kinds=self.kinds(),
        )
        self.send_page(handler, page, code)

    def kinds(self):
        bs = self.bs
        return ([("timeline:" + k, "Timeline · " + v) for k, v in bs.TIMELINE_TYPES.items()]
                + [("journal:" + k, "Journal · " + v) for k, v in bs.READING_TYPES.items()])

    # --- GET / POST -----------------------------------------------------------

    def handle_get(self, handler) -> None:
        if not self.host_ok(handler):
            return self.refuse(handler, 403, "Forbidden: wrong Host header (local form only).")
        self.render(handler)

    def handle_post(self, handler) -> None:
        if not self.host_ok(handler):
            return self.refuse(handler, 403, "Forbidden: wrong Host header (local form only).")
        if not self.origin_ok(handler):
            return self.refuse(handler, 403, "Forbidden: the request did not come from this preview.")
        if handler.headers.get_content_type() != "application/x-www-form-urlencoded":
            return self.refuse(handler, 415, "Unsupported form encoding.")
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if not 0 < length <= MAX_BODY:
            return self.refuse(handler, 413, "Request too large (or empty).")
        fields = parse_qs(handler.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        values = {k: v[0].strip() for k, v in fields.items()}
        if not secrets.compare_digest(values.get("token", ""), self.token):
            return self.refuse(handler, 403, "Forbidden: the form token is missing or old. Reload the form.")
        self.save(handler, values)

    # --- validate and save ----------------------------------------------------

    def entry_from(self, values: dict) -> tuple[str, dict, dict]:
        """(target, entry for the YAML, field name map yaml key -> form field)."""
        target, _, kind = values.get("kind", "").partition(":")
        entry, names = {}, {}
        if target == "timeline":
            for key in TIMELINE_KEYS:
                field = "t_" + key
                names[key] = field
                if key == "type":
                    entry["type"] = kind
                elif values.get(field):
                    entry[key] = values[field] if key == "notes" else " ".join(values[field].split())
        else:
            is_book = kind == "book"
            for key in JOURNAL_KEYS:
                field = "j_" + key
                names[key] = field
                if key == "type":
                    entry["type"] = kind
                elif key in ("status", "started", "cover_id", "book_ref") and not is_book:
                    continue   # book-only fields are ignored for other types
                elif key == "paper_ref" and is_book:
                    continue
                elif values.get(field):
                    value = values[field] if key == "notes" else " ".join(values[field].split())
                    entry[key] = int(value) if key == "cover_id" and value.isdigit() else value
        names["type"] = "kind"
        return target, entry, names

    def save(self, handler, values: dict) -> None:
        bs = self.bs
        target, entry, names = self.entry_from(values)
        if target not in ("timeline", "journal"):
            return self.render(handler, values, {"kind": ["Choose what to add."]}, code=400)
        try:
            site, papers, books, timeline, today = self.load_context()
        except bs.BuildError as exc:
            return self.render(handler, values, fatal=f"The current data doesn't build: {exc}", code=500)

        problems = bs.Problems("new entry")
        if target == "timeline":
            bs.check_timeline_item(entry, {t["id"] for t in timeline}, problems)
            path, keys, indent, insert = bs.TIMELINE_FILE, TIMELINE_KEYS, 0, insert_timeline
        else:
            bs.check_log_entry(entry, {t["id"] for t in timeline}, {p["id"] for p in papers},
                               {b["id"] for b in books}, problems)
            if entry.get("paper_ref") or entry.get("book_ref"):
                ref = "paper_ref" if entry.get("paper_ref") else "book_ref"
                for key in ("title", "author", "source", "url"):
                    if entry.get(key):
                        problems.add(key, f"leave {key} empty: with {ref} it comes from "
                                          f"{'papers.yaml' if ref == 'paper_ref' else 'books.yaml'}")
            path, keys, indent, insert = bs.READING_LOG_FILE, JOURNAL_KEYS, 2, insert_journal
        if problems:
            errors: dict[str, list[str]] = {}
            for key, message in problems.items:
                errors.setdefault(names.get(key, key), []).append(message)
            return self.render(handler, values, errors, code=400)

        block = yaml_block(entry, keys, indent)
        old_text = path.read_text(encoding="utf-8")
        new_text = insert(old_text, block)

        # Validate the WHOLE new file before replacing the real one.
        tmp = path.with_name(path.name + ".new.tmp")
        tmp.write_text(new_text, encoding="utf-8", newline="\n")
        try:
            if target == "timeline":
                new_timeline = bs.load_timeline(today, path=tmp)
                bs.load_reading_log(new_timeline, papers, books)
            else:
                bs.load_reading_log(timeline, papers, books, path=tmp)
        except (bs.BuildError, yaml.YAMLError) as exc:
            tmp.unlink(missing_ok=True)
            return self.render(handler, values, fatal=f"Not saved: the file would not be valid ({exc}).", code=400)
        os.replace(tmp, path)

        relative = path.relative_to(bs.ROOT).as_posix()
        try:
            bs.build()
            rebuilt = "The preview has been rebuilt."
        except bs.BuildError as exc:
            rebuilt = f"Saved, but the rebuild failed: {exc}"
        self.render(handler, saved={
            "file": relative,
            "where": "at the end of the file" if target == "timeline" else "right under `entries:`",
            "block": block,
            "rebuilt": rebuilt,
            "anchor": (f"my-path/#timeline-{entry['id']}" if target == "timeline"
                       else f"my-path/#journal-{entry['month']}" if entry.get("month") else "my-path/#bookshelf"),
        })

    # --- the link on My Own Path ------------------------------------------------

    def link_html(self) -> str:
        return (f'<p class="local-tools" data-local-only>Local preview only: '
                f'<a href="{html.escape(self.path)}">Add entry</a> '
                f'<span class="note">(not on the published site)</span></p>\n')

    def inject_link(self, page: str) -> str:
        marker = '<nav class="toc"'
        return page.replace(marker, self.link_html() + marker, 1) if marker in page else page
