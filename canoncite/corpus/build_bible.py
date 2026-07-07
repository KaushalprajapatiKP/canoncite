#!/usr/bin/env python3
"""Reproducible builder for the frozen Bible corpus (CANONCITE).

Produces ``canoncite/data/corpora/bible/corpus_index.jsonl`` -- one JSON object
per atomic citable verse for the full 66-book Protestant canon, plus a
``VALIDATION.md`` report and a version (sha256) line.

Citation ID scheme: ``BOOK chapter:verse`` (e.g. ``John 3:16``).

PUBLIC-DOMAIN source (English only; no original-language layer):

  * World English Bible (WEB) -- a modern English translation explicitly placed
    in the PUBLIC DOMAIN (no copyright; dedicated to the public domain by the
    Rainbow Missions / eBible.org WEB project). Fetched verse-by-verse from the
    getBible v2 open API, which serves the eBible.org ``eng-web`` text as
    structured JSON per book:

        https://api.getbible.net/v2/web/{book_nr}.json   (book_nr = 1..66)

CRITICAL RULE honoured throughout: no verse text is ever invented. Every
``text_en`` value comes from the fetched WEB JSON; if a verse cannot be
retrieved it is left ``null`` and recorded in VALIDATION.md. Where the WEB base
text itself omits a traditional verse number (e.g. Acts 8:37, following the
critical Greek text), that verse simply does not exist in the corpus and the
gap is reported honestly in VALIDATION.md -- nothing is fabricated to fill it.

Re-runnable: fetches into raw/ only if the cache is absent (use --refetch to
force), then parses from cache -> deterministic output.

Usage:
    python canoncite/corpus/build_bible.py            # build from cache (fetch if missing)
    python canoncite/corpus/build_bible.py --refetch  # re-download all 66 books
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # canoncite/
DATA = ROOT / "data" / "corpora" / "bible"
RAW = DATA / "raw"
GETBIBLE_DIR = RAW / "getbible"
OUT_JSONL = DATA / "corpus_index.jsonl"
VALIDATION = DATA / "VALIDATION.md"

RETRIEVED = "2026-06-30"
UA = "CanonciteCorpusBuilder/1.0 (research; public-domain corpus build)"
TRANSLATION_SOURCE = "WEB"

SOURCE_API = "https://api.getbible.net/v2/web/{nr}.json"
SOURCE_HOME = "https://getbible.net/"
WEB_HOME = "https://worldenglish.bible/"

# 66-book Protestant canon in canonical order.
#   (book_nr, canonical_name, expected_chapter_count)
# canonical_name is the normalized citation spelling used in `id` and `book`.
# book_nr matches the getBible v2 / standard Protestant ordinal (1..66).
BOOKS: list[tuple[int, str, int]] = [
    (1, "Genesis", 50), (2, "Exodus", 40), (3, "Leviticus", 27),
    (4, "Numbers", 36), (5, "Deuteronomy", 34), (6, "Joshua", 24),
    (7, "Judges", 21), (8, "Ruth", 4), (9, "1 Samuel", 31),
    (10, "2 Samuel", 24), (11, "1 Kings", 22), (12, "2 Kings", 25),
    (13, "1 Chronicles", 29), (14, "2 Chronicles", 36), (15, "Ezra", 10),
    (16, "Nehemiah", 13), (17, "Esther", 10), (18, "Job", 42),
    (19, "Psalms", 150), (20, "Proverbs", 31), (21, "Ecclesiastes", 12),
    (22, "Song of Solomon", 8), (23, "Isaiah", 66), (24, "Jeremiah", 52),
    (25, "Lamentations", 5), (26, "Ezekiel", 48), (27, "Daniel", 12),
    (28, "Hosea", 14), (29, "Joel", 3), (30, "Amos", 9),
    (31, "Obadiah", 1), (32, "Jonah", 4), (33, "Micah", 7),
    (34, "Nahum", 3), (35, "Habakkuk", 3), (36, "Zephaniah", 3),
    (37, "Haggai", 2), (38, "Zechariah", 14), (39, "Malachi", 4),
    (40, "Matthew", 28), (41, "Mark", 16), (42, "Luke", 24),
    (43, "John", 21), (44, "Acts", 28), (45, "Romans", 16),
    (46, "1 Corinthians", 16), (47, "2 Corinthians", 13), (48, "Galatians", 6),
    (49, "Ephesians", 6), (50, "Philippians", 4), (51, "Colossians", 4),
    (52, "1 Thessalonians", 5), (53, "2 Thessalonians", 3), (54, "1 Timothy", 6),
    (55, "2 Timothy", 4), (56, "Titus", 3), (57, "Philemon", 1),
    (58, "Hebrews", 13), (59, "James", 5), (60, "1 Peter", 5),
    (61, "2 Peter", 3), (62, "1 John", 5), (63, "2 John", 1),
    (64, "3 John", 1), (65, "Jude", 1), (66, "Revelation", 22),
]

# getBible labels a couple of books slightly differently from the canonical
# citation spelling; record the accepted source-side aliases for cross-check.
NAME_ALIASES = {
    "Song of Solomon": {"Song of Solomon", "Song of Songs"},
}


# ---------------------------------------------------------------------------
# Fetching (only when cache missing)
# ---------------------------------------------------------------------------
def _get(url: str, timeout: int = 40) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_books(refetch: bool = False) -> None:
    GETBIBLE_DIR.mkdir(parents=True, exist_ok=True)
    for nr, name, _ in BOOKS:
        dst = GETBIBLE_DIR / f"web_{nr:02d}.json"
        if dst.exists() and not refetch:
            continue
        url = SOURCE_API.format(nr=nr)
        for attempt in range(4):
            try:
                data = _get(url)
                # sanity: must be valid JSON with a chapters array
                obj = json.loads(data)
                if obj.get("chapters"):
                    dst.write_bytes(data)
                    print(f"[fetch] {name} (book {nr}) -> {dst}")
                    break
            except Exception as e:  # noqa: BLE001
                print(f"[warn] book {nr} ({name}) attempt {attempt}: {e}")
            time.sleep(5)
        else:
            raise RuntimeError(f"could not fetch WEB book {nr} ({name})")
        time.sleep(0.5)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
_WS = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Collapse whitespace (WEB poetry lines carry leading-indent spaces) and
    strip; never alter the words themselves."""
    return _WS.sub(" ", text.replace("\xa0", " ")).strip()


def load_book(nr: int) -> dict:
    return json.loads((GETBIBLE_DIR / f"web_{nr:02d}.json").read_text("utf-8"))


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build_records() -> tuple[list[dict], dict]:
    """Return (records, parsed_struct). parsed_struct maps
    nr -> {"name": src_name, "chapters": {ch: [verse_numbers...]}}."""
    records: list[dict] = []
    parsed: dict[int, dict] = {}
    for nr, name, _exp_ch in BOOKS:
        d = load_book(nr)
        src_name = d.get("name", "")
        chapters: dict[int, list[int]] = {}
        url = SOURCE_API.format(nr=nr)
        for c in d["chapters"]:
            ch = int(c["chapter"])
            vnums = []
            for v in c["verses"]:
                vn = int(v["verse"])
                vnums.append(vn)
                text = clean_text(v.get("text", ""))
                records.append({
                    "corpus": "bible",
                    "id": f"{name} {ch}:{vn}",
                    "unit": "verse",
                    "book": name,
                    "chapter": ch,
                    "verse": vn,
                    "text_en": text if text else None,
                    "translation_source": TRANSLATION_SOURCE if text else None,
                    "source_urls": {"en": url},
                    "retrieved": RETRIEVED,
                    "tokens": len(text.split()) if text else 0,
                })
            chapters[ch] = sorted(vnums)
        parsed[nr] = {"name": src_name, "chapters": chapters}
    return records, parsed


# sort key: canonical book order, then chapter, then verse
_ORDER = {name: nr for nr, name, _ in BOOKS}


def _sort_key(r: dict) -> tuple[int, int, int]:
    return (_ORDER[r["book"]], r["chapter"], r["verse"])


def write_jsonl(records: list[dict]) -> str:
    ordered = sorted(records, key=_sort_key)
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in ordered]
    blob = "\n".join(lines) + "\n"
    OUT_JSONL.write_text(blob, encoding="utf-8")
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------
SPOT = ["John 3:16", "Genesis 1:1", "Psalms 23:1", "Revelation 22:21",
        "Romans 8:28"]


def detect_gaps(chapters: dict[int, list[int]]) -> list[tuple[int, list[int]]]:
    """Return [(chapter, [missing verse numbers])] where verse numbering is not
    a contiguous 1..max run -- i.e. WEB omits a traditional verse number."""
    out = []
    for ch in sorted(chapters):
        vs = chapters[ch]
        if not vs:
            out.append((ch, []))
            continue
        expect = set(range(1, max(vs) + 1))
        missing = sorted(expect - set(vs))
        if missing:
            out.append((ch, missing))
    return out


def write_validation(records: list[dict], parsed: dict, sha: str) -> None:
    by_id = {r["id"]: r for r in records}
    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])
    missing_en = [r["id"] for r in records if not r["text_en"]]

    L: list[str] = []
    L.append("# VALIDATION -- Bible corpus (CANONCITE)\n")
    L.append(f"Generated by `canoncite/corpus/build_bible.py`. Retrieved: **{RETRIEVED}**.\n")
    L.append(f"**version (sha256 of sorted corpus_index.jsonl):** `{sha}`\n")

    L.append("## Sources (public-domain only)\n")
    L.append("| Field | Source | URL |")
    L.append("|---|---|---|")
    L.append("| text_en | World English Bible (WEB) -- modern English translation, "
             "**explicitly PUBLIC DOMAIN** (no copyright) | "
             f"{WEB_HOME} |")
    L.append("| machine-readable delivery | getBible v2 open API, serving the eBible.org "
             "`eng-web` WEB text as structured per-book JSON | "
             f"{SOURCE_API.format(nr='{1..66}')} |")
    L.append("")
    L.append("- **Canon:** 66-book Protestant canon, English only (no original-language layer).")
    L.append("- **ID scheme:** `BOOK chapter:verse` (e.g. `John 3:16`), book name normalized to "
             "the canonical citation spelling (e.g. `1 Corinthians`, `Psalms`, `Song of Solomon`).")
    L.append("- **Book order:** recorded in the canonical-order table below (ordinal 1..66).\n")

    # --- per-book table ---
    L.append("## Coverage summary\n")
    L.append(f"- Total citable verses (ID space `U`): **{total}**")
    L.append(f"- English (WEB) coverage: **{with_en}/{total} = {100*with_en/total:.2f}%**")
    L.append(f"- Verses missing text (flagged null): {missing_en or 'none'}")
    L.append(f"- Books sourced: **{len(BOOKS)}/66 = 100.00%** (no book unsourced)\n")

    L.append("## Per-book canon check (chapter count) and verse coverage\n")
    L.append("| # | Book | Exp. ch | Parsed ch | Verses | Source name | Status |")
    L.append("|---:|---|---:|---:|---:|---|---|")
    all_gaps: list[str] = []
    chap_problems = 0
    for nr, name, exp_ch in BOOKS:
        p = parsed[nr]
        chapters = p["chapters"]
        parsed_ch = len(chapters)
        vcount = sum(len(v) for v in chapters.values())
        flags = []
        if parsed_ch != exp_ch:
            flags.append(f"CHAPTERS {parsed_ch}!={exp_ch}")
            chap_problems += 1
        # name cross-check
        accepted = NAME_ALIASES.get(name, {name})
        if p["name"] not in accepted:
            flags.append(f"src-name '{p['name']}'")
        gaps = detect_gaps(chapters)
        for ch, miss in gaps:
            for m in miss:
                all_gaps.append(f"{name} {ch}:{m}")
        if gaps:
            flags.append(f"{sum(len(m) for _, m in gaps)} verse-gap(s)")
        status = "ok" if not flags else "; ".join(flags)
        srcn = p["name"] if p["name"] != name else "(same)"
        L.append(f"| {nr} | {name} | {exp_ch} | {parsed_ch} | {vcount} | {srcn} | {status} |")
    L.append(f"| | **TOTAL** | **{sum(b[2] for b in BOOKS)}** | "
             f"**{sum(len(parsed[nr]['chapters']) for nr,_,_ in BOOKS)}** | "
             f"**{total}** | | |")
    L.append("")
    L.append(f"All 66 books parsed with the expected chapter count "
             f"({'no discrepancies' if chap_problems == 0 else f'{chap_problems} discrepancies'}).\n")

    # --- gaps / omitted verses ---
    L.append("## WEB textual omissions (verse-number gaps)\n")
    L.append("These traditional verse numbers are **absent from the WEB base text itself** "
             "(WEB follows the modern critical text, which drops them or relegates them to "
             "footnotes). They are not citable in this corpus. Reported here for honesty; "
             "**no text was fabricated to fill them**:\n")
    if all_gaps:
        for g in all_gaps:
            L.append(f"- `{g}` -- not present in WEB")
    else:
        L.append("- none detected")
    L.append("")
    L.append(f"Total verse-number gaps: **{len(all_gaps)}**. This is why the WEB verse total "
             f"(**{total}**) is slightly below the ~31,100 traditional (KJV-numbering) count; "
             "the difference is accounted for entirely by the omissions listed above plus "
             "minor versification differences in the WEB edition.\n")

    # --- spot check ---
    L.append("## Content spot-check (actual fetched text -- verify nothing was fabricated)\n")
    for sid in SPOT:
        r = by_id.get(sid)
        if not r:
            L.append(f"### {sid}\n_NOT FOUND_\n")
            continue
        L.append(f"### {sid}  (book {r['book']}, chapter {r['chapter']}, "
                 f"verse {r['verse']}, tokens={r['tokens']})\n")
        L.append(f"- **text_en (WEB):** {r['text_en']}\n")

    VALIDATION.write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refetch", action="store_true", help="re-download all 66 books")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    fetch_books(args.refetch)

    records, parsed = build_records()
    sha = write_jsonl(records)
    write_validation(records, parsed, sha)

    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])
    print(f"[done] {total} verses -> {OUT_JSONL}")
    print(f"[done] English coverage {with_en}/{total} = {100*with_en/total:.2f}%")
    print(f"[done] version sha256 = {sha}")
    print(f"[done] validation -> {VALIDATION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
