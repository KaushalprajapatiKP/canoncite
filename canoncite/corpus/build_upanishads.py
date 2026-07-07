#!/usr/bin/env python3
"""Reproducible builder for the frozen Principal Upanishads corpus (CANONCITE).

Produces ``canoncite/data/corpora/upanishads/corpus_index.jsonl`` -- one JSON
object per atomic citable verse/mantra for a clean subset of the principal
Upanishads -- plus a ``VALIDATION.md`` report and a version (sha256) line.

Public-domain sources only (no verse text is ever invented):

  * text_en  -- F. Max Muller, *The Upanishads*, Sacred Books of the East
                vols. 1 (1879) and 15 (1884).  PUBLIC DOMAIN.
                Fetched per-section from sacred-texts.com (via the Internet
                Archive Wayback proxy, which serves the same digitised pages;
                the live host 403s automated agents).  Each section page is a
                khanda / valli / adhyaya / prasna whose verses are printed with
                inline "N." numbering, so it aligns cleanly to canonical ids.

  * original (Devanagari) + transliteration (IAST)
             -- GRETIL (Goettingen Register of Electronic Texts in Indian
                Languages), the "mula" (root-text) UTF-8 files under
                gretil/1_sanskr/1_veda/4_upa/.  GRETIL distributes the verse
                text in IAST with structured "|| KaU_1.2 ||" verse markers;
                that IAST is stored verbatim as ``transliteration``.  The
                ``original`` Devanagari is produced by *mechanical, lossless*
                transliteration of the GRETIL IAST via ``indic_transliteration``
                (Sanscript IAST->DEVANAGARI) -- this is a deterministic script
                conversion of fetched text, not an independent source, and is
                flagged as such in VALIDATION.md.

ALIGNMENT.  Each verse is keyed by (upanishad, section-path, verse-number).
English and Sanskrit are merged *by label number within each section* -- never
by position -- so a verse that one source numbers but the other omits is simply
left null on the missing side and flagged, rather than silently shifting the
alignment (this matters e.g. for Katha 2.6, where Muller skips verse 16).

SCOPE (honest, explicit).  The clean, well-aligned principal Upanishads are
built; the prose-heavy / non-aligning ones are deliberately NOT included and the
reason is documented in VALIDATION.md (see ``DEFERRED`` below).  Coverage of
text_en vs original is heterogeneous and reported per-Upanishad:

  isha          18  EN(SBE1)  + SA(GRETIL)
  kena          35  EN(SBE1)  + SA none   (GRETIL hosts no direct mula text)
  katha        119  EN(SBE15) + SA(GRETIL)
  prashna       67  EN(SBE15) + SA(GRETIL)
  mundaka       64  EN(SBE15) + SA none
  mandukya      12  EN none   + SA(GRETIL)  (Muller did not translate Mandukya)
  svetasvatara 113  EN(SBE15) + SA(GRETIL)
  aitareya      33  EN none   + SA(GRETIL)  (Muller renders it inside the
                                            Aitareya-Aranyaka with non-aligning
                                            verse divisions; see VALIDATION.md)

Re-runnable: fetches into raw/ only if the cache is absent (use --refetch to
force), then parses from cache -> deterministic output.

Usage:
    python canoncite/corpus/build_upanishads.py            # build (fetch if missing)
    python canoncite/corpus/build_upanishads.py --refetch  # re-download raw sources
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
ROOT = HERE.parent                                    # canoncite/
DATA = ROOT / "data" / "corpora" / "upanishads"
RAW = DATA / "raw"
EN_DIR = RAW / "en"
GR_DIR = RAW / "gretil"
OUT_JSONL = DATA / "corpus_index.jsonl"
VALIDATION = DATA / "VALIDATION.md"

CORPUS = "upanishads"
RETRIEVED = "2026-06-30"
UA = "CanonciteCorpusBuilder/1.0 (research; public-domain corpus build)"

TRANSLATION_SOURCE = "Muller_SBE"
ORIGINAL_SOURCE = "GRETIL"

# --- source URL templates ---------------------------------------------------
ST_LIVE = "https://www.sacred-texts.com/hin/{vol}/{page}.htm"
ST_FETCH = "https://web.archive.org/web/2019id_/https://www.sacred-texts.com/hin/{vol}/{page}.htm"
GR_BASE = "https://gretil.sub.uni-goettingen.de/gretil/1_sanskr/1_veda/4_upa/{f}"

# ---------------------------------------------------------------------------
# Corpus configuration
# ---------------------------------------------------------------------------
# EN_PAGES[upanishad] = list of (vol, page_number, section_prefix_tuple).
# A section_prefix_tuple holds the section ids that precede the verse number
# (e.g. (adhyaya, valli) for Katha, (khanda,) for Kena, () for flat Isha).
EN_PAGES = {
    "isha":        [("sbe01", 243, ())],
    "kena":        [("sbe01", 176, (1,)), ("sbe01", 177, (2,)),
                    ("sbe01", 178, (3,)), ("sbe01", 179, (4,))],
    "katha":       [("sbe15", 10, (1, 1)), ("sbe15", 11, (1, 2)),
                    ("sbe15", 12, (1, 3)), ("sbe15", 13, (2, 4)),
                    ("sbe15", 14, (2, 5)), ("sbe15", 15, (2, 6))],
    "mundaka":     [("sbe15", 16, (1, 1)), ("sbe15", 17, (1, 2)),
                    ("sbe15", 18, (2, 1)), ("sbe15", 19, (2, 2)),
                    ("sbe15", 20, (3, 1)), ("sbe15", 21, (3, 2))],
    "prashna":     [("sbe15", 106, (1,)), ("sbe15", 107, (2,)),
                    ("sbe15", 108, (3,)), ("sbe15", 109, (4,)),
                    ("sbe15", 110, (5,)), ("sbe15", 111, (6,))],
    "svetasvatara":[("sbe15", 100, (1,)), ("sbe15", 101, (2,)),
                    ("sbe15", 102, (3,)), ("sbe15", 103, (4,)),
                    ("sbe15", 104, (5,)), ("sbe15", 105, (6,))],
}

# GRETIL[upanishad] = (filename, key_parser).  key_parser maps a GRETIL verse
# label string (the part after "Prefix_") to (section_prefix_tuple, verse_int).
def _k_flat(k):                       # "7" -> ((), 7)
    return (), int(k)


def _k_two(k):                        # "3.2" -> ((3,), 2)
    a, v = k.split(".")
    return (int(a),), int(v)


def _k_katha(k):                      # "4.7" -> ((2, 4), 7)   adhyaya from valli
    valli, v = k.split(".")
    valli = int(valli)
    adhyaya = 1 if valli <= 3 else 2
    return (adhyaya, valli), int(v)


def _k_aitareya(k):                   # "1,3.14" -> ((1, 3), 14); "2.5" -> ((2,1),5)
    if "," in k:
        a, rest = k.split(",")
        kh, v = rest.split(".")
        return (int(a), int(kh)), int(v)
    a, v = k.split(".")
    return (int(a), 1), int(v)


GRETIL = {
    "isha":        ("isup___u.htm", _k_flat),
    "katha":       ("kathop_u.htm", _k_katha),
    "prashna":     ("prasup_u.htm", _k_two),
    "mandukya":    ("mandup_u.htm", _k_flat),
    "svetasvatara":("svetu_pu.htm", _k_two),
    "aitareya":    ("aitup__u.htm", _k_aitareya),
}

# Order + human-readable section scheme (for VALIDATION.md).
ORDER = ["isha", "kena", "katha", "prashna", "mundaka",
         "mandukya", "svetasvatara", "aitareya"]
SCHEME = {
    "isha":         "isha.<verse>                       (18 mantras, flat)",
    "kena":         "kena.<khanda>.<verse>              (4 khandas)",
    "katha":        "katha.<adhyaya>.<valli>.<verse>    (2 adhyayas / 6 vallis)",
    "prashna":      "prashna.<question>.<verse>         (6 questions)",
    "mundaka":      "mundaka.<mundaka>.<khanda>.<verse> (3 mundakas x 2 khandas)",
    "mandukya":     "mandukya.<verse>                   (12 mantras, flat)",
    "svetasvatara": "svetasvatara.<adhyaya>.<verse>     (6 adhyayas)",
    "aitareya":     "aitareya.<adhyaya>.<khanda>.<verse>(3 adhyayas)",
}
# Upanishads consciously left out of this build, with the honest reason.
DEFERRED = {
    "taittiriya": "SBE15 renders it as continuous prose with inline editorial "
                  "notes and only sparse '(1-5)'-style numbering; it cannot be "
                  "split into per-verse English without fabricating boundaries. "
                  "GRETIL also hosts no direct mula file (it links out to TITUS).",
    "chandogya":  "Tractable but large (8 prapathakas, ~150 SBE1 section pages); "
                  "deferred to keep this first build a clean, fully-validated "
                  "subset. GRETIL mula = chup___u.htm; SBE1 = sbe01022-175.",
    "brihadaranyaka": "Tractable but large (6 adhyayas, ~47 SBE15 section pages) "
                  "and the SBE15 digitisation drops brahmana I,3; deferred for "
                  "the same reason. GRETIL mula = brup___u.htm; SBE15 = sbe15053-099.",
}

# ---------------------------------------------------------------------------
# Fetching (only when cache missing)
# ---------------------------------------------------------------------------
def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _fetch_to(dst: Path, url: str, refetch: bool, min_size: int = 1500) -> None:
    if dst.exists() and not refetch:
        return
    for attempt in range(4):
        try:
            data = _get(url)
            if len(data) >= min_size:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(data)
                print(f"[fetch] {dst.name} <- {url}")
                return
        except Exception as e:                                   # noqa: BLE001
            print(f"[warn] {dst.name} attempt {attempt}: {e}")
        time.sleep(6)
    raise RuntimeError(f"could not fetch {url}")


def fetch_all(refetch: bool = False) -> None:
    for pages in EN_PAGES.values():
        for vol, page, _ in pages:
            pg = f"{vol}{page:03d}"
            _fetch_to(EN_DIR / f"{pg}.html",
                      ST_FETCH.format(vol=vol, page=pg), refetch)
            time.sleep(1)
    for fname, _ in GRETIL.values():
        _fetch_to(GR_DIR / fname, GR_BASE.format(f=fname), refetch, min_size=2000)
        time.sleep(1)


# ---------------------------------------------------------------------------
# Parsing -- English (Muller SBE section pages)
# ---------------------------------------------------------------------------
def parse_en_page(path: Path) -> dict[int, str]:
    """Return {verse_number: english_text} for one SBE section page.

    Verses are <p>N. ...</p>; continuation paragraphs (page breaks) carry no
    number and are appended.  Footnote refs and the trailing 'Footnotes'
    section are stripped, and any post-text appendix (e.g. the Rammohun Roy
    rendering on the Isa page) is dropped by enforcing sequential numbering.
    """
    h = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<BODY.*?</BODY>", h, re.S | re.I)
    body = m.group(0) if m else h
    body = re.split(r"<H3[^>]*>\s*Footnotes", body, flags=re.I)[0]
    verses: dict[int, str] = {}
    cur = None
    for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S | re.I):
        t = re.sub(r'<A NAME[^>]*></A><A HREF[^>]*>.*?</A>', "", p, flags=re.S)
        t = re.sub(r'<FONT SIZE="1">.*?</FONT>', "", t, flags=re.S)
        t = re.sub(r"<[^>]+>", " ", t)
        t = html.unescape(t)
        t = re.sub(r"\s+", " ", t).strip()
        if not t or "sacred-texts.com" in t:
            continue
        t = re.sub(r"\bp\.\s*\d+\b", "", t).strip()       # page markers
        if not t:
            continue
        mm = re.match(r"^(\d+)\s*\.\s*(.*)$", t)
        if mm:
            n = int(mm.group(1))
            if (cur is None and n == 1) or (cur is not None and cur < n <= cur + 4):
                cur = n
                verses[n] = mm.group(2).strip()
            # else: out-of-sequence (appendix / alt numbering) -> ignore rest
        elif cur is not None:
            verses[cur] = (verses[cur] + " " + t).strip()
    return verses


# ---------------------------------------------------------------------------
# Parsing -- GRETIL (IAST mula files)
# ---------------------------------------------------------------------------
_MARK = re.compile(r"[|/]{2}\s*([A-Za-z]+)_([0-9][0-9,\.]*)\s*[|/]{2}")


def _gr_clean(txt: str) -> str:
    txt = re.sub(r"[|/]{2}\s*iti[^|/]*?[|/]{2}", " ", txt)   # end-of-section colophons
    txt = re.sub(r"[|/]{2}\s*atha[^|/]*?[|/]{2}", " ", txt)
    txt = txt.strip().strip("/|").strip()
    return re.sub(r"\s+", " ", txt)


def parse_gretil(path: Path) -> dict[str, str]:
    """Return {verse_label: iast_text} for one GRETIL mula file."""
    h = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<body.*?</body>", h, re.S | re.I)
    body = m.group(0) if m else h
    t = html.unescape(re.sub(r"<[^>]+>", " ", body))
    idx = t.rfind("gretil.htm")                # cut metadata header
    if idx != -1:
        t = t[idx + len("gretil.htm"):]
    out: dict[str, str] = {}
    buf: list[str] = []
    for raw in t.split("\n"):
        line = raw.strip()
        if not line:
            continue
        mm = _MARK.search(line)
        if mm:
            pre = line[:mm.start()].strip()
            if pre:
                buf.append(pre)
            out[mm.group(2)] = _gr_clean(" ".join(buf))
            buf = []
            rest = line[mm.end():].strip()
            if rest and ("/" in rest or "|" in rest):
                buf.append(rest)
        elif "/" in line or "|" in line:        # verse / pada line
            buf.append(line)
        # else: title / section-header line -> skip
    return out


# ---------------------------------------------------------------------------
# Devanagari (mechanical transliteration of the GRETIL IAST)
# ---------------------------------------------------------------------------
def _make_deva():
    try:
        from indic_transliteration import sanscript
    except Exception:                                          # noqa: BLE001
        print("[warn] indic_transliteration unavailable -> original=Devanagari left null")
        return None

    def conv(iast: str) -> str:
        s = iast.replace("//", "।।").replace("/", "।").replace("|", "।")
        return sanscript.transliterate(s, sanscript.IAST, sanscript.DEVANAGARI)
    return conv


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def _id(ns: str, path: tuple[int, ...]) -> str:
    return ns + "." + ".".join(str(x) for x in path)


def build_records(deva) -> tuple[list[dict], dict]:
    records: list[dict] = []
    stats: dict = {}

    for ns in ORDER:
        # ---- gather English: {section_tuple: {verse: text}} ----
        en: dict[tuple, dict[int, str]] = {}
        en_page_url: dict[tuple, str] = {}
        for vol, page, prefix in EN_PAGES.get(ns, []):
            pg = f"{vol}{page:03d}"
            vs = parse_en_page(EN_DIR / f"{pg}.html")
            en.setdefault(prefix, {}).update(vs)
            en_page_url[prefix] = ST_LIVE.format(vol=vol, page=pg)

        # ---- gather Sanskrit: {section_tuple: {verse: iast}} ----
        sa: dict[tuple, dict[int, str]] = {}
        gr_url = None
        if ns in GRETIL:
            fname, parser = GRETIL[ns]
            gr_url = GR_BASE.format(f=fname)
            for label, txt in parse_gretil(GR_DIR / fname).items():
                sec, v = parser(label)
                sa.setdefault(sec, {})[v] = txt

        # ---- union of (section_tuple, verse) keys ----
        keys: set[tuple] = set()
        for sec, d in en.items():
            for v in d:
                keys.add(sec + (v,))
        for sec, d in sa.items():
            for v in d:
                keys.add(sec + (v,))

        n_en = n_sa = 0
        for path in sorted(keys):
            sec, v = path[:-1], path[-1]
            text_en = en.get(sec, {}).get(v)
            iast = sa.get(sec, {}).get(v)
            original = deva(iast) if (iast and deva) else None
            if text_en:
                n_en += 1
            if iast:
                n_sa += 1
            tok = text_en.split() if text_en else (iast.split() if iast else [])
            records.append({
                "corpus": CORPUS,
                "id": _id(ns, path),
                "unit": "verse",
                "upanishad": ns,
                "sections": list(path),
                "text_en": text_en,
                "original": original,
                "transliteration": iast,
                "translation_source": TRANSLATION_SOURCE if text_en else None,
                "original_source": ORIGINAL_SOURCE if iast else None,
                "source_urls": {
                    "en": en_page_url.get(sec) if text_en else None,
                    "original": gr_url if iast else None,
                },
                "retrieved": RETRIEVED,
                "tokens": len(tok),
            })
        stats[ns] = {"total": len(keys), "en": n_en, "sa": n_sa}
    return records, stats


def write_jsonl(records: list[dict]) -> str:
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records]
    blob = "\n".join(lines) + "\n"
    OUT_JSONL.write_text(blob, encoding="utf-8")
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------
SPOT = ["isha.1", "katha.1.2.5", "prashna.1.3", "svetasvatara.4.3", "mandukya.7"]


def write_validation(records: list[dict], stats: dict, sha: str) -> None:
    by_id = {r["id"]: r for r in records}
    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])
    with_sa = sum(1 for r in records if r["transliteration"])

    L: list[str] = []
    L.append("# VALIDATION -- Principal Upanishads corpus (CANONCITE)\n")
    L.append(f"Generated by `canoncite/corpus/build_upanishads.py`. Retrieved: **{RETRIEVED}**.\n")
    L.append(f"**version (sha256 of sorted corpus_index.jsonl):** `{sha}`\n")

    L.append("## Sources (public-domain only)\n")
    L.append("| Field | Source | URL |")
    L.append("|---|---|---|")
    L.append("| text_en | F. Max Muller, *The Upanishads*, Sacred Books of the East "
             "vols. 1 (1879) & 15 (1884), PUBLIC DOMAIN | "
             "https://www.sacred-texts.com/hin/sbe01/ , https://www.sacred-texts.com/hin/sbe15/ |")
    L.append("| transliteration (IAST) | GRETIL mula UTF-8 texts (gretil/1_sanskr/1_veda/4_upa/) | "
             "https://gretil.sub.uni-goettingen.de/gretil/1_sanskr/1_veda/4_upa/ |")
    L.append("| original (Devanagari) | mechanical IAST->Devanagari transliteration of the GRETIL "
             "text (indic_transliteration / Sanscript), deterministic; NOT an independent source | "
             "(derived) |")
    L.append("")
    L.append("> sacred-texts.com 403s automated fetchers, so the identical digitised pages are "
             "fetched through the Internet Archive Wayback proxy "
             "(`web.archive.org/web/2019id_/...`). The canonical citation URL recorded in each "
             "record's `source_urls.en` is the live sacred-texts.com page.\n")

    L.append("## Coverage summary\n")
    L.append(f"- Upanishads included: **{len(ORDER)}** -- {', '.join(ORDER)}.")
    L.append(f"- Total citable verses (closed id space): **{total}**.")
    L.append(f"- text_en (Muller) present: **{with_en}/{total} = {100*with_en/total:.1f}%**.")
    L.append(f"- original+transliteration (GRETIL) present: **{with_sa}/{total} = {100*with_sa/total:.1f}%**.\n")

    L.append("## Per-Upanishad id grammar, counts & coverage\n")
    L.append("| Upanishad | id grammar | verses | text_en | sanskrit | notes |")
    L.append("|---|---|---:|---:|---:|---|")
    notes = {
        "isha": "full EN+SA, both 18, exact label match",
        "kena": "EN only -- GRETIL hosts no direct Kena mula (links out to TITUS)",
        "katha": "EN+SA; Muller skips label 2.6.16 (SA present, EN null there)",
        "prashna": "full EN+SA, exact per-question label match",
        "mundaka": "EN only -- GRETIL hosts no direct Mundaka mula",
        "mandukya": "SA only -- Muller did not translate Mandukya (EN null)",
        "svetasvatara": "full EN+SA, exact per-adhyaya label match",
        "aitareya": "SA only -- Muller's Aitareya-Aranyaka numbering does not align",
    }
    for ns in ORDER:
        s = stats[ns]
        L.append(f"| {ns} | `{SCHEME[ns].split('(')[0].strip()}` | {s['total']} | "
                 f"{s['en']} | {s['sa']} | {notes[ns]} |")
    L.append(f"| **total** | | **{total}** | **{with_en}** | **{with_sa}** | |")
    L.append("")

    L.append("## Section scheme per Upanishad\n")
    for ns in ORDER:
        L.append(f"- **{ns}** -- `{SCHEME[ns]}`")
    L.append("")

    # gaps / flags
    L.append("## Flagged gaps (null fields -- never fabricated)\n")
    miss_en = sorted([r["id"] for r in records if not r["text_en"]])
    miss_sa = sorted([r["id"] for r in records if not r["transliteration"]])
    L.append(f"- Verses with **no text_en** ({len(miss_en)}): every Mandukya & Aitareya verse "
             "(Muller did not translate them in an aligning form), plus **katha.2.6.16** "
             "(Muller's edition skips that verse number). Full id list:")
    L.append("  " + ", ".join(miss_en) + "\n")
    L.append(f"- Verses with **no original/transliteration** ({len(miss_sa)}): all of Kena and "
             "Mundaka (GRETIL hosts no direct mula file for them -- the catalogue links out to "
             "the external TITUS database, which is outside the GRETIL source mandate), plus "
             "**katha.2.6.19** (Muller's closing santi-mantra, absent from the GRETIL text).\n")

    L.append("## Upanishads deliberately NOT included (honest scope)\n")
    for ns, why in DEFERRED.items():
        L.append(f"- **{ns}** -- {why}")
    L.append("")

    L.append("## Content spot-check (actual fetched text -- verify nothing was fabricated)\n")
    for sid in SPOT:
        r = by_id.get(sid)
        if not r:
            L.append(f"### {sid}\n_NOT FOUND_\n")
            continue
        L.append(f"### {sid}  (sections={r['sections']}, tokens={r['tokens']})\n")
        L.append(f"- **text_en (Muller):** {r['text_en']}")
        L.append(f"- **transliteration (GRETIL IAST):** {r['transliteration']}")
        L.append(f"- **original (Devanagari, derived):** {r['original']}\n")

    VALIDATION.write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refetch", action="store_true", help="re-download all raw sources")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    fetch_all(args.refetch)

    deva = _make_deva()
    records, stats = build_records(deva)
    sha = write_jsonl(records)
    write_validation(records, stats, sha)

    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])
    with_sa = sum(1 for r in records if r["transliteration"])
    print(f"[done] {total} verses -> {OUT_JSONL}")
    print(f"[done] text_en coverage {with_en}/{total} = {100*with_en/total:.1f}%")
    print(f"[done] sanskrit coverage {with_sa}/{total} = {100*with_sa/total:.1f}%")
    print(f"[done] version sha256 = {sha}")
    print(f"[done] validation -> {VALIDATION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
