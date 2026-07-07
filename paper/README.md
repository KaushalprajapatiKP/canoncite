# paper/

Draft of the CANONCITE research paper.

## Status: DRAFT SKELETON

[`canoncite.md`](./canoncite.md) is a **draft skeleton**. It fixes the paper's
structure, problem statement, benchmark design, metric definitions, experimental
protocol, and — importantly — the **precise, honest prior-art positioning**
(against Ovcharov 2026 "Citation Grounding", IslamicEval 2025, ParamBench, MILU,
and the ALCE/AttributedQA/CAQA/VeriCite/Self-RAG/CRAG lineage).

**All empirical results are FORTHCOMING.** Every results table (§5.3, Tables
5.1–5.5) is a placeholder to be filled once the experiment grid is run:

- systems A–E × 10 corpora (per tier) × query language (en / hi / native script)
  × ≥3 readers (incl. Indic-tuned models)
- attribution / misattribution numbers (CER, CG, Attr P/R/F1, MAR, NMR, AbstAcc)
- cross-lingual attribution, closed-book base-competence control
- inter-annotator agreement (α / κ) and content-support-judge calibration

## To do before submission (fill the skeleton)

1. Run the v0 Gita milestone (60–100 double-annotated items) → first real
   MAR / abstention numbers + one agreement number.
2. Build Tier-A deep annotation (Gita, Bible, Constitution of India, Thirukkural)
   and Tier-B breadth items; report α/κ.
3. Implement + run systems A–E across the grid; populate Tables 5.1–5.5.
4. Write the C4 findings (misattribution taxonomy, cross-lingual transfer) once
   data exists.
5. Ship the datasheet (`DATASHEET.md`) referenced in §6.

## Sources

Content and verified citations are drawn from the repo's planning docs:
`RESEARCH_PLAN.md`, `RELATED_WORK.md`, `RELATED_WORK_MULTILINGUAL.md`,
`BENCHMARK_DESIGN.md`, and `canoncite/CORPORA.md`. Only citations already
gathered in those documents are used — none were invented.
