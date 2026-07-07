#!/usr/bin/env python3
"""Reproducible builder for the frozen Constitution of India corpus (CANONCITE).

Produces ``canoncite/data/corpora/constitution_india/corpus_index.jsonl`` -- one
JSON object per citable unit of the Constitution of India, plus a
``VALIDATION.md`` report and a version (sha256) line.

Citable unit = **Article** (with an optional **clause**-level layer for articles
whose text is a clean, sequentially-numbered enumeration).

Citation ID scheme:
    * article : ``Art. 21``, ``Art. 21A``, ``Art. 368``, ``Art. 243ZG``
    * clause  : ``Art. 19(1)``, ``Art. 368(2)``   (top-level numbered clause)
    * preamble: ``Preamble``                       (one special non-article row)

The example ``Art. 19(1)(a)`` references a *sub*-clause; this corpus materialises
article rows and top-level numbered clause rows. Sub-clause depth ``(a)/(b)`` is
NOT separately materialised (see "Granularity" in VALIDATION.md) -- the (a)/(b)
text remains verbatim inside its parent clause row, never dropped.

PUBLIC-DOMAIN source (the Constitution of India carries no copyright):

  * Primary, machine-readable: the **civictech-India/constitution-of-india**
    open dataset (``constitution_of_india.json``) -- the Government of India text
    of every Article 1..395 plus inserted articles (21A, 31A-D, 51A, the 243- and
    371-series, 300A, 323A/B, ...), served as structured JSON:

        https://raw.githubusercontent.com/civictech-India/constitution-of-india/main/constitution_of_india.json

  * Gap fill: the civic dataset is missing one *live* article, **Article 320**
    (Functions of Public Service Commissions). Its verbatim text is supplied from
    the public-domain Government of India text as reproduced at
    constitutionofindia.net and embedded below (cached to raw/ for reproducibility):

        https://www.constitutionofindia.net/articles/article-320-functions-of-public-service-commissions/

CRITICAL RULE honoured throughout: **no article text is ever invented.** Every
``text_en`` value comes from the fetched source JSON (or, for Art. 320, from the
embedded fetched supplement). Articles that the source omits entirely (genuinely
*repealed/omitted* articles) are reported honestly in VALIDATION.md and are NOT
fabricated. Articles present but repealed carry the source's own repeal note as
their verbatim text.

Re-runnable: fetches into raw/ only if the cache is absent (use --refetch to
force), then parses from cache -> deterministic output.

Usage:
    python canoncite/corpus/build_constitution_india.py            # build (fetch if missing)
    python canoncite/corpus/build_constitution_india.py --refetch  # re-download source JSON
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
DATA = ROOT / "data" / "corpora" / "constitution_india"
RAW = DATA / "raw"
CIVIC_RAW = RAW / "constitution_of_india.json"
ART320_RAW = RAW / "article_320_supplement.json"
OUT_JSONL = DATA / "corpus_index.jsonl"
VALIDATION = DATA / "VALIDATION.md"

RETRIEVED = "2026-06-30"
UA = "CanonciteCorpusBuilder/1.0 (research; public-domain corpus build)"
TRANSLATION_SOURCE = "GoI_public_domain"

CIVIC_URL = ("https://raw.githubusercontent.com/civictech-India/"
             "constitution-of-india/main/constitution_of_india.json")
CIVIC_HOME = "https://github.com/civictech-India/constitution-of-india"
ART320_URL = ("https://www.constitutionofindia.net/articles/"
              "article-320-functions-of-public-service-commissions/")

# ---------------------------------------------------------------------------
# Article 320 supplement -- verbatim public-domain GoI text (the one live
# article the civic dataset omits). Fetched from ART320_URL and embedded here so
# the build is fully reproducible offline; written to raw/ on build.
# ---------------------------------------------------------------------------
ART320 = {
    "article": "320",
    "title": "Functions of Public Service Commissions",
    "source_url": ART320_URL,
    "description": (
        "(1) It shall be the duty of the Union and the State Public Service "
        "Commissions to conduct examinations for appointments to the services of "
        "the Union and the services of the State respectively.\n\n"
        "(2) It shall also be the duty of the Union Public Service Commission, if "
        "requested by any two or more States so to do, to assist those States in "
        "framing and operating schemes of joint recruitment for any services for "
        "which candidates possessing special qualifications are required.\n\n"
        "(3) The Union Public Service Commission or the State Public Service "
        "Commission, as the case may be, shall be consulted—\n"
        "(a) on all matters relating to methods of recruitment to civil services "
        "and for civil posts;\n"
        "(b) on the principles to be followed in making appointments to civil "
        "services and posts and in making promotions and transfers from one "
        "service to another and on the suitability of candidates for such "
        "appointments, promotions or transfers;\n"
        "(c) on all disciplinary matters affecting a person serving under the "
        "Government of India or the Government of a State in a civil capacity, "
        "including memorials or petitions relating to such matters;\n"
        "(d) on any claim by or in respect of a person who is serving or has "
        "served under the Government of India or the Government of a State or "
        "under the Crown in India or under the Government of an Indian State, in a "
        "civil capacity, that any costs incurred by him in defending legal "
        "proceedings instituted against him in respect of acts done or purporting "
        "to be done in the execution of his duty should be paid out of the "
        "Consolidated Fund of India, or, as the case may be, out of the "
        "Consolidated Fund of the State;\n"
        "(e) on any claim for the award of a pension in respect of injuries "
        "sustained by a person while serving under the Government of India or the "
        "Government of a State or under the Crown in India or under the Government "
        "of an Indian State, in a civil capacity, and any question as to the "
        "amount of any such award, and it shall be the duty of a Public Service "
        "Commission to advise on any matter so referred to them and on any other "
        "matter which the President, or, as the case may be, the Governor of the "
        "State, may refer to them:\n"
        "Provided that the President as respects the all-India services and also "
        "as respects other services and posts in connection with the affairs of "
        "the Union, and the Governor, as respects other services and posts in "
        "connection with the affairs of a State, may make regulations specifying "
        "the matters in which either generally, or in any particular class of case "
        "or in any particular circumstances, it shall not be necessary for a "
        "Public Service Commission to be consulted.\n\n"
        "(4) Nothing in clause (3) shall require a Public Service Commission to be "
        "consulted as respects the manner in which any provision referred to in "
        "clause (4) of article 16 may be made or as respects the manner in which "
        "effect may be given to the provisions of article 335.\n\n"
        "(5) All regulations made under the proviso to clause (3) by the President "
        "or the Governor of a State shall be laid for not less than fourteen days "
        "before each House of Parliament or the House or each House of the "
        "Legislature of the State, as the case may be, as soon as possible after "
        "they are made, and shall be subject to such modifications, whether by way "
        "of repeal or amendment, as both Houses of Parliament or the House or both "
        "Houses of the Legislature of the State may make during the session in "
        "which they are so laid."
    ),
}

# ---------------------------------------------------------------------------
# Part structure (Parts I..XXII). Each Part is keyed by the article identifier
# at which it begins; a Part runs until the next Part's start. Start markers are
# in strictly increasing article order, so each article is assigned to the last
# Part whose start <= the article. Sub-parts (IVA, IXA, IXB, XIVA) carry letter
# Roman labels. This mapping is the standard, well-established article->Part
# division of the Constitution of India.
# ---------------------------------------------------------------------------
PARTS: list[tuple[str, str, str]] = [
    # (start_article_id, roman_label, part_name)
    ("1",      "I",     "The Union and its Territory"),
    ("5",      "II",    "Citizenship"),
    ("12",     "III",   "Fundamental Rights"),
    ("36",     "IV",    "Directive Principles of State Policy"),
    ("51A",    "IVA",   "Fundamental Duties"),
    ("52",     "V",     "The Union"),
    ("152",    "VI",    "The States"),
    ("238",    "VII",   "The States in Part B of the First Schedule (Repealed)"),
    ("239",    "VIII",  "The Union Territories"),
    ("243",    "IX",    "The Panchayats"),
    ("243P",   "IXA",   "The Municipalities"),
    ("243ZH",  "IXB",   "The Co-operative Societies"),
    ("244",    "X",     "The Scheduled and Tribal Areas"),
    ("245",    "XI",    "Relations between the Union and the States"),
    ("264",    "XII",   "Finance, Property, Contracts and Suits"),
    ("301",    "XIII",  "Trade, Commerce and Intercourse within the Territory of India"),
    ("308",    "XIV",   "Services under the Union and the States"),
    ("323A",   "XIVA",  "Tribunals"),
    ("324",    "XV",    "Elections"),
    ("330",    "XVI",   "Special Provisions Relating to Certain Classes"),
    ("343",    "XVII",  "Official Language"),
    ("352",    "XVIII", "Emergency Provisions"),
    ("361",    "XIX",   "Miscellaneous"),
    ("368",    "XX",    "Amendment of the Constitution"),
    ("369",    "XXI",   "Temporary, Transitional and Special Provisions"),
    ("393",    "XXII",  "Short Title, Commencement, Authoritative Text in Hindi and Repeals"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_WS = re.compile(r"\s+")
_ART_RE = re.compile(r"^(\d+)([A-Z]*)$")


def normalize_artno(raw: str) -> str:
    """Source-side ArtNo cleanup: strip spaces (the civic dataset stores the
    inserted article 239AA as the malformed token '239 A A')."""
    return raw.replace(" ", "").strip()


def art_key(artno: str) -> tuple[int, str]:
    """Sort/ordering key: (base integer, uppercase letter suffix). Letter
    suffixes compare lexicographically, which reproduces the constitutional
    insertion order ('' < 'A' < 'AA' < 'AB' < 'B' ... < 'Z' < 'ZA' < 'ZH')."""
    m = _ART_RE.match(artno)
    if not m:
        raise ValueError(f"unparseable article id: {artno!r}")
    return (int(m.group(1)), m.group(2))


# precompute part lookup as ordered (key, roman, name)
_PART_STARTS = [(art_key(s), roman, name) for s, roman, name in PARTS]


def part_for(artno: str) -> tuple[str, str]:
    """Return (roman, name) of the Part containing the given article."""
    k = art_key(artno)
    chosen = _PART_STARTS[0]
    for start_key, roman, name in _PART_STARTS:
        if start_key <= k:
            chosen = (start_key, roman, name)
        else:
            break
    return chosen[1], chosen[2]


def clean_text(text: str) -> str:
    """Collapse all whitespace to single spaces and strip; never alter words.
    Mirrors the Bible builder's clean_text for cross-corpus consistency."""
    return _WS.sub(" ", text.replace("\xa0", " ")).strip()


def is_repealed(text: str) -> bool:
    """True if the article's verbatim text is itself a repeal/omission note
    (i.e. the article number survives but the substantive text was removed)."""
    s = text.strip()
    return bool(
        re.match(r"^\[.*?\]\s*(Rep\.|Omitted)", s)
        or re.match(r"^Omitted by", s)
        or re.match(r"^Rep\. by", s)
    )


def split_clauses(raw_desc: str) -> list[tuple[str, str]] | None:
    """Split a raw (newline-bearing) article description into top-level numbered
    clauses. Only splits on a '(N)' marker at the start of the text or start of a
    line (so inline references like 'clause (4) of article 16' are NOT split on),
    and only accepts the split if the clause numbers form a clean 1..k sequence;
    otherwise returns None (article kept whole). Pure segmentation of verbatim
    text -- no words added or removed."""
    ms = list(re.finditer(r"(?:\A|\n)\s*\((\d+)\)\s", raw_desc))
    if len(ms) < 2:
        return None
    nums = [int(m.group(1)) for m in ms]
    if nums != list(range(1, len(nums) + 1)):
        return None
    out: list[tuple[str, str]] = []
    for i, m in enumerate(ms):
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(raw_desc)
        out.append((m.group(1), raw_desc[start:end]))
    return out


# ---------------------------------------------------------------------------
# Fetch (only when cache missing)
# ---------------------------------------------------------------------------
def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_sources(refetch: bool = False) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    # primary civic dataset
    if refetch or not CIVIC_RAW.exists():
        for attempt in range(4):
            try:
                data = _get(CIVIC_URL)
                obj = json.loads(data)
                if isinstance(obj, list) and obj and "article" in obj[0]:
                    CIVIC_RAW.write_bytes(data)
                    print(f"[fetch] civic dataset -> {CIVIC_RAW} ({len(obj)} entries)")
                    break
            except Exception as e:  # noqa: BLE001
                print(f"[warn] civic fetch attempt {attempt}: {e}")
            time.sleep(5)
        else:
            raise RuntimeError("could not fetch civic constitution_of_india.json")
    # Article 320 supplement: write the embedded verbatim text (its provenance
    # URL is recorded so the cache is auditable).
    if refetch or not ART320_RAW.exists():
        ART320_RAW.write_text(
            json.dumps(ART320, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[write] Article 320 supplement -> {ART320_RAW}")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def load_source_entries() -> list[dict]:
    """Return the merged source entries (civic dataset + Art. 320 supplement),
    each as {artno, title, description, source_url}. Preamble kept as artno='0'."""
    civic = json.loads(CIVIC_RAW.read_text("utf-8"))
    supp = json.loads(ART320_RAW.read_text("utf-8"))
    entries: list[dict] = []
    seen: set[str] = set()
    for e in civic:
        artno = normalize_artno(str(e["article"]))
        seen.add(artno)
        entries.append({
            "artno": artno,
            "title": (e.get("title") or "").strip(),
            "description": e.get("description") or "",
            "source_url": CIVIC_URL,
        })
    # insert the missing live Article 320
    if supp["article"] not in seen:
        entries.append({
            "artno": normalize_artno(supp["article"]),
            "title": supp["title"].strip(),
            "description": supp["description"],
            "source_url": supp["source_url"],
        })
    return entries


def build_records() -> tuple[list[dict], dict]:
    entries = load_source_entries()
    records: list[dict] = []
    meta = {
        "articles": 0, "clause_rows": 0, "repealed_present": [],
        "preamble": False, "art320_filled": False, "filled_via_supplement": [],
    }
    for e in entries:
        artno = e["artno"]
        title = e["title"]
        raw_desc = e["description"]
        text_en = clean_text(raw_desc)
        source = e["source_url"]
        if source != CIVIC_URL:
            meta["filled_via_supplement"].append(artno)

        if artno == "0":  # Preamble -- special non-article row
            records.append({
                "corpus": "constitution_india",
                "id": "Preamble",
                "unit": "preamble",
                "part": "Preamble",
                "article": None,
                "clause": None,
                "heading": title or "Preamble",
                "text_en": text_en or None,
                "translation_source": TRANSLATION_SOURCE if text_en else None,
                "source_urls": {"en": source},
                "retrieved": RETRIEVED,
                "tokens": len(text_en.split()) if text_en else 0,
            })
            meta["preamble"] = True
            continue

        roman, _name = part_for(artno)
        if is_repealed(raw_desc):
            meta["repealed_present"].append(artno)
        if artno == "320" and source != CIVIC_URL:
            meta["art320_filled"] = True

        # article-level row
        records.append({
            "corpus": "constitution_india",
            "id": f"Art. {artno}",
            "unit": "article",
            "part": roman,
            "article": artno,
            "clause": None,
            "heading": title or None,
            "text_en": text_en or None,
            "translation_source": TRANSLATION_SOURCE if text_en else None,
            "source_urls": {"en": source},
            "retrieved": RETRIEVED,
            "tokens": len(text_en.split()) if text_en else 0,
        })
        meta["articles"] += 1

        # optional clause-level rows
        clauses = split_clauses(raw_desc)
        if clauses:
            for cno, ctext in clauses:
                ctxt = clean_text(ctext)
                records.append({
                    "corpus": "constitution_india",
                    "id": f"Art. {artno}({cno})",
                    "unit": "clause",
                    "part": roman,
                    "article": artno,
                    "clause": cno,
                    "heading": title or None,
                    "text_en": ctxt or None,
                    "translation_source": TRANSLATION_SOURCE if ctxt else None,
                    "source_urls": {"en": source},
                    "retrieved": RETRIEVED,
                    "tokens": len(ctxt.split()) if ctxt else 0,
                })
                meta["clause_rows"] += 1
    return records, meta


def _sort_key(r: dict) -> tuple:
    if r["unit"] == "preamble":
        return (0, "", 0, 0)
    base, suf = art_key(r["article"])
    is_clause = 1 if r["unit"] == "clause" else 0
    cl = int(r["clause"]) if r["clause"] is not None else 0
    return (base, suf, is_clause, cl)


def write_jsonl(records: list[dict]) -> str:
    ordered = sorted(records, key=_sort_key)
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in ordered]
    blob = "\n".join(lines) + "\n"
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(blob, encoding="utf-8")
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------
# Articles genuinely OMITTED/repealed and therefore absent from the source text
# (no substantive text exists; reported, never fabricated). Verified against the
# numeric gap analysis 1..395.
KNOWN_OMITTED = {
    232: "Omitted (Constitution (7th Amendment) Act, 1956)",
    242: "Omitted (Constitution (7th Amendment) Act, 1956) -- Coorg",
    259: "Omitted (Constitution (7th Amendment) Act, 1956)",
    272: "Omitted (Constitution (80th Amendment) Act, 2000)",
    278: "Omitted (Constitution (7th Amendment) Act, 1956)",
    291: "Omitted (Constitution (26th Amendment) Act, 1971) -- privy purses",
    306: "Omitted (Constitution (7th Amendment) Act, 1956)",
    314: "Omitted (Constitution (28th Amendment) Act, 1972)",
    362: "Omitted (Constitution (26th Amendment) Act, 1971)",
    379: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    380: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    381: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    382: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    383: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    384: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    385: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    386: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    387: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    388: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    389: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    390: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
    391: "Omitted (Constitution (7th Amendment) Act, 1956) -- transitional",
}

SPOT = ["Art. 21", "Art. 14", "Art. 19(1)", "Art. 368", "Art. 320"]


def write_validation(records: list[dict], meta: dict, sha: str) -> None:
    by_id = {r["id"]: r for r in records}
    art_rows = [r for r in records if r["unit"] == "article"]
    clause_rows = [r for r in records if r["unit"] == "clause"]
    total = len(records)
    art_present_nums = set()
    for r in art_rows:
        art_present_nums.add(art_key(r["article"])[0])
    with_text = sum(1 for r in records if r["text_en"])
    null_text = [r["id"] for r in records if not r["text_en"]]

    # numeric gaps 1..395
    numeric_gaps = [n for n in range(1, 396) if n not in art_present_nums]
    unexpected_gaps = [n for n in numeric_gaps if n not in KNOWN_OMITTED]

    # per-part counts
    part_counts: dict[str, int] = {}
    for r in art_rows:
        part_counts[r["part"]] = part_counts.get(r["part"], 0) + 1

    L: list[str] = []
    L.append("# VALIDATION -- Constitution of India corpus (CANONCITE)\n")
    L.append(f"Generated by `canoncite/corpus/build_constitution_india.py`. "
             f"Retrieved: **{RETRIEVED}**.\n")
    L.append(f"**version (sha256 of sorted corpus_index.jsonl):** `{sha}`\n")

    L.append("## Sources (public-domain only)\n")
    L.append("The text of the Constitution of India is a Government of India work and "
             "carries **no copyright** (public domain).\n")
    L.append("| Field | Source | URL |")
    L.append("|---|---|---|")
    L.append("| text_en (primary) | Government of India text, machine-readable via the "
             "**civictech-India/constitution-of-india** open dataset "
             "(`constitution_of_india.json`) | "
             f"{CIVIC_URL} |")
    L.append("| text_en (Art. 320 fill) | GoI public-domain text of Article 320, "
             "reproduced at constitutionofindia.net (the one live article the civic "
             "dataset omits) | "
             f"{ART320_URL} |")
    L.append(f"| dataset home | civictech-India/constitution-of-india | {CIVIC_HOME} |")
    L.append("")
    L.append(f"- **translation_source** field value: `{TRANSLATION_SOURCE}`")
    L.append("- **ID scheme:** `Art. N` (article), `Art. N(c)` (top-level clause), "
             "`Preamble` (one special row). Inserted articles keep their letter "
             "suffix (e.g. `Art. 21A`, `Art. 300A`, `Art. 243ZG`). The source token "
             "`239 A A` is normalised to `239AA`.\n")

    L.append("## Granularity\n")
    L.append("- **Primary citable unit = Article.** Every article row carries the full "
             "verbatim article text in `text_en`.")
    L.append("- **Clause layer (optional):** for articles whose text is a clean, "
             "sequentially-numbered enumeration `(1) (2) (3)...`, an extra row per "
             "top-level clause is emitted (`unit: clause`). The split is pure "
             "segmentation of the verbatim text -- it triggers only when the clause "
             "numbers form an unbroken `1..k` run and the marker sits at a line start "
             "(so inline references such as 'clause (4) of article 16' are never split "
             "on). Articles without such a run (e.g. Art. 14, Art. 21) have no clause "
             "rows; their full text lives in the single article row.")
    L.append("- **Sub-clause depth NOT materialised:** the citation example "
             "`Art. 19(1)(a)` references a sub-clause `(a)`. Sub-clause `(a)/(b)/(c)` "
             "text is retained verbatim *inside* its parent clause row but is not split "
             "into its own row. No `(a)/(b)` text is ever dropped.\n")

    L.append("## Coverage summary\n")
    L.append(f"- Total rows (ID space `U`): **{total}** "
             f"= {len(art_rows)} article + {len(clause_rows)} clause "
             f"+ {'1 preamble' if meta['preamble'] else '0 preamble'}")
    L.append(f"- Article rows: **{len(art_rows)}**")
    L.append(f"- Distinct base article numbers present (of 1..395): "
             f"**{len(art_present_nums)}**")
    L.append(f"- Articles genuinely omitted/repealed (absent from source, expected): "
             f"**{len(KNOWN_OMITTED)}**")
    present_plus_omitted = len(art_present_nums)
    # coverage of the *existing* (non-omitted) articles
    expected_live_base = 395 - len([n for n in KNOWN_OMITTED])
    L.append(f"- Base-number coverage of **live** articles: "
             f"**{len(art_present_nums)}/{expected_live_base + 0} live base numbers "
             f"present** (live = 1..395 minus the {len(KNOWN_OMITTED)} omitted).")
    pct = 100.0 * len(art_present_nums) / expected_live_base if expected_live_base else 0
    L.append(f"- Live base-number coverage: **{pct:.2f}%**")
    L.append(f"- Text present (non-null `text_en`): **{with_text}/{total} = "
             f"{100*with_text/total:.2f}%**")
    L.append(f"- Rows flagged with null text: {null_text or 'none'}")
    L.append(f"- Article 320 (live, missing from civic dataset) filled from supplement: "
             f"**{'YES' if meta['art320_filled'] else 'NO'}**\n")

    L.append("## Part coverage (Parts I-XXII)\n")
    L.append("| Part | Name | Article rows |")
    L.append("|---|---|---:|")
    for _start, roman, name in PARTS:
        L.append(f"| {roman} | {name} | {part_counts.get(roman, 0)} |")
    L.append(f"| | **TOTAL article rows** | **{len(art_rows)}** |")
    L.append("")
    parts_empty = [roman for _s, roman, _n in PARTS if part_counts.get(roman, 0) == 0]
    L.append(f"- Parts with zero article rows: "
             f"{parts_empty or 'none'} "
             f"(Part VII is the repealed 'States in Part B' part -- Article 238 is "
             f"present only as its omission note).\n")

    L.append("## Repealed / omitted articles (honest gap report)\n")
    L.append("### (a) Present in corpus, text IS a repeal note (article number survives)\n")
    if meta["repealed_present"]:
        for a in sorted(meta["repealed_present"], key=art_key):
            r = by_id.get(f"Art. {a}")
            note = (r["text_en"][:120] + "...") if r and r["text_en"] else "?"
            L.append(f"- `Art. {a}` -- {note}")
    else:
        L.append("- none")
    L.append("")
    L.append("### (b) Omitted entirely -- absent from source, NOT fabricated\n")
    L.append("These base numbers have no substantive constitutional text (repealed and "
             "removed). They are correctly absent and are reported here for honesty:\n")
    for n in sorted(KNOWN_OMITTED):
        L.append(f"- `Art. {n}` -- {KNOWN_OMITTED[n]}")
    L.append("")
    if unexpected_gaps:
        L.append(f"### (c) UNEXPECTED gaps (live articles missing -- INVESTIGATE)\n")
        L.append(f"- {unexpected_gaps}")
    else:
        L.append("### (c) Unexpected gaps\n- **none** -- every missing base number is a "
                 "known omitted/repealed article (Article 320, a live article missing "
                 "from the civic dataset, was sourced separately and is present).")
    L.append("")

    L.append("## Content spot-check (actual fetched text -- verify nothing fabricated)\n")
    for sid in SPOT:
        r = by_id.get(sid)
        if not r:
            L.append(f"### {sid}\n_NOT FOUND_\n")
            continue
        L.append(f"### {sid}  (part {r['part']}, article {r['article']}, "
                 f"clause {r['clause']}, heading: {r['heading']}, tokens={r['tokens']})\n")
        L.append(f"- **text_en:** {r['text_en']}\n")

    L.append("## Reproducibility\n")
    L.append("- Raw source cached under `raw/` (`constitution_of_india.json`, "
             "`article_320_supplement.json`). Re-run with `--refetch` to re-download.")
    L.append("- Output is deterministically sorted by (article base, letter suffix, "
             "clause) so the sha256 above is stable across runs.\n")

    VALIDATION.write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refetch", action="store_true",
                    help="re-download the source dataset")
    args = ap.parse_args()

    fetch_sources(args.refetch)
    records, meta = build_records()
    sha = write_jsonl(records)
    write_validation(records, meta, sha)

    art_rows = sum(1 for r in records if r["unit"] == "article")
    clause_rows = sum(1 for r in records if r["unit"] == "clause")
    with_text = sum(1 for r in records if r["text_en"])
    total = len(records)
    print(f"[done] {total} rows ({art_rows} article + {clause_rows} clause + preamble) "
          f"-> {OUT_JSONL}")
    print(f"[done] text present {with_text}/{total} = {100*with_text/total:.2f}%")
    print(f"[done] Art. 320 filled from supplement: {meta['art320_filled']}")
    print(f"[done] version sha256 = {sha}")
    print(f"[done] validation -> {VALIDATION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
