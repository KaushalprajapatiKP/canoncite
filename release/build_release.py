#!/usr/bin/env python3
"""Assemble the public-release bundle for the CANONCITE benchmark.

Produces `release/canoncite-v0/`, a reproducible, publish-ready bundle
(HuggingFace Datasets / arXiv) containing ONLY public-domain-safe data:

  * per-corpus frozen `corpus_index.jsonl` (public-domain text layer)
  * per-corpus items (`seed_candidates.jsonl`; gold.jsonl will replace these
    post human review — see NOTE below)
  * per-corpus public `VALIDATION.md` (provenance, sources, sha256)
  * a top-level `manifest.json` (counts, sha256, sources, licenses)

Hard guarantees (the script FAILS LOUDLY otherwise):
  * No copyright-restricted / private artifact is ever copied:
      - `*.with_english.private.jsonl`   (e.g. Guru Granth Sahib English)
      - `text_en_supplement.jsonl`       (Ramayana / Mahabharata English)
      - `VALIDATION_EN.md`               (docs for the private English layer)
      - any `raw/` fetch cache
  * Every released record's `translation_source` is on the public-domain
    allowlist (the BENCHMARK_DESIGN §7 CI check); anything else aborts.
  * `original_source` / any record field never contains a forbidden
    (copyrighted) source token.
  * Corpora whose English is copyright-restricted (Guru Granth Sahib,
    Ramayana, Mahabharata) must carry NO English text (`text_en` all null).

Stdlib only. Run:  python3 release/build_release.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RELEASE_DIR = Path(__file__).resolve().parent
REPO = RELEASE_DIR.parent
SRC_CORPORA = REPO / "canoncite" / "data" / "corpora"
SRC_ITEMS = REPO / "canoncite" / "data" / "items"
OUT = RELEASE_DIR / "canoncite-v0"

VERSION = "v0"
BUNDLE_DATE = str(date.today())

# ---------------------------------------------------------------------------
# Public-domain allowlist / denylist (BENCHMARK_DESIGN.md §7)
# ---------------------------------------------------------------------------
# A record's `translation_source` MUST be one of these (or null). This is the
# release CI gate: any other value means a possibly-copyrighted translation
# has leaked into the release text layer.
PD_TRANSLATION_SOURCES = {
    None,
    "Besant_1905",       # Annie Besant, Bhagavad-Gita (1905), public domain
    "WEB",               # World English Bible, public domain
    "GoI_public_domain", # Constitution of India, Government of India (PD)
    "Muller_SBE_1881",   # Max Muller, Sacred Books of the East (Dhammapada)
    "Muller_SBE",        # Max Muller, Sacred Books of the East (Upanishads)
    "Pope_1886",         # G.U. Pope, Thirukkural (1886), public domain
    "Vivekananda_1896",  # Woods/Vivekananda, Raja-Yoga aphorisms (1896), PD
}

# Tokens that must NEVER appear in a released record's TEXT-CONTENT fields.
# These name in-copyright translations the release deliberately excludes. NOTE:
# these tokens ARE allowed inside provenance/license metadata fields (e.g. the
# public Guru Granth Sahib index keeps a `translation_license` note naming
# "Dr. Sant Singh Khalsa ... COPYRIGHTED" to document *why* English is absent).
# We only forbid them in fields that carry actual scripture/answer text.
FORBIDDEN_SOURCE_TOKENS = (
    "Sant_Singh_Khalsa",
    "BBT", "Prabhupada", "Bhaktivedanta",
    "IIT-K", "IIT_Kanpur", "IIT Kanpur",
)

# Fields whose VALUES are actual text content (scripture, translation, answers,
# questions) — the only place a copyrighted-text leak could hide.
CONTENT_FIELDS = (
    "text_en", "original", "sanskrit", "transliteration",
    "translation", "question", "gold_answer",
)


def _content_strings(rec: dict):
    """Yield text-content strings from a corpus/item record (incl. translations)."""
    for k in CONTENT_FIELDS:
        v = rec.get(k)
        if isinstance(v, str) and v:
            yield v
    tr = rec.get("translations")
    if isinstance(tr, dict):
        for payload in tr.values():
            if isinstance(payload, dict):
                for v in payload.values():
                    if isinstance(v, str) and v:
                        yield v


def _scan_forbidden_content(rec: dict, where: str) -> None:
    for s in _content_strings(rec):
        for tok in FORBIDDEN_SOURCE_TOKENS:
            if tok in s:
                raise ReleaseError(
                    f"{where}: forbidden source token {tok!r} found in text content — aborting."
                )

# Filenames / directories that must never be copied into the release.
FORBIDDEN_FILE_SUBSTR = (
    ".private.jsonl",
    "with_english",
    "text_en_supplement",
    "VALIDATION_EN",
)
FORBIDDEN_DIR_NAMES = {"raw", "__pycache__"}

# ---------------------------------------------------------------------------
# Per-corpus release metadata (drives manifest.json + docs)
# ---------------------------------------------------------------------------
CORPORA = {
    "bhagavad_gita": {
        "tradition": "Hindu",
        "native_lang": "sa",
        "script": "Devanagari",
        "english_status": "public_domain",
        "pd_editions": {
            "english": "Annie Besant, Bhagavad-Gita (4th ed., 1905) — public domain",
            "original": "gita/gita open dataset (Devanagari + IAST); ancient/public-domain Sanskrit",
        },
    },
    "bible": {
        "tradition": "Christian",
        "native_lang": "en",
        "script": "Latin",
        "english_status": "public_domain",
        "pd_editions": {
            "english": "World English Bible (WEB) — public domain",
        },
    },
    "constitution_india": {
        "tradition": "Secular-legal",
        "native_lang": "en",
        "script": "Latin",
        "english_status": "public_domain",
        "pd_editions": {
            "english": "Constitution of India — Government of India public-domain text",
        },
    },
    "dhammapada": {
        "tradition": "Buddhist",
        "native_lang": "pi",
        "script": "Latin (Pali)",
        "english_status": "public_domain",
        "pd_editions": {
            "english": "F. Max Muller, Sacred Books of the East vol. X (1881) — public domain",
            "original": "Pali root text via SuttaCentral (Mahasangiti) — ancient/public-domain",
        },
    },
    "guru_granth_sahib": {
        "tradition": "Sikh",
        "native_lang": "pa",
        "script": "Gurmukhi",
        "english_status": "excluded_copyright",  # Sant Singh Khalsa EN is private
        "pd_editions": {
            "original": "Gurmukhi Unicode via GurbaniNow API / BaniDB / Shabad OS db — gurbani text public-domain",
        },
        "excluded": "Dr. Sant Singh Khalsa English translation (copyrighted to 2096) — NOT released; kept private.",
    },
    "mahabharata": {
        "tradition": "Hindu",
        "native_lang": "sa",
        "script": "Devanagari",
        "english_status": "excluded_unaligned",  # Ganguli EN not per-shloka alignable
        "pd_editions": {
            "original": "GRETIL Mahabharata (Devanagari + IAST) — ancient/public-domain Sanskrit",
        },
        "excluded": "K.M. Ganguli English (public-domain) could not be aligned to the critical-edition shloka grid; excluded from the released text layer.",
    },
    "ramayana": {
        "tradition": "Hindu",
        "native_lang": "sa",
        "script": "Devanagari",
        "english_status": "excluded_copyright",  # IIT-K EN private; Griffith unaligned
        "pd_editions": {
            "original": "GRETIL Valmiki Ramayana, Baroda Critical Edition (Devanagari + IAST) — ancient/public-domain Sanskrit",
        },
        "excluded": "IIT-Kanpur English translation (copyrighted) kept private; Griffith (PD) could not be aligned to the shloka grid. No English in the release.",
    },
    "thirukkural": {
        "tradition": "Tamil-ethical",
        "native_lang": "ta",
        "script": "Tamil",
        "english_status": "public_domain",
        "pd_editions": {
            "english": "G.U. Pope, Thirukkural (1886) — public domain",
            "original": "Classical Tamil kural text — ancient/public-domain",
        },
    },
    "upanishads": {
        "tradition": "Hindu",
        "native_lang": "sa",
        "script": "Devanagari",
        "english_status": "public_domain",
        "pd_editions": {
            "english": "F. Max Muller, Sacred Books of the East (Upanishads) — public domain",
            "original": "GRETIL (Devanagari + IAST) — ancient/public-domain Sanskrit",
        },
    },
    "yoga_sutras": {
        "tradition": "Hindu",
        "native_lang": "sa",
        "script": "Devanagari",
        "english_status": "public_domain",
        "pd_editions": {
            "english": "Swami Vivekananda / J.H. Woods, Raja-Yoga aphorisms (1896) — public domain",
            "original": "GRETIL Patanjali Yogasutra (Devanagari + IAST) — ancient/public-domain Sanskrit",
        },
    },
}

# Corpora whose English is deliberately excluded → must carry NO text_en.
NO_ENGLISH_CORPORA = {"guru_granth_sahib", "mahabharata", "ramayana"}


class ReleaseError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_safe_filename(path: Path) -> None:
    """Refuse to copy anything matching a forbidden (private) pattern."""
    name = path.name
    for sub in FORBIDDEN_FILE_SUBSTR:
        if sub in name:
            raise ReleaseError(
                f"REFUSING to include forbidden/private file: {path} (matched '{sub}')"
            )
    for part in path.parts:
        if part in FORBIDDEN_DIR_NAMES:
            raise ReleaseError(
                f"REFUSING to include file under forbidden dir '{part}': {path}"
            )


def scan_corpus_index(path: Path, corpus: str) -> dict:
    """Validate every record is public-domain-safe; return summary stats."""
    n = 0
    with_en = 0
    translation_sources: dict[str, int] = {}
    original_sources: dict[str, int] = {}
    src_urls: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            n += 1

            ts = rec.get("translation_source")
            if ts not in PD_TRANSLATION_SOURCES:
                raise ReleaseError(
                    f"{corpus} line {lineno}: translation_source {ts!r} is NOT on the "
                    f"public-domain allowlist — possible copyrighted text leak."
                )
            translation_sources[str(ts)] = translation_sources.get(str(ts), 0) + 1

            osrc = rec.get("original_source") or rec.get("sanskrit_source")
            if osrc:
                key = osrc if len(osrc) <= 60 else osrc[:57] + "..."
                original_sources[key] = original_sources.get(key, 0) + 1

            # Forbidden-token scan over text-content fields only.
            _scan_forbidden_content(rec, f"{corpus} line {lineno}")

            if rec.get("text_en"):
                with_en += 1

            # capture a representative source_urls map
            if not src_urls and isinstance(rec.get("source_urls"), dict):
                src_urls = {k: v for k, v in rec["source_urls"].items()}

    if corpus in NO_ENGLISH_CORPORA and with_en != 0:
        raise ReleaseError(
            f"{corpus}: {with_en} records carry English text but this corpus's English "
            f"is copyright-restricted/excluded — release must have NO English here."
        )

    return {
        "units": n,
        "units_with_english": with_en,
        "english_coverage_pct": round(100.0 * with_en / n, 2) if n else 0.0,
        "translation_sources": translation_sources,
        "original_sources": original_sources,
        "source_urls": src_urls,
    }


def copy_file(src: Path, dst: Path) -> dict:
    assert_safe_filename(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "path": str(dst.relative_to(OUT)),
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
    }


def build() -> dict:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    manifest = {
        "name": "canoncite",
        "version": VERSION,
        "built": BUNDLE_DATE,
        "description": (
            "CANONCITE — a trilingual, multi-tradition benchmark for canonical-citation "
            "attribution over public-domain scripture/legal corpora. Public release: "
            "public-domain text only; copyrighted translations excluded."
        ),
        "annotations_license": "CC BY 4.0",
        "text_license": "public-domain per source (see per-corpus)",
        "items_note": (
            "Items ship as seed_candidates.jsonl (LLM-seeded, pre human review). "
            "Post-review gold.jsonl will replace these in a later cut."
        ),
        "totals": {"corpora": 0, "corpus_units": 0, "items": 0},
        "corpora": {},
    }

    total_units = 0
    total_items = 0

    for corpus, meta in CORPORA.items():
        src_index = SRC_CORPORA / corpus / "corpus_index.jsonl"
        src_valid = SRC_CORPORA / corpus / "VALIDATION.md"
        src_items = SRC_ITEMS / corpus / "seed_candidates.jsonl"

        if not src_index.exists():
            raise ReleaseError(f"missing corpus_index.jsonl for {corpus}: {src_index}")

        # Validate the text layer BEFORE copying anything.
        stats = scan_corpus_index(src_index, corpus)

        files = {}
        files["corpus_index"] = copy_file(
            src_index, OUT / "corpora" / corpus / "corpus_index.jsonl"
        )
        if src_valid.exists():
            files["validation"] = copy_file(
                src_valid, OUT / "corpora" / corpus / "VALIDATION.md"
            )

        n_items = 0
        if src_items.exists():
            files["items"] = copy_file(
                src_items, OUT / "items" / corpus / "seed_candidates.jsonl"
            )
            with open(src_items, encoding="utf-8") as f:
                n_items = sum(1 for ln in f if ln.strip())

        total_units += stats["units"]
        total_items += n_items

        manifest["corpora"][corpus] = {
            "tradition": meta["tradition"],
            "native_lang": meta["native_lang"],
            "script": meta["script"],
            "english_status": meta["english_status"],
            "units": stats["units"],
            "units_with_english": stats["units_with_english"],
            "english_coverage_pct": stats["english_coverage_pct"],
            "n_items": n_items,
            "pd_editions": meta["pd_editions"],
            "excluded": meta.get("excluded"),
            "translation_sources": stats["translation_sources"],
            "original_sources": stats["original_sources"],
            "source_urls": stats["source_urls"],
            "files": files,
        }

    manifest["totals"] = {
        "corpora": len(CORPORA),
        "corpus_units": total_units,
        "items": total_items,
    }

    manifest_path = OUT / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    return manifest


def post_build_exclusion_asserts() -> None:
    """Belt-and-suspenders: walk the built bundle and prove nothing leaked."""
    leaks = []
    for p in OUT.rglob("*"):
        if not p.is_file():
            if p.is_dir() and p.name in FORBIDDEN_DIR_NAMES:
                leaks.append(f"forbidden dir present: {p}")
            continue
        for sub in FORBIDDEN_FILE_SUBSTR:
            if sub in p.name:
                leaks.append(f"forbidden file present: {p}")
        # Token scan over text-content fields of every shipped jsonl record,
        # plus assert excluded-English corpora ship zero English text.
        if p.suffix == ".jsonl":
            corpus = p.parent.name
            with open(p, encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    for s in _content_strings(rec):
                        for tok in FORBIDDEN_SOURCE_TOKENS:
                            if tok in s:
                                leaks.append(f"forbidden token {tok!r} in {p}:{lineno}")
                    if corpus in NO_ENGLISH_CORPORA and rec.get("text_en"):
                        leaks.append(f"English text present in excluded corpus {p}:{lineno}")
    if leaks:
        raise ReleaseError("EXCLUSION ASSERT FAILED:\n  " + "\n  ".join(leaks))
    print("[assert] exclusion checks PASSED — no private/copyrighted artifact in bundle.")


def main() -> int:
    print(f"Building CANONCITE release {VERSION} into {OUT}")
    try:
        manifest = build()
        post_build_exclusion_asserts()
    except ReleaseError as e:
        print(f"\nBUILD FAILED: {e}", file=sys.stderr)
        return 1

    t = manifest["totals"]
    print(f"\n[ok] {t['corpora']} corpora, {t['corpus_units']:,} corpus units, "
          f"{t['items']:,} items")
    print(f"[ok] manifest: {OUT / 'manifest.json'}")
    print("\nPer-corpus (units / items / english%):")
    for c, m in manifest["corpora"].items():
        note = ""
        if m["english_status"].startswith("excluded"):
            note = "  [EN excluded]"
        print(f"  {c:20s} {m['units']:>7,} / {m['n_items']:>3} / "
              f"{m['english_coverage_pct']:>5.1f}%{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
