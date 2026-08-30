"""Recompute every headline figure in the paper from the result JSONL, and check
the .tex against them.

Three reviewer passes each found a stale number that a recomputation had left
behind in a paragraph nobody re-read. The figures were hand-typed, so nothing
caught the drift. This does:

    python paper/acl/figures.py          # print the authoritative values
    python paper/acl/figures.py --check  # verify canoncite.tex quotes them

Exit status is non-zero if a checked figure is missing from the .tex, so this can
gate a commit. It cannot catch a number quoted in the wrong *context* -- only a
human can -- but it catches the class of error that actually occurred: a value
updated in one place and not another.
"""
from __future__ import annotations

import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
RES = os.path.join(ROOT, "results", "gpu_qwen14b")


def load(name: str) -> dict:
    path = os.path.join(RES, name)
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                d = json.loads(line)
                out[(d["corpus"], d["qlang"])] = d
    return out


S = {"A": load("systemA.jsonl"), "B": load("systemB_all.jsonl"),
     "C": load("systemC_all.jsonl"), "D": load("systemD_all.jsonl"),
     "E2": load("systemE2_all.jsonl"), "CB": load("systemCB_qwen14b.jsonl")}
XL = [k for k in S["C"] if k[1] != "en" and k in S["D"] and k in S["E2"]]
EN = [k for k in S["C"] if k[1] == "en" and k in S["D"] and k in S["E2"]]


def _mar(sys_, k):
    return S[sys_][k]["agg"].get("mar")


def macro(sys_, cells):
    """Mean of per-cell MARs, over cells where this system's MAR is defined."""
    v = [_mar(sys_, k) for k in cells if _mar(sys_, k) is not None]
    return sum(v) / len(v) if v else None


def peritem(sys_, cells):
    """Wrong citations per item ATTEMPTED. A cell that cited nothing contributes
    zero wrong citations over its n items -- defined, and the best possible
    score. This is the coverage-corrected metric."""
    w = sum((_mar(sys_, k) or 0.0) * S[sys_][k]["agg"]["n_citing"] for k in cells)
    n = sum(S[sys_][k]["agg"]["n"] for k in cells)
    return w / n if n else None


def coverage(sys_, cells):
    nc = sum(S[sys_][k]["agg"]["n_citing"] for k in cells)
    n = sum(S[sys_][k]["agg"]["n"] for k in cells)
    return nc / n if n else None


def common(a, b):
    return [k for k in XL if _mar(a, k) is not None and _mar(b, k) is not None]


def figures() -> dict[str, float]:
    f: dict[str, float] = {}
    def r3(v):
        return None if v is None else round(v, 3)
    for s in ("C", "D", "E2"):
        f[f"macro_{s}"] = r3(macro(s, [k for k in XL if _mar(s, k) is not None]))
        f[f"peritem_{s}"] = r3(peritem(s, XL))
        f[f"coverage_{s}"] = r3(coverage(s, XL))
    for a, b in (("E2", "D"), ("E2", "C"), ("D", "C")):
        cm = common(a, b)
        ma, mb = macro(a, cm), macro(b, cm)
        pa, pb = peritem(a, XL), peritem(b, XL)
        f[f"macro_margin_{a}_{b}"] = r3(None if ma is None or mb is None else ma - mb)
        f[f"macro_cells_{a}_{b}"] = len(cm)
        f[f"peritem_margin_{a}_{b}"] = r3(None if pa is None or pb is None else pa - pb)
    if S["CB"]:
        def _avg(cells, field):
            v = [S["CB"][k][field] for k in cells if S["CB"][k].get(field) is not None]
            return round(sum(v) / len(v), 3) if v else None
        cb_en = [k for k in S["CB"] if k[1] == "en"]
        cb_xl = [k for k in S["CB"] if k[1] != "en"]
        for name, cells in (("en", cb_en), ("xl", cb_xl)):
            f[f"cb_f1_{name}"] = _avg(cells, "f1_exact")
            f[f"cb_mar_{name}"] = _avg(cells, "mar")
    for s in ("C", "D", "E2"):
        v = [S[s][k]["agg"].get("nmr") for k in XL if S[s][k]["agg"].get("nmr") is not None]
        f[f"nmr_{s}"] = round(sum(v) / len(v), 3)
    f["n_cells_xl"] = len(XL)
    return f


# Figures whose exact string must appear in the .tex. Deliberately not every
# value -- only those a recomputation would move and a reader would check.
CHECKED = ["macro_C", "macro_D", "macro_E2", "peritem_C", "peritem_D", "peritem_E2",
           "coverage_C", "coverage_D", "coverage_E2",
           "macro_margin_E2_D", "peritem_margin_E2_D",
           "nmr_C", "nmr_D", "nmr_E2", "cb_mar_en", "cb_mar_xl"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify canoncite.tex quotes the computed figures")
    a = ap.parse_args(argv)
    f = figures()

    if not a.check:
        for k in sorted(f):
            print(f"  {k:26} {f[k]}")
        return 0

    tex = open(os.path.join(HERE, "canoncite.tex"), encoding="utf-8").read()
    tex_nums = set(re.findall(r"\d\.\d{3}", tex))
    missing = []
    for key in CHECKED:
        if key not in f or f[key] is None:
            continue
        s = f"{abs(f[key]):.3f}"
        if s not in tex_nums:
            missing.append((key, f[key]))
    for key, val in missing:
        print(f"  MISSING from canoncite.tex: {key} = {val}")
    if missing:
        print(f"\n{len(missing)} figure(s) in the results are not quoted in the paper. "
              "Either the paper is stale or the figure is intentionally unreported.")
        return 1
    print(f"OK: all {len(CHECKED)} checked figures appear in canoncite.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
