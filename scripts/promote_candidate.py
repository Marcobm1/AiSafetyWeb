"""Promote an arXiv paper candidate into data/papers.yaml.

It copies the candidate's verified data (title, authors, year, URL, arXiv id,
topics) from data/paper_candidates.json into a new block at the end of
data/papers.yaml. The fields only I can fill in are left as TODO, so the build
does not publish the entry until I have written them:
  - synopsis    2-4 neutral sentences in my own words (not the abstract)
  - difficulty  intro | intermediate | advanced
  - tags        only if the candidate had no topics

The block is appended as plain text instead of loading and re-saving the YAML
file, because re-saving with PyYAML would delete every comment in it. That is
why `entries` must stay the last key of data/papers.yaml.

Usage (from the repository root, with the venv active):
    python scripts/promote_candidate.py arxiv:2401.05566
    python scripts/promote_candidate.py 2401.05566 --id sleeper-agents
    python scripts/promote_candidate.py arxiv:2401.05566 --dry-run   # only print the block
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

import yaml

from fetch_news import CANDIDATES_FILE, PAPERS_FILE, ROOT, load_json, normalize_url

BOOKS_FILE = ROOT / "data" / "books.yaml"
PAPER_TYPES = ("paper", "essay", "report", "scenario", "blog-post")
SLUG_MAX_WORDS = 5
# Words left out of generated ids, so they stay short and meaningful.
SLUG_STOPWORDS = {"a", "an", "the", "of", "for", "and", "or", "in", "on", "to",
                  "with", "via", "from", "by", "is", "are", "do", "does", "can", "towards"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PromoteError(Exception):
    """Something that stops the promotion; nothing has been written."""


def load_entries(path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("entries") or []


def make_slug(title: str, taken: set[str]) -> str:
    """'Sleeper Agents: Training Deceptive LLMs...' -> 'sleeper-agents-training-deceptive-llms'."""
    words = [w for w in re.sub(r"[^a-z0-9]+", " ", title.lower()).split()
             if w not in SLUG_STOPWORDS]
    slug = "-".join(words[:SLUG_MAX_WORDS]) or "paper"
    candidate, n = slug, 2
    while candidate in taken:
        candidate, n = f"{slug}-{n}", n + 1
    return candidate


def yaml_str(value) -> str:
    """A value as YAML text. JSON strings and lists are valid YAML, and quoting
    avoids surprises with titles containing ':' or '#'."""
    return json.dumps(value, ensure_ascii=False)


def build_block(candidate: dict, slug: str, paper_type: str, today: str) -> str:
    authors = candidate["authors"]
    if len(authors) > 3:
        authors = authors[:3] + ["et al."]
    arxiv_id = candidate["id"].removeprefix("arxiv:")
    tags = ", ".join(candidate.get("topics") or []) or "TODO"
    return (
        f"  - id: {slug}\n"
        f"    title: {yaml_str(candidate['title'])}\n"
        f"    authors: {yaml_str(authors)}\n"
        f"    year: {int(candidate['year'])}\n"
        f"    type: {paper_type}\n"
        f"    url: {candidate['url']}\n"
        f"    arxiv_id: {yaml_str(arxiv_id)}\n"
        f"    tags: [{tags}]   # alignment | interpretability | evals | governance | security\n"
        f"    difficulty: TODO   # intro | intermediate | advanced\n"
        f"    synopsis: >\n"
        f"      TODO: 2-4 neutral sentences in my own words, after reading the paper.\n"
        f"    added: {today}\n"
    )


def promote(candidate_id: str, slug: str | None, paper_type: str, dry_run: bool) -> str:
    if not candidate_id.startswith("arxiv:"):
        candidate_id = "arxiv:" + candidate_id
    candidates = load_json(CANDIDATES_FILE, {})
    candidate = candidates.get(candidate_id)
    if candidate is None:
        raise PromoteError(f"{candidate_id} is not in {CANDIDATES_FILE.name}. "
                           "Copy the exact \"id\" from that file.")

    papers = load_entries(PAPERS_FILE)
    arxiv_id = candidate_id.removeprefix("arxiv:")
    for entry in papers:
        if str(entry.get("arxiv_id")) == arxiv_id or \
                normalize_url(str(entry.get("url", ""))) == normalize_url(candidate["url"]):
            raise PromoteError(f"already in papers.yaml as '{entry.get('id')}'")

    # Ids are unique across papers.yaml and books.yaml (the reading tracker uses them).
    taken = {str(e.get("id")) for e in papers + load_entries(BOOKS_FILE)}
    if slug is None:
        slug = make_slug(candidate["title"], taken)
    elif not ID_RE.match(slug):
        raise PromoteError(f"--id must be a lowercase slug like 'sleeper-agents', got {slug!r}")
    elif slug in taken:
        raise PromoteError(f"the id '{slug}' is already used")

    block = build_block(candidate, slug, paper_type, date.today().isoformat())
    if dry_run:
        return block

    original = PAPERS_FILE.read_text(encoding="utf-8")
    updated = original.rstrip("\n") + "\n\n" + block
    # Check the result before keeping it: still valid YAML, `entries` still the
    # last key, and the new block really landed as the last entry.
    try:
        data = yaml.safe_load(updated) or {}
    except yaml.YAMLError as exc:
        raise PromoteError(f"the result would not be valid YAML ({exc}); nothing written")
    entries = data.get("entries") or []
    if list(data)[-1:] != ["entries"] or not entries or entries[-1].get("id") != slug:
        raise PromoteError("`entries` is not the last key of papers.yaml, so the block can't "
                           "be appended safely; nothing written")
    tmp = PAPERS_FILE.with_suffix(".yaml.tmp")
    tmp.write_text(updated, encoding="utf-8", newline="\n")
    tmp.replace(PAPERS_FILE)
    return block


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("candidate", help='candidate id, e.g. "arxiv:2401.05566"')
    parser.add_argument("--id", dest="slug", help="id for the new entry (default: from the title)")
    parser.add_argument("--type", default="paper", choices=PAPER_TYPES)
    parser.add_argument("--dry-run", action="store_true", help="print the block, write nothing")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        block = promote(args.candidate, args.slug, args.type, args.dry_run)
    except PromoteError as exc:
        print(f"Not promoted: {exc}", file=sys.stderr)
        return 1

    print(block)
    if args.dry_run:
        print("--dry-run: nothing written")
    else:
        print(f"Appended to {PAPERS_FILE.relative_to(ROOT)}. Next:\n"
              "  1. Check the id (it never changes once published).\n"
              "  2. Write the synopsis and choose the difficulty (and tags if TODO).\n"
              "  3. python scripts/build_site.py  (it skips the entry while any TODO is left)\n"
              "  4. Commit and push. The next fetch drops it from the candidates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
