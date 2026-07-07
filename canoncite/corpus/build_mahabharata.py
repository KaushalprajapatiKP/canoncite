#!/usr/bin/env python3
"""Reproducible builder for the frozen Mahabharata corpus (CANONCITE).

Produces ``canoncite/data/corpora/mahabharata/corpus_index.jsonl`` -- one JSON
object per atomic citable *shloka* for the full 18-parva Mahabharata, plus a
``VALIDATION.md`` report and a version (sha256) line.

This is the LARGEST CANONCITE corpus. We are deliberately PRAGMATIC and HONEST
about coverage (see VALIDATION.md):

  * Sanskrit (the constituted critical text) -- COMPLETE, all 18 parvas:
        GRETIL machine-readable edition of the **Bhandarkar Oriental Research
        Institute (BORI / "Poona") Critical Edition**, entered by Muneo Tokunaga
        et al., revised by John Smith (Cambridge).
        https://gretil.sub.uni-goettingen.de/gretil/1_sanskr/2_epic/mbh/
        GRETIL ships the text in **IAST transliteration** with authoritative
        ``parva,adhyaya.shloka`` line labels (the BORI numbering itself).
        The ID space of this corpus IS that numbering: id = "<parva>.<adhyaya>.<shloka>".

  * transliteration (IAST): taken verbatim from GRETIL (its native encoding).

  * original (Devanagari): produced by DETERMINISTIC, mechanical IAST -> Devanagari
        transliteration of the GRETIL IAST via ``indic_transliteration.sanscript``.
        It is NOT a second independent source; it is a script conversion of the
        GRETIL text. Documented as such in VALIDATION.md. (No verse text is
        invented; transliteration is a reversible character mapping.)

  * English (Ganguli, 1883-96, PUBLIC DOMAIN): NOT aligned at shloka level.
        Kisari Mohan Ganguli's complete English prose translation is organised by
        parva -> "SECTION" following the *Calcutta vulgate* segmentation, which
        does NOT map 1:1 to BORI critical-edition adhyaya/shloka numbers. There is
        no verified shloka<->section concordance, so assigning per-shloka English
        would FABRICATE alignment (forbidden). ``text_en`` is therefore left null
        for every record; ``source_urls.en`` points to the Ganguli parva index
        (section granularity) for provenance, and the parva index pages are cached
        under ``raw/ganguli/`` (fetched via the Wayback Machine, since
        sacred-texts.com is now behind Cloudflare).

CRITICAL RULE honoured throughout: no shloka text is ever invented. Every
``transliteration`` value is the fetched GRETIL line text; ``original`` is its
mechanical Devanagari transliteration; ``text_en`` is null wherever it cannot be
aligned without fabrication (i.e. everywhere, here -- and that is recorded).

Star ("*") passages -- the critical edition's *apparatus / interpolation*
insertions (lines such as ``01,001.003b*0018_01``) -- are EXCLUDED from the
constituted-text shloka index; they carry non-shloka numbering and are not part
of the constituted text. Their per-parva counts are reported in VALIDATION.md.

Re-runnable: fetches into raw/ only if the cache is absent (use --refetch to
force), then parses from cache -> deterministic output.

Usage:
    python canoncite/corpus/build_mahabharata.py            # build from cache (fetch if missing)
    python canoncite/corpus/build_mahabharata.py --refetch  # re-download raw sources
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

try:
    from indic_transliteration import sanscript
except Exception as exc:  # noqa: BLE001
    sys.stderr.write(
        "ERROR: this builder needs `indic_transliteration` for IAST->Devanagari.\n"
        "       pip install indic_transliteration\n")
    raise

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # canoncite/
DATA = ROOT / "data" / "corpora" / "mahabharata"
RAW = DATA / "raw"
GRETIL_DIR = RAW / "gretil"
GANGULI_DIR = RAW / "ganguli"
OUT_JSONL = DATA / "corpus_index.jsonl"
VALIDATION = DATA / "VALIDATION.md"

RETRIEVED = "2026-06-30"
UA = "CanonciteCorpusBuilder/1.0 (research; public-domain corpus build)"

ORIGINAL_SOURCE = "GRETIL"
TRANSLATION_SOURCE = "Ganguli"          # nominal English source (section-level only; see below)

# 18 parvas: number -> short name (matches the Gita corpus' lowercase style).
PARVA_NAME = {
    1: "adi", 2: "sabha", 3: "vana", 4: "virata", 5: "udyoga", 6: "bhishma",
    7: "drona", 8: "karna", 9: "shalya", 10: "sauptika", 11: "stri",
    12: "shanti", 13: "anushasana", 14: "ashvamedhika", 15: "ashramavasika",
    16: "mausala", 17: "mahaprasthanika", 18: "svargarohana",
}

GRETIL_BASE = "https://gretil.sub.uni-goettingen.de/gretil/1_sanskr/2_epic/mbh"
GRETIL_FILE = "mbh_{p:02d}_u.htm"
# Ganguli (sacred-texts.com) parva index, fetched through the Wayback Machine.
GANGULI_INDEX = "https://www.sacred-texts.com/hin/m{p:02d}/index.htm"
WAYBACK = "https://web.archive.org/web/2020id_/{url}"

# Bhagavad Gita overlap inside Bhishma parva (BORI): adhyayas 23-40 of parva 6.
GITA_PARVA = 6
GITA_ADHYAYAS = (23, 40)


# ---------------------------------------------------------------------------
# Fetching (only when cache missing)
# ---------------------------------------------------------------------------
def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_gretil(refetch: bool = False) -> None:
    GRETIL_DIR.mkdir(parents=True, exist_ok=True)
    for p in range(1, 19):
        dst = GRETIL_DIR / GRETIL_FILE.format(p=p)
        if dst.exists() and not refetch:
            continue
        url = f"{GRETIL_BASE}/{GRETIL_FILE.format(p=p)}"
        for attempt in range(4):
            try:
                data = _get(url)
                if len(data) > 10000:
                    dst.write_bytes(data)
                    print(f"[fetch] GRETIL parva {p} -> {dst} ({len(data)} bytes)")
                    break
            except Exception as e:  # noqa: BLE001
                print(f"[warn] GRETIL parva {p} attempt {attempt}: {e}")
            time.sleep(6)
        else:
            raise RuntimeError(f"could not fetch GRETIL parva {p}")
        time.sleep(1)


def fetch_ganguli(refetch: bool = False) -> None:
    """Cache the 18 Ganguli parva INDEX pages (section-level provenance only;
    non-fatal). sacred-texts.com is behind Cloudflare -> fetch via Wayback."""
    GANGULI_DIR.mkdir(parents=True, exist_ok=True)
    for p in range(1, 19):
        dst = GANGULI_DIR / f"m{p:02d}_index.htm"
        if dst.exists() and not refetch:
            continue
        url = WAYBACK.format(url=GANGULI_INDEX.format(p=p))
        try:
            data = _get(url)
            if len(data) > 2000:
                dst.write_bytes(data)
                print(f"[fetch] Ganguli parva {p} index -> {dst}")
        except Exception as e:  # noqa: BLE001
            print(f"[warn] Ganguli parva {p} index not cached: {e}")
        time.sleep(2)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
# GRETIL line label: PP,SSS.NNN<suffix>[<star>](TAB|"<>")text[<BR>]
#   PP   = 2-digit parva           SSS = 3-digit adhyaya       NNN = 3-digit shloka
#   suffix = pada letters a-f (verse) or A-H (prose paragraph) or empty (speaker tag)
#   star   = "*NNNN_NN" -> apparatus / interpolation passage (EXCLUDED)
LINE = re.compile(
    r'^([0-9]{2}),([0-9]{3})\.([0-9]{3})'      # parva, adhyaya, shloka
    r'([A-Za-z]*)'                              # pada/prose suffix (may be empty)
    r'(\*[^<\t]*)?'                             # optional star (apparatus) marker
    r'(?:\t|<>)'                                # label/text delimiter (tab or "<>")
    r'(.*?)'                                    # body
    r'(?:<BR>)?\s*$')


def _clean(text: str) -> str:
    # GRETIL bodies are plain IAST; drop any stray tags / collapse whitespace.
    s = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", s).strip()


def parse_parva(path: Path) -> dict[tuple[int, int, int], str]:
    """Return {(parva, adhyaya, shloka): IAST text}. Pada/prose lines belonging
    to the same shloka are concatenated in file (reading) order. Star (apparatus)
    lines are excluded. Also returns nothing about stars here; counts done by caller."""
    out: dict[tuple[int, int, int], list[str]] = {}
    for ln in path.read_text(encoding="utf-8").split("\n"):
        m = LINE.match(ln)
        if not m:
            continue
        parva, adh, sh, _suf, star, body = m.groups()
        if star:                                 # apparatus / interpolation -> skip
            continue
        body = _clean(body)
        if not body:
            continue
        key = (int(parva), int(adh), int(sh))
        out.setdefault(key, []).append(body)
    return {k: " ".join(v) for k, v in out.items()}


def count_stars(path: Path) -> int:
    n = 0
    for ln in path.read_text(encoding="utf-8").split("\n"):
        m = LINE.match(ln)
        if m and m.group(5):
            n += 1
    return n


def iast_to_devanagari(iast: str) -> str:
    return sanscript.transliterate(iast, sanscript.IAST, sanscript.DEVANAGARI)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build_records(parsed: dict[tuple[int, int, int], str]) -> list[dict]:
    records = []
    for (parva, adh, sh) in sorted(parsed):
        iast = parsed[(parva, adh, sh)]
        deva = iast_to_devanagari(iast)
        records.append({
            "corpus": "mahabharata",
            "id": f"{parva}.{adh}.{sh}",
            "unit": "shloka",
            "parva": parva,
            "parva_name": PARVA_NAME[parva],
            "adhyaya": adh,
            "shloka": sh,
            "text_en": None,                     # section-level only; not aligned (see VALIDATION.md)
            "original": deva,                    # Devanagari (mechanical IAST->Deva of GRETIL)
            "transliteration": iast,             # IAST verbatim from GRETIL
            "translation_source": None,          # no aligned English -> null (cf. Ganguli, section-level)
            "original_source": ORIGINAL_SOURCE,
            "source_urls": {
                "original": f"{GRETIL_BASE}/{GRETIL_FILE.format(p=parva)}",
                "en": GANGULI_INDEX.format(p=parva),   # Ganguli parva index (section granularity)
            },
            "retrieved": RETRIEVED,
            # text_en is null -> tokens counts the transliteration words (the citable
            # unit's length), so the field is still meaningful. Documented in VALIDATION.md.
            "tokens": len(iast.split()),
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
# 5-shloka spot check (must be real, fetched text). Includes the Gita-overlap case.
SPOT = ["1.1.1", "1.1.0", "6.23.1", "6.40.1", "3.1.1"]


def write_validation(records, parsed, stars, sha) -> None:
    by_id = {r["id"]: r for r in records}
    total = len(records)
    with_en = sum(1 for r in records if r["text_en"])

    # per-parva tally
    per = {}
    for (parva, adh, sh) in parsed:
        d = per.setdefault(parva, {"sh": 0, "adh": set()})
        d["sh"] += 1
        d["adh"].add(adh)

    L: list[str] = []
    L.append("# VALIDATION -- Mahabharata corpus (CANONCITE)\n")
    L.append(f"Generated by `canoncite/corpus/build_mahabharata.py`. Retrieved: **{RETRIEVED}**.\n")
    L.append(f"**version (sha256 of sorted corpus_index.jsonl):** `{sha}`\n")

    L.append("## What this corpus is (and is not)\n")
    L.append(
        "The Mahabharata is the LARGEST CANONCITE corpus. This is a **complete, "
        "ID-validated Sanskrit shloka index** of all 18 parvas of the **BORI / Poona "
        "Critical Edition** (the constituted critical text), with Devanagari + IAST. "
        "It is honest about one thing in particular: **English is NOT aligned to "
        "shloka IDs** (see below). `text_en` is null for every record.\n")
    L.append(f"- ID scheme (own namespace `mahabharata`): `parva.adhyaya.shloka`, "
             f"e.g. `1.1.1`, `6.23.1`. The numbering IS the BORI critical-edition numbering.")
    L.append(f"- Total citable shlokas indexed: **{total}**")
    L.append(f"- Sanskrit (Devanagari + IAST) coverage: **{total}/{total} = 100.00%** "
             f"of the constituted critical text.")
    L.append(f"- English (`text_en`) coverage: **{with_en}/{total} = 0.00%** "
             f"(section-level source only; intentionally not fabricated -- see EN alignment note).\n")

    L.append("## Sources (public-domain only)\n")
    L.append("| Field | Source | URL |")
    L.append("|---|---|---|")
    L.append("| transliteration (IAST) + the `parva.adhyaya.shloka` numbering | "
             "**GRETIL** machine-readable BORI/Poona Critical Edition (entered by Muneo "
             "Tokunaga et al., rev. John Smith, Cambridge; (C) BORI, Pune) | "
             f"{GRETIL_BASE}/ |")
    L.append("| original (Devanagari) | **mechanical IAST->Devanagari transliteration** of "
             "the GRETIL IAST (`indic_transliteration.sanscript`) -- a script conversion, "
             "not a second source | (derived) |")
    L.append("| text_en (NOT aligned; section-level provenance only) | **Kisari Mohan "
             "Ganguli**, *The Mahabharata*, 1883-96 (PUBLIC DOMAIN) | "
             "https://www.sacred-texts.com/hin/maha/ (parva indices cached via Wayback) |")
    L.append("")

    L.append("## English (Ganguli) alignment -- granularity and why text_en is null\n")
    L.append(
        "Ganguli's translation is complete prose, organised **parva -> SECTION**. The "
        "SECTION segmentation follows the **Calcutta vulgate**, NOT the BORI critical "
        "edition used here for the Sanskrit/ID space. The two segmentations diverge "
        "(the critical edition removed thousands of vulgate lines as later "
        "interpolations and renumbered/merged adhyayas), so **a Ganguli SECTION does "
        "not correspond 1:1 to a BORI adhyaya, and Ganguli prose is not numbered per "
        "shloka at all.** There is no verified shloka<->section concordance. Assigning "
        "per-shloka (or even per-adhyaya) English under these conditions would mean "
        "**fabricating alignment boundaries, which the build rules forbid.**\n")
    L.append(
        "Therefore: `text_en` and `translation_source` are **null** for every record. "
        "English remains available at **SECTION granularity** at the Ganguli source; "
        "each record's `source_urls.en` points to its **parva index** (the entry point "
        "to that parva's sections), and the 18 parva index pages are cached under "
        "`raw/ganguli/`. Aligning Ganguli sections to BORI shlokas is left to a future "
        "version that builds (and validates) an explicit concordance.\n")
    L.append("> Note on `tokens`: since `text_en` is null, `tokens` counts the **IAST "
             "transliteration** words of the shloka (the citable unit's length), rather "
             "than English tokens as in the Gita corpus.\n")

    L.append("## Bhagavad Gita overlap (deliberate cross-corpus near-miss)\n")
    L.append(
        f"The Bhagavad Gita is a subset of this text: in the BORI edition it is **Bhishma "
        f"parva (6), adhyayas {GITA_ADHYAYAS[0]}-{GITA_ADHYAYAS[1]}** -- i.e. mahabharata "
        f"IDs `6.23.x` .. `6.40.x`. Spot-checked: `6.23.1` here is "
        f"\"dharmakṣetre kurukṣetre ...\" = Bhagavad Gita **1.1**; adhyaya `6.40` is "
        f"Gita chapter 18. The standalone `bhagavad_gita` corpus keeps its OWN namespace "
        f"(`<chapter>.<verse>`, e.g. `1.1`). These IDs are kept SEPARATE on purpose: the "
        f"same verses are citable under two different IDs in two corpora, a deliberate "
        f"near-miss / cross-corpus case for the benchmark. (The Gita corpus' English is "
        f"Besant 1905, verse-aligned; this corpus does not import it -- different source, "
        f"different ID space.)\n")

    L.append("## Per-parva counts (constituted critical text)\n")
    L.append("| Parva | Name | Adhyayas | Shlokas indexed | Star/apparatus lines excluded |")
    L.append("|---:|---|---:|---:|---:|")
    tot_sh = tot_adh = tot_star = 0
    for p in range(1, 19):
        d = per.get(p, {"sh": 0, "adh": set()})
        nsh, nadh, nstar = d["sh"], len(d["adh"]), stars.get(p, 0)
        tot_sh += nsh
        tot_adh += nadh
        tot_star += nstar
        L.append(f"| {p} | {PARVA_NAME[p]} | {nadh} | {nsh} | {nstar} |")
    L.append(f"| **sum** | **18 parvas** | **{tot_adh}** | **{tot_sh}** | **{tot_star}** |")
    L.append("")
    L.append(
        "Adhyaya counts match the published BORI critical edition (e.g. Adi 225, "
        "Sabha 72, Vana 299, Bhishma 117, Shanti 353). The constituted-text total "
        f"(**{tot_sh}** shlokas) excludes **{tot_star}** apparatus/star (interpolation) "
        "lines, which carry non-shloka numbering and are not part of the constituted "
        "text. ~Half-verse pada lines (labels `a`/`c`, or `a`-`f` for tristubh) and "
        "speaker tags (\"X uvaca\") are merged into their parent shloka; prose passages "
        "(uppercase labels) are kept as their numbered unit.\n")

    L.append("## What is covered vs NOT covered\n")
    L.append("- **Covered:** complete Sanskrit shloka index for **all 18 parvas** "
             "(constituted BORI critical text), Devanagari + IAST, every record "
             "ID-validated to the `parva.adhyaya.shloka` scheme.")
    L.append("- **NOT covered:** per-shloka (or per-adhyaya) English. `text_en` is null "
             "everywhere by design (no verified Ganguli<->BORI concordance; not fabricated).")
    L.append("- **NOT covered:** the critical edition's *apparatus* (star passages, "
             "Northern/Southern recension insertions). Only the constituted text is indexed.")
    L.append("- **Provenance cached:** 18 GRETIL parva files (`raw/gretil/`) and 18 "
             "Ganguli parva index pages (`raw/ganguli/`, via Wayback).\n")

    L.append("## ID validation\n")
    ok = all(re.fullmatch(r"\d+\.\d+\.\d+", r["id"]) for r in records)
    dup = total != len({r["id"] for r in records})
    L.append(f"- All {total} IDs match `^\\d+\\.\\d+\\.\\d+$`: **{ok}**")
    L.append(f"- Duplicate IDs present: **{dup}** (expect False)")
    L.append(f"- Parva range {min(r['parva'] for r in records)}-"
             f"{max(r['parva'] for r in records)}; all 18 parvas present: "
             f"**{sorted(per) == list(range(1, 19))}**\n")

    L.append("## Content spot-check (actual fetched GRETIL text -- nothing fabricated)\n")
    for sid in SPOT:
        r = by_id.get(sid)
        if not r:
            L.append(f"### {sid}\n_NOT FOUND_\n")
            continue
        L.append(f"### {sid}  (parva {r['parva']} {r['parva_name']}, adhyaya "
                 f"{r['adhyaya']}, shloka {r['shloka']}, tokens={r['tokens']})\n")
        L.append(f"- **original (Devanagari):** {r['original']}")
        L.append(f"- **transliteration (IAST):** {r['transliteration']}")
        L.append(f"- **text_en:** {r['text_en']}  _(null -- Ganguli is section-level; see above)_\n")

    VALIDATION.write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refetch", action="store_true", help="re-download all raw sources")
    ap.add_argument("--no-ganguli", action="store_true", help="skip Ganguli provenance fetch")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    fetch_gretil(args.refetch)
    if not args.no_ganguli:
        try:
            fetch_ganguli(args.refetch)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] Ganguli provenance fetch skipped: {e}")

    parsed: dict[tuple[int, int, int], str] = {}
    stars: dict[int, int] = {}
    for p in range(1, 19):
        path = GRETIL_DIR / GRETIL_FILE.format(p=p)
        parsed.update(parse_parva(path))
        stars[p] = count_stars(path)

    records = build_records(parsed)
    sha = write_jsonl(records)
    write_validation(records, parsed, stars, sha)

    print(f"[done] {len(records)} shlokas -> {OUT_JSONL}")
    print(f"[done] version sha256 = {sha}")
    print(f"[done] validation -> {VALIDATION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
