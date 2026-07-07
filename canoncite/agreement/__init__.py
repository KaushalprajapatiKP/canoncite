"""Reviewer-agreement + adjudication tooling for the CANONCITE benchmark.

Pipeline (BENCHMARK_DESIGN.md §4, Step 4):

    fetch.py       pull `verdicts` rows from Supabase -> data/reviews/<corpus>/verdicts.jsonl
    agreement.py   inter-annotator agreement (Krippendorff alpha + MASI, Cohen/Fleiss kappa)
    adjudicate.py  fold verdicts into gold.jsonl, flagging disagreements for adjudication

Everything here is pure-stdlib: the statistics (MASI distance, Krippendorff's
alpha, Cohen's/Fleiss' kappa) are implemented from scratch so the tool has no
third-party dependency and is unit-testable without any model or SciPy.

Quality-gate targets (BENCHMARK_DESIGN.md §4): Krippendorff alpha >= 0.67
(citation sets), Cohen/Fleiss kappa >= 0.6 (categorical labels).
"""

ALPHA_TARGET = 0.67   # Krippendorff's alpha on citation sets (MASI distance)
KAPPA_TARGET = 0.60   # Cohen's / Fleiss' kappa on categorical labels
