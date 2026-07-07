#!/usr/bin/env python3
"""Reproducible builder for the frozen Dhammapada corpus (CANONCITE).

Produces ``canoncite/data/corpora/dhammapada/corpus_index.jsonl`` -- one JSON
object per atomic citable verse for the full Dhammapada (26 vaggas / chapters,
423 verses), plus a ``VALIDATION.md`` report and a version (sha256) line.

Public-domain / open sources only:

  * Pali root text (``original``):
        SuttaCentral ``bilara-data`` Mahasangiti edition, root/pli/ms.
        https://github.com/suttacentral/bilara-data  (CC0 -- public domain).
        26 JSON files, one per vagga, e.g. ``dhp1-20_root-pli-ms.json``.
        Each file maps segment ids ``dhpN:M`` -> a line of Pali; segment "0"/
        "0.x" entries are structural headers (collection / vagga / vatthu
        titles) and are skipped. Concatenating the integer segments of ``dhpN``
        reconstructs the full Pali of verse N. The 26 file verse-ranges coincide
        exactly with the canonical vagga boundaries, so chapter number is
        derived from the file a verse came from (no hand-numbering).
        The Pali is romanised (IAST/Latin) at source.

  * English translation (``text_en``):
        F. Max Muller, *The Dhammapada*, Sacred Books of the East vol. 10
        (Oxford, 1881) -- PUBLIC DOMAIN, strictly verse-numbered. The
        machine-readable copy is Project Gutenberg ebook #2017
        (https://www.gutenberg.org/files/2017/2017-h/2017-h.htm), whose text is
        Muller's identical SBE vol.10 translation. Each verse is an HTML <p>
        beginning with its number ("1.", "2." ...). Muller prints nine couplets
        under a shared double number ("58, 59." etc.); both verse ids then carry
        that shared text (recorded in VALIDATION.md). The canonical sacred-texts
        SBE10 pages (https://sacred-texts.com/bud/sbe10/) are the same text but
        block automated fetching, so Gutenberg #2017 is used as the copy.

CRITICAL RULE honoured throughout: no verse text is ever invented. Every
``text_en`` / ``original`` value comes from a fetched source; verses that cannot
be retrieved/aligned are left null and recorded in VALIDATION.md.

Re-runnable: fetches into raw/ only if the cache is absent (use --refetch to
force), then parses from cache -> deterministic output.

Usage:
    python canoncite/corpus/build_dhammapada.py            # build from cache
    python canoncite/corpus/build_dhammapada.py --refetch  # re-download sources
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # canoncite/
DATA = ROOT / "data" / "corpora" / "dhammapada"
RAW = DATA / "raw"
PALI_DIR = RAW / "pali"
OUT_JSONL = DATA / "corpus_index.jsonl"
VALIDATION = DATA / "VALIDATION.md"

RETRIEVED = "2026-06-30"
UA = "CanonciteCorpusBuilder/1.0 (research; public-domain corpus build)"

TRANSLATION_SOURCE = "Muller_SBE_1881"
ORIGINAL_SOURCE = "SuttaCentral"

# --- Pali source (SuttaCentral bilara-data, root/pli/ms, CC0) ---------------
BILARA_BASE = ("https://raw.githubusercontent.com/suttacentral/bilara-data/"
               "published/root/pli/ms/sutta/kn/dhp/")
BILARA_REPO = "https://github.com/suttacentral/bilara-data"

# The 26 vagga files in canonical order: (chapter, start, end, filename,
# pali_title, en_title). Ranges coincide with the file names; they also serve
# as the verse->chapter map and a per-chapter count cross-check (sum == 423).
CHAPTERS = [
    (1,  1,  20,  "dhp1-20",    "Yamakavagga",        "The Twin-Verses"),
    (2,  21, 32,  "dhp21-32",   "Appamadavagga",      "On Earnestness"),
    (3,  33, 43,  "dhp33-43",   "Cittavagga",         "Thought"),
    (4,  44, 59,  "dhp44-59",   "Pupphavagga",        "Flowers"),
    (5,  60, 75,  "dhp60-75",   "Balavagga",          "The Fool"),
    (6,  76, 89,  "dhp76-89",   "Panditavagga",       "The Wise Man"),
    (7,  90, 99,  "dhp90-99",   "Arahantavagga",      "The Venerable (Arhat)"),
    (8,  100,115, "dhp100-115", "Sahassavagga",       "The Thousands"),
    (9,  116,128, "dhp116-128", "Papavagga",          "Evil"),
    (10, 129,145, "dhp129-145", "Dandavagga",         "Punishment"),
    (11, 146,156, "dhp146-156", "Jaravagga",          "Old Age"),
    (12, 157,166, "dhp157-166", "Attavagga",          "Self"),
    (13, 167,178, "dhp167-178", "Lokavagga",          "The World"),
    (14, 179,196, "dhp179-196", "Buddhavagga",        "The Buddha (The Awakened)"),
    (15, 197,208, "dhp197-208", "Sukhavagga",         "Happiness"),
    (16, 209,220, "dhp209-220", "Piyavagga",          "Pleasure"),
    (17, 221,234, "dhp221-234", "Kodhavagga",         "Anger"),
    (18, 235,255, "dhp235-255", "Malavagga",          "Impurity"),
    (19, 256,272, "dhp256-272", "Dhammatthavagga",    "The Just"),
    (20, 273,289, "dhp273-289", "Maggavagga",         "The Way"),
    (21, 290,305, "dhp290-305", "Pakinnakavagga",     "Miscellaneous"),
    (22, 306,319, "dhp306-319", "Nirayavagga",        "The Downward Course"),
    (23, 320,333, "dhp320-333", "Nagavagga",          "The Elephant"),
    (24, 334,359, "dhp334-359", "Tanhavagga",         "Thirst"),
    (25, 360,382, "dhp360-382", "Bhikkhuvagga",       "The Bhikshu (Mendicant)"),
    (26, 383,423, "dhp383-423", "Brahmanavagga",      "The Brahmana (Arhat)"),
]

# --- English source (Max Muller SBE vol.10, 1881; copy = PG ebook #2017) ----
GUTENBERG_URL = "https://www.gutenberg.org/files/2017/2017-h/2017-h.htm"
SACRED_TEXTS_REF = "https://sacred-texts.com/bud/sbe10/"


# ---------------------------------------------------------------------------
# Fetching (only when cache missing)
# ---------------------------------------------------------------------------
def _get(url: str, timeout: int = 40) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_pali(refetch: bool = False) -> None:
    PALI_DIR.mkdir(parents=True, exist_ok=True)
    for (_ch, _s, _e, stem, *_rest) in CHAPTERS:
        fname = f"{stem}_root-pli-ms.json"
        dst = PALI_DIR / fname
        if dst.exists() and not refetch:
            continue
        for attempt in range(4):
            try:
                data = _get(BILARA_BASE + fname)
                json.loads(data)            # validate
                dst.write_bytes(data)
                print(f"[fetch] Pali {fname} -> {dst}")
                break
            except Exception as e:          # noqa: BLE001
                print(f"[warn] {fname} attempt {attempt}: {e}")
                time.sleep(5)
        else:
            raise RuntimeError(f"could not fetch Pali file {fname}")
        time.sleep(1)


def fetch_muller(refetch: bool = False) -> Path:
    dst = RAW / "muller_gutenberg_2017.html"
    if dst.exists() and not refetch:
        return dst
    print(f"[fetch] Muller (Gutenberg #2017) -> {dst}")
    RAW.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(_get(GUTENBERG_URL))
    return dst


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse_pali() -> dict[int, str]:
    """Return {verse_number: full Pali text}. Verse N = concatenated integer
    segments of the bilara keys ``dhpN:M`` (skip structural "0" headers)."""
    out: dict[int, str] = {}
    for (_ch, _s, _e, stem, *_rest) in CHAPTERS:
        path = PALI_DIR / f"{stem}_root-pli-ms.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        segs: dict[int, list[tuple[float, str]]] = {}
        for key, val in data.items():
            m = re.match(r"dhp(\d+):(\d+(?:\.\d+)?)$", key)
            if not m:
                continue
            verse = int(m.group(1))
            seg = float(m.group(2))
            if seg < 1:                     # "0" / "0.x" structural headers
                continue
            segs.setdefault(verse, []).append((seg, val))
        for verse, parts in segs.items():
            parts.sort(key=lambda t: t[0])
            text = " ".join(p[1] for p in parts)
            out[verse] = re.sub(r"\s+", " ", text).strip()
    return out


_PARA = re.compile(r"<p>(.*?)</p>", re.S)
# leading verse number(s): "5." or "58, 59." or "153-154."
_VNUM = re.compile(r"^\s*(\d+(?:\s*[,\-]\s*\d+)*)\s*\.\s*")


def parse_muller(path: Path) -> dict[int, str]:
    """Return {verse_number: English text}. Couplets printed under a shared
    double number assign the same text to both verse numbers."""
    raw = path.read_text(encoding="utf-8")
    out: dict[int, str] = {}
    for chunk in _PARA.findall(raw):
        t = re.sub(r"<[^>]+>", " ", chunk)
        t = html.unescape(t)
        t = re.sub(r"\s+", " ", t).strip()
        m = _VNUM.match(t)
        if not m:
            continue
        nums = [int(x) for x in re.split(r"[,\-]", m.group(1))]
        if not all(1 <= n <= 423 for n in nums):
            continue
        body = t[m.end():].strip()
        if not body:
            continue
        for n in nums:
            out[n] = body
    return out


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def verse_chapter_map() -> dict[int, tuple]:
    m = {}
    for (ch, s, e, _stem, ptitle, etitle) in CHAPTERS:
        for v in range(s, e + 1):
            m[v] = (ch, s, ptitle, etitle)
    return m


def build_records(pali: dict[int, str], muller: dict[int, str]) -> list[dict]:
    vmap = verse_chapter_map()
    file_of = {ch: stem for (ch, _s, _e, stem, *_r) in CHAPTERS}
    records = []
    for v in range(1, 424):
        ch, start, _pt, _et = vmap[v]
        local = v - start + 1
        en = muller.get(v)
        pl = pali.get(v)
        records.append({
            "corpus": "dhammapada",
            "id": f"{ch}.{local}",
            "unit": "verse",
            "chapter": ch,
            "verse": local,
            "global_verse": v,
            "text_en": en,
            "original": pl,
            "transliteration": None,        # Pali already romanised (IAST) at source
            "translation_source": TRANSLATION_SOURCE if en else None,
            "original_source": ORIGINAL_SOURCE if pl else None,
            "tokens": len(en.split()) if en else 0,
            "source_urls": {
                "en": GUTENBERG_URL if en else None,
                "en_canonical_ref": SACRED_TEXTS_REF,
                "original": (BILARA_BASE + f"{file_of[ch]}_root-pli-ms.json") if pl else None,
                "original_repo": BILARA_REPO,
            },
            "retrieved": RETRIEVED,
        })
    return records


def write_jsonl(records: list[dict]) -> str:
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records]
    blob = "\n".join(lines) + "\n"
    OUT_JSONL.write_text(blob, encoding="utf-8")
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------
SPOT = ["1.1", "1.5", "5.1", "24.21", "26.41"]   # incl. global 1, 5, 60, 354, 423


def write_validation(records, pali, muller, sha) -> None:
    by_id = {r["id"]: r for r in records}
    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])
    with_pl = sum(1 for r in records if r["original"])
    missing_en = [r["id"] for r in records if not r["text_en"]]
    missing_pl = [r["id"] for r in records if not r["original"]]

    L = []
    L.append("# VALIDATION -- Dhammapada corpus (CANONCITE)\n")
    L.append(f"Generated by `canoncite/corpus/build_dhammapada.py`. Retrieved: **{RETRIEVED}**.\n")
    L.append(f"**version (sha256 of sorted corpus_index.jsonl):** `{sha}`\n")

    L.append("## Sources (public-domain / open only)\n")
    L.append("| Field | Source | License | URL |")
    L.append("|---|---|---|---|")
    L.append(f"| original (Pali, romanised) | SuttaCentral bilara-data, Mahasangiti root/pli/ms | CC0 (public domain) | {BILARA_REPO} |")
    L.append(f"| text_en | F. Max Muller, *The Dhammapada*, SBE vol.10 (Oxford, 1881) | Public domain | {GUTENBERG_URL} |")
    L.append(f"| (canonical EN reference) | sacred-texts.com SBE10 (same Muller text; blocks automated fetch) | Public domain | {SACRED_TEXTS_REF} |")
    L.append("")
    L.append("### Notes (honest provenance)\n")
    L.append(
        "- **Pali IS sourced.** All 423 verses carry the Pali root text from SuttaCentral's "
        "open (CC0) Mahasangiti edition (`bilara-data`, `root/pli/ms`). Each verse is "
        "reconstructed by concatenating the integer line-segments of the bilara keys "
        "`dhpN:M` (structural header segments `0`/`0.x` are skipped). The text is romanised "
        "(IAST/Latin) at source, so `transliteration` is left `null` (the `original` already "
        "is the Latin-script reading); no Devanagari Pali was available from this source.")
    L.append(
        "- **English copy.** The released Müller SBE vol.10 (1881) text is taken from Project "
        "Gutenberg ebook #2017, which reproduces Müller's identical SBE translation, strictly "
        "verse-numbered. The canonical sacred-texts.com SBE10 pages carry the same text but "
        "block automated fetching (HTTP 403); Gutenberg #2017 is therefore the machine copy. "
        "`translation_source` is `Muller_SBE_1881`.")
    L.append(
        "- **Couplets.** Müller prints nine verse-pairs under a shared double number "
        "(58/59, 87/88, 104/105, 153/154, 195/196, 229/230, 256/257, 268/269, 271/272). Both "
        "verse ids in each pair carry that shared English text (405 single + 9 double "
        "paragraphs = 423 verses, an exact match to the canon -- no fabricated boundaries).")
    L.append(
        "- **IDs are chapter-local** (`chapter.verse`, e.g. `1.5`, `5.1`). The continuous "
        "1..423 Dhammapada numbering is preserved in the `global_verse` field. Chapter number "
        "is derived from which of the 26 SuttaCentral vagga files a verse came from; those "
        "file ranges coincide with the canonical vagga boundaries.\n")

    L.append("## Coverage summary\n")
    L.append(f"- Total citable verses (ID space): **{total}** (expected 423)")
    L.append(f"- Pali (`original`) coverage: **{with_pl}/{total} = {100*with_pl/total:.2f}%**")
    L.append(f"- English (Müller) coverage: **{with_en}/{total} = {100*with_en/total:.2f}%**")
    L.append(f"- Verses missing English (flagged): {missing_en or 'none'}")
    L.append(f"- Verses missing Pali (flagged): {missing_pl or 'none'}\n")

    L.append("## Per-chapter (vagga) counts\n")
    L.append("| Ch | Vagga (Pali) | Title (EN) | Verses (global) | Expected | Pali | English | Status |")
    L.append("|---:|---|---|---|---:|---:|---:|---|")
    for (ch, s, e, _stem, ptitle, etitle) in CHAPTERS:
        exp = e - s + 1
        recs = [r for r in records if r["chapter"] == ch]
        pl_n = sum(1 for r in recs if r["original"])
        en_n = sum(1 for r in recs if r["text_en"])
        status = "ok" if (len(recs) == exp and pl_n == exp and en_n == exp) else "CHECK"
        L.append(f"| {ch} | {ptitle} | {etitle} | {s}-{e} | {exp} | {pl_n} | {en_n} | {status} |")
    L.append(f"| **sum** |  |  |  | **{sum(e-s+1 for _c,s,e,*_ in CHAPTERS)}** "
             f"| **{with_pl}** | **{with_en}** |  |")
    L.append("")

    L.append("## Content spot-check (actual fetched text -- verify nothing was fabricated)\n")
    for sid in SPOT:
        r = by_id.get(sid)
        if not r:
            L.append(f"### {sid}\n_NOT FOUND_\n")
            continue
        L.append(f"### {sid}  (vagga {r['chapter']}, verse {r['verse']}, "
                 f"global {r['global_verse']}, tokens={r['tokens']})\n")
        L.append(f"- **original (Pali):** {r['original']}")
        L.append(f"- **text_en (Müller 1881):** {r['text_en']}\n")

    VALIDATION.write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refetch", action="store_true", help="re-download all raw sources")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    fetch_pali(args.refetch)
    muller_path = fetch_muller(args.refetch)

    pali = parse_pali()
    muller = parse_muller(muller_path)

    # integrity guards (never fabricate; fail loudly on gaps)
    assert set(pali) == set(range(1, 424)), f"Pali gap: {set(range(1,424)) - set(pali)}"
    assert set(muller) == set(range(1, 424)), f"English gap: {set(range(1,424)) - set(muller)}"

    records = build_records(pali, muller)
    sha = write_jsonl(records)
    write_validation(records, pali, muller, sha)

    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])
    with_pl = sum(1 for r in records if r["original"])
    print(f"[done] {total} verses -> {OUT_JSONL}")
    print(f"[done] Pali coverage    {with_pl}/{total} = {100*with_pl/total:.2f}%")
    print(f"[done] English coverage {with_en}/{total} = {100*with_en/total:.2f}%")
    print(f"[done] version sha256 = {sha}")
    print(f"[done] validation -> {VALIDATION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
