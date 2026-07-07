"""Web review app for CANONCITE seed items.

Reviewers verify LLM-drafted seed items against the real source text: for each item
they see the question (English + Hindi + native, whichever exist), the gold citation
IDs *with the actual verse text pulled from corpus_index*, the near-miss distractors,
and the draft answer — then approve / edit / reject. Verdicts are written per reviewer
so multiple people annotate the same items in parallel; `merge.py` computes
inter-annotator agreement and adjudicated gold.

Run:  PYTHONPATH=. python -m canoncite.review --port 8080
"""
