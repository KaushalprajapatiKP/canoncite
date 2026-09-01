"""Assemble the HuggingFace payload for CANONCITE from the built v0 release.

The v0 package under `release/canoncite-v0/` is correct but under-describes
itself, and it predates the human verification pass. This script produces an
upload-ready tree that fixes both, without touching the source release:

  * `items/<corpus>/seed_candidates.jsonl` is kept under its original filename.
    It is the full 622-item benchmark and it is what every experiment in the
    paper actually loaded (`canoncite/systems/naive_rag.py`). The v0 manifest
    called it "pre human review", which reads as though it were superseded. It
    is not, and the note is rewritten here.
  * `verified/<corpus>/verified.jsonl` is new: the 120-item stratified subsample
    that two annotators reviewed. Every label was confirmed. The only deltas
    against the corresponding seed records are 18 citation lists in a different
    order, which are set-identical and therefore invisible to the scorer.
  * `reviews/<corpus>/<pseudonym>.jsonl` is new, and is pseudonymised. The
    on-disk records carry real annotator names; a public release should not,
    absent explicit consent from each annotator. Pass --real-names to override,
    which you should only do if every named annotator has agreed.

Usage:
  python release/hf/build_hf.py                 # stage to release/hf/payload
  python release/hf/build_hf.py --out /tmp/x    # stage elsewhere
  python release/hf/build_hf.py --real-names    # keep annotator names (see above)

Uploading is deliberately a separate step; see upload.sh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "release", "canoncite-v0")
ITEMS = os.path.join(ROOT, "canoncite", "data", "items")
REVIEWS = os.path.join(ROOT, "canoncite", "data", "reviews")

ITEMS_NOTE = (
    "items/<corpus>/seed_candidates.jsonl is the benchmark: 622 items, and the "
    "exact files every experiment in the paper loaded. The filename is retained "
    "for reproducibility against the released harness. 'seed' refers to how the "
    "items were drafted (LLM-seeded from the frozen corpus index), not to their "
    "status: a 120-item stratified subsample was independently reviewed by two "
    "annotators and every label was confirmed. That subsample ships under "
    "verified/, the raw review records under reviews/."
)


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_subsample():
    """Recompute the claim the dataset card makes, rather than trusting it.

    Returns (n_verified, n_reordered, n_substantive). A non-zero third element
    means the card's wording is wrong and the build should stop.
    """
    n = reorder = substantive = 0
    for corpus in sorted(os.listdir(ITEMS)):
        gold = os.path.join(ITEMS, corpus, "gold.jsonl")
        seed = os.path.join(ITEMS, corpus, "seed_candidates.jsonl")
        if not (os.path.exists(gold) and os.path.exists(seed)):
            continue
        by_id = {r["id"]: r for r in read_jsonl(seed)}
        for g in read_jsonl(gold):
            o = by_id.get(g["id"])
            if o is None:
                continue
            n += 1
            same_set = (
                set(g.get("gold_citations", [])) == set(o.get("gold_citations", []))
                and g.get("must_abstain") == o.get("must_abstain")
                and g.get("answerable") == o.get("answerable")
            )
            if not same_set:
                substantive += 1
            elif g.get("gold_citations") != o.get("gold_citations"):
                reorder += 1
    return n, reorder, substantive


def pseudonymise(rows, mapping):
    out = []
    for r in rows:
        r = dict(r)
        name = r.get("reviewer")
        if name:
            r["reviewer"] = mapping.setdefault(name, f"annotator_{chr(65 + len(mapping))}")
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(HERE, "payload"))
    ap.add_argument("--real-names", action="store_true",
                    help="keep real annotator names (requires each annotator's consent)")
    a = ap.parse_args()

    if not os.path.isdir(SRC):
        raise SystemExit(f"built release not found at {SRC}; run release/build_release.py first")

    n_ver, n_reorder, n_sub = verify_subsample()
    if n_sub:
        raise SystemExit(
            f"{n_sub} verified items differ substantively from their seed records. "
            "The dataset card claims every label was confirmed. Fix the card or the "
            "data before uploading."
        )
    print(f"  verification check: {n_ver} reviewed, {n_reorder} reorder-only, "
          f"{n_sub} substantive -> card wording holds")

    out = a.out
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)

    # 1. corpora + items, verbatim from the built release
    for sub in ("corpora", "items"):
        shutil.copytree(os.path.join(SRC, sub), os.path.join(out, sub))
    print(f"  copied corpora/ and items/ from {os.path.relpath(SRC, ROOT)}")

    # 2. the human-verified subsample
    n_v = 0
    for corpus in sorted(os.listdir(ITEMS)):
        rows = read_jsonl(os.path.join(ITEMS, corpus, "gold.jsonl"))
        if rows:
            write_jsonl(os.path.join(out, "verified", corpus, "verified.jsonl"), rows)
            n_v += len(rows)
    print(f"  wrote verified/ ({n_v} items)")

    # 3. review records, pseudonymised unless explicitly overridden
    mapping: dict[str, str] = {}
    n_r = 0
    if os.path.isdir(REVIEWS):
        for corpus in sorted(os.listdir(REVIEWS)):
            d = os.path.join(REVIEWS, corpus)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.endswith(".jsonl"):
                    continue
                rows = read_jsonl(os.path.join(d, fn))
                if not rows:
                    continue
                if not a.real_names:
                    rows = pseudonymise(rows, mapping)
                label = rows[0].get("reviewer", os.path.splitext(fn)[0])
                write_jsonl(os.path.join(out, "reviews", corpus, f"{label}.jsonl"), rows)
                n_r += len(rows)
    if mapping:
        print(f"  wrote reviews/ ({n_r} records), pseudonymised: "
              + ", ".join(f"{v}" for v in mapping.values()))
    else:
        print(f"  wrote reviews/ ({n_r} records) WITH REAL NAMES")

    # 4. manifest with the corrected note and fresh checksums
    man = json.load(open(os.path.join(SRC, "manifest.json"), encoding="utf-8"))
    man["items_note"] = ITEMS_NOTE
    man["human_verification"] = {
        "reviewed_items": n_ver,
        "annotators": 2,
        "labels_changed": n_sub,
        "citation_lists_reordered": n_reorder,
        "note": "Reordered lists are set-identical; the scorer compares as sets.",
    }
    files = {}
    for dirpath, _, names in os.walk(out):
        for nm in sorted(names):
            p = os.path.join(dirpath, nm)
            files[os.path.relpath(p, out)] = {
                "sha256": sha256(p), "bytes": os.path.getsize(p)
            }
    man["files"] = files
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2)
    print(f"  wrote manifest.json ({len(files)} files checksummed)")

    # 5. docs
    for src, dst in (
        (os.path.join(ROOT, "release", "LICENSE"), "LICENSE"),
        (os.path.join(ROOT, "release", "DATASHEET.md"), "DATASHEET.md"),
        (os.path.join(HERE, "README.md"), "README.md"),
    ):
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(out, dst))
            print(f"  copied {dst}")
        else:
            print(f"  MISSING {src}")

    total = sum(v["bytes"] for v in files.values())
    print(f"\n  payload: {out}")
    print(f"  {len(files)} files, {total / 1e6:.1f} MB")
    print("  next: review it, then see release/hf/upload.sh")


if __name__ == "__main__":
    main()
