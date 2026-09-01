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
    on-disk records carry real annotator names; the public release must not.
    This is not optional and there is no override flag: annotators are private
    individuals, one of them is not the repository owner, and a dataset card is
    a poor place to discover that you published someone's name without asking.
    The build additionally refuses to finish if any real name survives anywhere
    in the payload, so a future change to the copying logic cannot leak one
    silently.

Usage:
  python release/hf/build_hf.py                 # stage to release/hf/payload
  python release/hf/build_hf.py --out /tmp/x    # stage elsewhere

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


def real_names() -> set[str]:
    """Every annotator name appearing in the on-disk review records.

    Collected from the data rather than hardcoded, so adding an annotator does
    not silently widen what can leak.
    """
    names = set()
    if not os.path.isdir(REVIEWS):
        return names
    for corpus in os.listdir(REVIEWS):
        d = os.path.join(REVIEWS, corpus)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(".jsonl"):
                for r in read_jsonl(os.path.join(d, fn)):
                    if r.get("reviewer"):
                        names.add(r["reviewer"])
                names.add(os.path.splitext(fn)[0])
    return {n for n in names if n}


# The public code repository is owned by an account whose handle contains a real
# first name. That URL is intentional and is not a leak, so occurrences inside it
# are not counted.
ALLOWED_IN = ("KaushalprajapatiKP",)


def assert_no_real_names(payload: str, names: set[str]) -> None:
    """Fail the build if any annotator name survives anywhere in the payload."""
    hits = []
    for dirpath, _, files in os.walk(payload):
        for fn in files:
            p = os.path.join(dirpath, fn)
            try:
                text = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for name in names:
                start = 0
                while (i := text.find(name, start)) != -1:
                    window = text[max(0, i - 20):i + len(name) + 20]
                    if not any(tok in window for tok in ALLOWED_IN):
                        hits.append((os.path.relpath(p, payload), name))
                        break
                    start = i + len(name)
    if hits:
        for path, name in sorted(set(hits)):
            print(f"  LEAK: {name!r} in {path}")
        raise SystemExit(
            f"{len(set(hits))} real annotator name(s) found in the payload. "
            "Refusing to stage a release that would publish them."
        )
    print(f"  name check: 0 of {len(names)} real annotator names present in payload")


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

    # 3. review records, always pseudonymised
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
                rows = pseudonymise(rows, mapping)
                label = rows[0].get("reviewer", os.path.splitext(fn)[0])
                write_jsonl(os.path.join(out, "reviews", corpus, f"{label}.jsonl"), rows)
                n_r += len(rows)
    if mapping:
        print(f"  wrote reviews/ ({n_r} records), pseudonymised as "
              + ", ".join(sorted(mapping.values())))
    else:
        print(f"  wrote reviews/ ({n_r} records)")

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

    # 6. last gate: nothing leaves with a real annotator name in it
    assert_no_real_names(out, real_names())

    total = sum(v["bytes"] for v in files.values())
    print(f"\n  payload: {out}")
    print(f"  {len(files)} files, {total / 1e6:.1f} MB")
    print("  next: review it, then see release/hf/upload.sh")


if __name__ == "__main__":
    main()
