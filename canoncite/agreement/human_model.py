"""Human--model agreement on the verification sample.

This is **not** inter-annotator agreement. IAA measures whether two independent
*people* converge; it is the reliability evidence a benchmark needs, and it
requires a second human. This script measures something different and weaker but
still useful: how closely an automatic checker
(`agreement/auto_annotate.py`) tracks the human annotator on the same items.

Report it as "human--model agreement", name the model, and never let it stand in
for Table 5.4. Where a paper needs $\\alpha$/$\\kappa$ between annotators, this
number does not qualify.

Run:
    PYTHONPATH=. python canoncite/agreement/human_model.py [--corpus X]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from canoncite.agreement.agreement import (  # noqa: E402
    ROOT, cohen_kappa, effective_labels, krippendorff_alpha, load_items_by_id,
    load_verdicts, masi_distance,
)

AUTO_DIR = os.path.join(ROOT, "canoncite", "data", "reviews_auto")


def load_auto(corpus: str | None = None) -> list[dict]:
    rows: list[dict] = []
    if not os.path.isdir(AUTO_DIR):
        return rows
    for c in ([corpus] if corpus else sorted(os.listdir(AUTO_DIR))):
        d = os.path.join(AUTO_DIR, c)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".jsonl"):
                with open(os.path.join(d, fn), encoding="utf-8") as fh:
                    rows += [json.loads(l) for l in fh if l.strip()]
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", default=None)
    a = ap.parse_args(argv)

    human = [v for v in load_verdicts(a.corpus)
             if v.get("annotator_type") != "model"
             and not str(v.get("reviewer", "")).startswith("auto:")]
    auto = load_auto(a.corpus)
    items = load_items_by_id(a.corpus)

    if not auto:
        print("No machine verdicts found. Run agreement/auto_annotate.py first.")
        return 1

    # Group by annotator: each human and each machine model is its own rater.
    # Collapsing them (as an earlier version did) silently mixes raters and
    # reports a meaningless blend, so every comparison below is per-pair.
    humans: dict[str, dict] = {}
    for v in human:
        humans.setdefault(v["reviewer"], {})[(v["corpus"], v["item_id"])] = v
    models: dict[str, dict] = {}
    for v in auto:
        models.setdefault(str(v.get("reviewer") or "auto:?"), {})[
            (v["corpus"], v["item_id"])] = v

    fmt = lambda v: "n/a" if v is None else f"{v:.3f}"
    print("Human--model agreement  (NOT inter-annotator agreement)")
    print(f"  human annotators: {', '.join(sorted(humans))}")
    print(f"  machine models  : {', '.join(sorted(models))}")
    print()

    for mname, M in sorted(models.items()):
        print(f"=== {mname}  ({len(M)} verdicts) ===")
        for hname, H in sorted(humans.items()):
            shared = sorted(set(H) & set(M))
            if not shared:
                print(f"  vs {hname}: no overlap")
                continue
            gold_units, status_pairs, exact, dis = [], [], 0, []
            for key in shared:
                it = items.get(key[1]) or {}
                eh = effective_labels(H[key], it)
                ea = effective_labels(M[key], it)
                gold_units.append([eh["gold"], ea["gold"]])
                status_pairs.append((eh["status"], ea["status"]))
                if eh["gold"] == ea["gold"]:
                    exact += 1
                else:
                    dis.append((key, sorted(eh["gold"]), sorted(ea["gold"]),
                                (M[key].get("notes") or "")[:90]))
            a = krippendorff_alpha(gold_units, masi_distance)
            k = cohen_kappa(status_pairs)
            print(f"  vs {hname:10} n={len(shared):3}  exact {exact}/{len(shared)} "
                  f"({exact/len(shared)*100:.1f}%)  alpha-MASI {fmt(a)}  kappa {fmt(k)}")
            print(f"      model status: {dict(Counter(s for _, s in status_pairs))}")
            for (c, i), hg, ag, why in dis[:10]:
                print(f"      DIFF {c}/{i}: human {hg} vs model {ag}")
                if why:
                    print(f"           model: {why}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
