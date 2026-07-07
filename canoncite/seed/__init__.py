"""Seed-question generation: LLM proposes ID-grounded candidate items from real
verses; humans then verify (BENCHMARK_DESIGN.md §4 step 1).

Design principle: gold citations are chosen by SAMPLING real verses (correct by
construction), and the LLM only writes the question text. The LLM never decides
which citation is gold — that is exactly the part that must be right. All output
is `provenance.seed = llm_proposed`, `verified = false` until human annotation.
"""
