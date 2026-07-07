#!/usr/bin/env python3
"""Reproducible builder for the frozen Sri Guru Granth Sahib corpus (CANONCITE).

Produces ``canoncite/data/corpora/guru_granth_sahib/corpus_index.jsonl`` -- one
JSON object per atomic citable LINE of the Sri Guru Granth Sahib (SGGS), across
all 1430 Angs (pages), plus a ``VALIDATION.md`` report and a version (sha256).

------------------------------------------------------------------------------
CITABLE UNIT & ID GRAMMAR  (documented here and in VALIDATION.md)
------------------------------------------------------------------------------
The traditional, universally-used citation handle for the SGGS is the **Ang**
(page) number, 1..1430 -- the SGPC standard printing has a fixed, canonical
pagination, so "Ang N" is unambiguous and stable across editions.  Within an
Ang, lines are numbered 1..k in reading order.  We therefore make the atomic
citable unit the **line**, with ID grammar:

        id  ::=  "ang" "." <ang> "." <line>
        ang ::=  1 .. 1430                      (canonical SGGS pagination)
        line::=  1 .. k_ang                     (UNIQUE reading-order tuk index in Ang)

    e.g.  ang.1.1   = Ang 1, line 1   (the Mool Mantar)
          ang.1430.57 = last line of the SGGS (close of Raagmala)

NOTE on `line`: the citable line is the **tuk** (the phrase BaniDB segments as one
line, ending in a danda), numbered sequentially 1..k in reading order within the
Ang.  This is DISTINCT from the printed physical page-line: a single printed line
of the SGGS holds several tuks, so the API's ``lineno`` (kept as ``page_line``)
REPEATS within an Ang and cannot be the citation key.  ``line`` is therefore the
unique sequential tuk index; ``page_line`` is retained only as a printed-line
reference.  Each record also carries the upstream BaniDB stable ``line_id`` (a
content handle, e.g. "0NVY") and ``shabad_id``, so a citation stays resolvable
even if tuk segmentation is ever revised.

------------------------------------------------------------------------------
SOURCES  (real fetched data only -- nothing is ever invented)
------------------------------------------------------------------------------
  * Gurmukhi (Unicode), transliteration, Raag, author, Ang/line numbering:
        GurbaniNow API v2  (https://api.gurbaninow.com/v2/ang/{ang}), which
        serves the open **BaniDB / Shabad OS** database
        (https://github.com/shabados/database, MIT-licensed code; the gurbani
        text itself is ancient and PUBLIC DOMAIN).  One request per Ang;
        responses are cached verbatim under raw/gurbaninow/ang_{n}.json.

  * English translation (``text_en``):
        Dr. Sant Singh Khalsa's English translation (the ``translation.english
        .default`` field served by BaniDB), which is the de-facto standard
        English rendering used by SGPC, SikhNet and SikhiToTheMax.
        *** LICENSING CAVEAT (see VALIDATION.md) ***  This translation is NOT
        public-domain: it is under copyright (US, to 2096) and its stated terms
        require permission for commercial / internet redistribution, even though
        it is freely and widely redistributed for devotional / research use.
        Because the license is therefore NOT cleanly open, ``text_en`` can be
        suppressed with --no-english, which yields a Gurmukhi-only corpus whose
        every field is unambiguously public-domain.  When included, it is
        clearly flagged via ``translation_source`` = "Sant_Singh_Khalsa" and the
        per-record ``translation_license`` field.

CRITICAL RULE honoured throughout: no Gurmukhi or English text is ever invented.
Every ``original`` / ``transliteration`` / ``text_en`` value comes from the
fetched BaniDB response; anything missing upstream is left null and recorded.

Re-runnable: fetches into raw/ only if the cache is absent (use --refetch to
force), then parses from cache -> deterministic output.

Usage:
    python canoncite/corpus/build_guru_granth_sahib.py             # build (fetch if missing)
    python canoncite/corpus/build_guru_granth_sahib.py --refetch   # re-download all Angs
    python canoncite/corpus/build_guru_granth_sahib.py --no-english # Gurmukhi-only (all-PD)
    python canoncite/corpus/build_guru_granth_sahib.py --max-ang 50 # partial build (debug)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # canoncite/
DATA = ROOT / "data" / "corpora" / "guru_granth_sahib"
RAW = DATA / "raw"
GN_DIR = RAW / "gurbaninow"
OUT_JSONL = DATA / "corpus_index.jsonl"
VALIDATION = DATA / "VALIDATION.md"

RETRIEVED = "2026-06-30"
UA = "CanonciteCorpusBuilder/1.0 (research; public-domain gurbani corpus build)"
N_ANGS = 1430

API = "https://api.gurbaninow.com/v2/ang/{ang}"
GN_REPO = "https://github.com/shabados/database"
TRANSLATION_SOURCE = "Sant_Singh_Khalsa"
TRANSLATION_LICENSE = (
    "Dr. Sant Singh Khalsa English translation -- COPYRIGHTED (US, to 2096); "
    "freely & widely redistributed for devotional/research use (SGPC, SikhNet, "
    "SikhiToTheMax) but NOT public-domain; commercial/internet reuse nominally "
    "requires permission of the copyright holders. FLAGGED, not an open license."
)
GURMUKHI_LICENSE = "Public domain (ancient scripture text); served via BaniDB (MIT-licensed db)"


# ---------------------------------------------------------------------------
# Fetching (only when cache missing)
# ---------------------------------------------------------------------------
def _get(url: str, timeout: int = 45) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_angs(max_ang: int, refetch: bool = False, delay: float = 0.25) -> None:
    GN_DIR.mkdir(parents=True, exist_ok=True)
    for ang in range(1, max_ang + 1):
        dst = GN_DIR / f"ang_{ang}.json"
        if dst.exists() and not refetch:
            continue
        url = API.format(ang=ang)
        for attempt in range(5):
            try:
                data = _get(url)
                obj = json.loads(data)               # validate it parses
                if obj.get("page") and not obj.get("error"):
                    dst.write_bytes(data)
                    if ang == 1 or ang % 100 == 0 or ang == max_ang:
                        print(f"[fetch] Ang {ang}/{max_ang} -> {dst.name} "
                              f"({obj.get('count')} lines)")
                    break
            except Exception as e:                    # noqa: BLE001
                print(f"[warn] Ang {ang} attempt {attempt}: {e}")
                time.sleep(3 + 2 * attempt)
        else:
            raise RuntimeError(f"could not fetch Ang {ang} after retries")
        time.sleep(delay)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _clean(s: str | None) -> str | None:
    if s is None:
        return None
    s = " ".join(s.split()).strip()
    return s or None


def parse_ang(path: Path) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for entry in obj.get("page", []):
        ln = entry["line"]
        gur = (ln.get("gurmukhi") or {}).get("unicode")
        tr = (((ln.get("transliteration") or {}).get("english")) or {}).get("text")
        en = (((ln.get("translation") or {}).get("english")) or {}).get("default")
        writer = (ln.get("writer") or {}).get("english")
        raag = (ln.get("raag") or {}).get("english")
        out.append({
            "ang": int(ln["pageno"]),
            "page_line": int(ln["lineno"]),     # PRINTED physical page-line (repeats!)
            "line_id": ln.get("id"),
            "shabad_id": ln.get("shabadid"),
            "original": _clean(gur),
            "transliteration": _clean(tr),
            "text_en": _clean(en),
            "raag": _clean(raag),
            "author": _clean(writer),
        })
    return out


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build_records(max_ang: int, include_en: bool) -> list[dict]:
    records = []
    for ang in range(1, max_ang + 1):
        path = GN_DIR / f"ang_{ang}.json"
        # `line` is a UNIQUE sequential index within the Ang (reading order, 1..k);
        # the API's printed `page_line` repeats (many tuks per physical page-line),
        # so it cannot serve as the citation key -- it is kept only as a reference.
        for seq, li in enumerate(parse_ang(path), start=1):
            en = li["text_en"] if include_en else None
            records.append({
                "corpus": "guru_granth_sahib",
                "id": f"ang.{li['ang']}.{seq}",
                "unit": "line",
                "ang": li["ang"],
                "line": seq,
                "page_line": li["page_line"],
                "line_id": li["line_id"],
                "shabad_id": li["shabad_id"],
                "raag": li["raag"],
                "author": li["author"],
                "original": li["original"],
                "transliteration": li["transliteration"],
                "text_en": en,
                "translation_source": TRANSLATION_SOURCE if en else None,
                "translation_license": TRANSLATION_LICENSE if en else None,
                "gurmukhi_license": GURMUKHI_LICENSE,
                "tokens": len(en.split()) if en else 0,
                "source_urls": {
                    "data": API.format(ang=li["ang"]),
                    "database": GN_REPO,
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
SPOT = ["ang.1.1", "ang.1.2", "ang.2.1", "ang.8.18", "ang.1430.57"]


def write_validation(records: list[dict], max_ang: int, include_en: bool,
                     sha: str) -> None:
    by_id = {r["id"]: r for r in records}
    total = len(records)
    with_gur = sum(1 for r in records if r["original"])
    with_tr = sum(1 for r in records if r["transliteration"])
    with_en = sum(1 for r in records if r["text_en"])

    angs_present = sorted({r["ang"] for r in records})
    missing_angs = [a for a in range(1, N_ANGS + 1) if a not in set(angs_present)]
    lines_per_ang = {a: sum(1 for r in records if r["ang"] == a) for a in angs_present}
    empty_angs = [a for a, n in lines_per_ang.items() if n == 0]

    L = []
    L.append("# VALIDATION -- Sri Guru Granth Sahib corpus (CANONCITE)\n")
    L.append(f"Generated by `canoncite/corpus/build_guru_granth_sahib.py`. "
             f"Retrieved: **{RETRIEVED}**.\n")
    L.append(f"**version (sha256 of sorted corpus_index.jsonl):** `{sha}`\n")
    if max_ang < N_ANGS:
        L.append(f"> NOTE: PARTIAL build -- Angs 1..{max_ang} of {N_ANGS}.\n")

    # ---- ID grammar ----
    L.append("## Citable unit & ID grammar\n")
    L.append("The atomic citable unit is the **line** within an **Ang** (page). The Ang "
             "number (1..1430) is the canonical, edition-stable citation handle for the "
             "Sri Guru Granth Sahib (SGPC standard pagination). ID grammar:\n")
    L.append("```")
    L.append("id   ::= \"ang\" \".\" <ang> \".\" <line>")
    L.append("ang  ::= 1 .. 1430        # canonical SGGS pagination")
    L.append("line ::= 1 .. k_ang       # UNIQUE reading-order tuk index within that Ang")
    L.append("```")
    L.append("Examples: `ang.1.1` = Ang 1 line 1 (the Mool Mantar); "
             "`ang.1430.57` = last line of the SGGS.\n")
    L.append("**`line` is the tuk index, not the printed page-line.** The citable line is "
             "the *tuk* (the danda-terminated phrase BaniDB segments as one line), numbered "
             "sequentially 1..k in reading order within the Ang. A single PRINTED line of the "
             "SGGS contains several tuks, so the source API's physical `lineno` (preserved in "
             "each record as `page_line`) **repeats within an Ang and is NOT unique** -- hence "
             "it cannot be the citation key. The `id`/`line` field is the unique sequential "
             "tuk index; `page_line` is kept only as a printed-line cross-reference.\n")
    L.append("Each record additionally carries the upstream BaniDB stable `line_id` "
             "(content handle, e.g. `0NVY`) and `shabad_id` for robust cross-referencing.\n")

    # ---- sources ----
    L.append("## Sources\n")
    L.append("| Field | Source | License |")
    L.append("|---|---|---|")
    L.append(f"| original (Gurmukhi, Unicode), transliteration, raag, author, ang/line | "
             f"GurbaniNow API v2 serving BaniDB / Shabad OS db ({GN_REPO}) | "
             f"gurbani text PUBLIC DOMAIN; db code MIT |")
    L.append(f"| text_en | Dr. Sant Singh Khalsa English translation (BaniDB "
             f"`translation.english.default`) | **COPYRIGHTED -- see caveat** |")
    L.append("")
    L.append("Per-Ang raw API responses are cached verbatim under "
             "`raw/gurbaninow/ang_{n}.json` for full reproducibility.\n")

    # ---- license caveat ----
    L.append("## English translation license -- HONEST CAVEAT\n")
    L.append("`text_en` is **Dr. Sant Singh Khalsa's** English translation -- the de-facto "
             "standard open rendering used by SGPC, SikhNet and SikhiToTheMax, and served as "
             "BaniDB's default English. **It is NOT public domain.** Published terms state the "
             "translation is under copyright (US, to ~2096) and that commercial / internet "
             "redistribution nominally requires the permission of the copyright holders "
             "(Dr. Sant Singh Khalsa / Dr. Kulbir S. Thind), even though it is freely and "
             "widely redistributed for devotional and research use. It is therefore included "
             "here as **flagged, non-open content** (`translation_source=Sant_Singh_Khalsa`, "
             "`translation_license` set on every record).\n")
    L.append("No clean public-domain *complete, line-aligned* English translation of the SGGS "
             "is known to exist (older PD works -- Trumpp 1877, Macauliffe 1909 -- are partial "
             "and not Ang/line aligned). Downstream users who need a strictly-open corpus can "
             "rebuild with `--no-english`, which leaves every `text_en` null and yields a "
             "corpus whose every populated field is unambiguously public domain "
             "(Gurmukhi + transliteration + Ang/line index).\n")
    L.append(f"This build: English included = **{include_en}**.\n")

    # ---- coverage ----
    pct = lambda n: f"{n}/{total} = {100*n/total:.2f}%" if total else "0"
    L.append("## Coverage summary\n")
    L.append(f"- Angs covered: **{len(angs_present)}** "
             f"({angs_present[0]}..{angs_present[-1]}) of {N_ANGS}")
    L.append(f"- Missing Angs: {missing_angs or 'none'}")
    L.append(f"- Empty Angs (0 lines parsed): {empty_angs or 'none'}")
    L.append(f"- Total citable lines (ID space `U`): **{total}**")
    L.append(f"- Gurmukhi (original) coverage: **{pct(with_gur)}**")
    L.append(f"- Transliteration coverage: **{pct(with_tr)}**")
    L.append(f"- English (Sant Singh Khalsa) coverage: **{pct(with_en)}**")
    gaps_gur = [r["id"] for r in records if not r["original"]]
    L.append(f"- Lines missing Gurmukhi (should be none): "
             f"{gaps_gur[:20] or 'none'}{' ...' if len(gaps_gur) > 20 else ''}\n")

    # ---- flagged gaps ----
    L.append("## Flagged gaps / notes\n")
    if missing_angs:
        L.append(f"- **{len(missing_angs)} Angs not fetched/parsed** "
                 f"(PARTIAL build): {missing_angs[:30]}{' ...' if len(missing_angs) > 30 else ''}")
    else:
        L.append("- All 1430 Angs fetched and parsed; no missing pages.")
    miss_en = sum(1 for r in records if not r["text_en"])
    if include_en:
        L.append(f"- Lines with no English translation upstream (text_en null): **{miss_en}** "
                 f"(left null, not fabricated).")
    L.append("- Line counts per Ang vary (10..60+); the count is whatever BaniDB segments for "
             "that page. Segmentation follows the standard SGGS line breaks; the upstream "
             "stable `line_id` insulates citations against any future re-segmentation.\n")

    # ---- spot check ----
    L.append("## Content spot-check (actual fetched text -- verify nothing was fabricated)\n")
    for sid in SPOT:
        r = by_id.get(sid)
        if not r:
            L.append(f"### {sid}\n_NOT IN THIS BUILD_\n")
            continue
        L.append(f"### {sid}  (Ang {r['ang']}, line {r['line']}, raag={r['raag']}, "
                 f"author={r['author']}, tokens={r['tokens']})\n")
        L.append(f"- **original (Gurmukhi):** {r['original']}")
        L.append(f"- **transliteration:** {r['transliteration']}")
        L.append(f"- **text_en (Sant Singh Khalsa):** {r['text_en']}")
        L.append(f"- **line_id:** `{r['line_id']}`  shabad_id: `{r['shabad_id']}`\n")

    VALIDATION.write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refetch", action="store_true", help="re-download all Angs")
    ap.add_argument("--no-english", action="store_true",
                    help="suppress copyrighted English -> all-public-domain corpus")
    ap.add_argument("--max-ang", type=int, default=N_ANGS,
                    help="build only Angs 1..MAX (partial build)")
    args = ap.parse_args()
    max_ang = max(1, min(args.max_ang, N_ANGS))
    include_en = not args.no_english

    RAW.mkdir(parents=True, exist_ok=True)
    fetch_angs(max_ang, args.refetch)

    records = build_records(max_ang, include_en)
    sha = write_jsonl(records)
    write_validation(records, max_ang, include_en, sha)

    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])
    angs = len({r["ang"] for r in records})
    print(f"[done] {total} lines across {angs} Angs -> {OUT_JSONL}")
    print(f"[done] English coverage {with_en}/{total} "
          f"= {100*with_en/total:.2f}% (include_en={include_en})")
    print(f"[done] version sha256 = {sha}")
    print(f"[done] validation -> {VALIDATION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
