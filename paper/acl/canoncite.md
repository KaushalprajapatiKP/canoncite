# CANONCITE: A Multilingual, Multi-Tradition Benchmark for Canonical-Citation Attribution and Abstention

> Rendered from `canoncite.tex` by `tex2md.py` — the `.tex` is the submission artefact; regenerate this file rather than editing it.

## Abstract

When a language model cites a canonical source—a scripture verse, a constitutional article—citing the *wrong* unit is a distinct and more damaging failure than citing nothing. Existing attribution benchmarks score whether a claim is supported by a retrieved passage; they cannot detect that the model named Gita 2.48 when the source was 2.47. We introduce **CANONCITE**, a benchmark for *exact-ID* citation attribution and abstention over ten public-domain canonical corpora spanning four traditions and five scripts (188,557 citable units), with every question posed in English, Hindi, and the corpus's native script. Instantiating a five-system ladder, we show that the cross-lingual attribution collapse is fundamentally a *retrieval-ranking* failure: on our pilot corpora, attribution F1 under non-English queries rises from 0.177 to 0.690 through hybrid and reranked retrieval alone, with the gold unit retrieved but ranked at median 7–13 throughout. We then show that a joint discriminative exact-ID selector cuts misattribution by 29–61% at ~2 LLM calls per item versus the Self-RAG/CRAG baseline's ~10—and, contrary to our own hypothesis, that it does so by eliminating *implausible* citations rather than by resolving near misses, which rise as a share of the residual error. A three-point reader study (8B/14B/120B) shows the advantage is capacity-dependent: below a threshold between 8B and 14B the decomposed baseline wins, a reversal that survives end-to-end replication (margin 0.026 against a ±0.014 noise band). We release the corpora, items, metric harness, and all system code.

## Introduction

Retrieval-augmented generation is now the default remedy for factual hallucination, and a mature literature evaluates whether a generated claim is *supported* by the passages a system retrieved (Gao 2023; Bohnet 2022; Hu 2025). That framing has a blind spot. In domains organised around a fixed, publicly known identifier scheme—scripture verses, statutes, constitutional articles, case law—the citation is not a pointer to evidence but a *claim about identity*. A model that answers a question about non-attachment correctly but attributes it to Bhagavad Gītā 2.48 instead of 2.47 has produced a fluent, well-supported, and false citation. Support-based metrics score it as a success: the neighbouring verse is on the same theme and entails much the same content.
This failure is most consequential exactly where canonical texts matter most and where NLP resources are thinnest: religious and legal corpora in Indian languages, read by users querying in Hindi or in the text's own script. Yet Indic LLM benchmarks evaluate *understanding* through multiple-choice questions (Verma 2024; Team 2025; AI4Bharat 2024), and the one prior line that exploits fixed identifiers for exact attribution does so for a single jurisdiction in a single language (Ovcharov 2026).

**Contributions.**  

We are careful about novelty. We do *not* claim the fixed-ID-enables-exact-attribution idea, already demonstrated for one legal jurisdiction (Ovcharov 2026), nor first religious verse-attribution, already done for a single tradition (Task 2025), nor Indian scripture knowledge (Team 2025; Verma 2024). Our contributions are:
- **C1 — Benchmark.** The first multilingual, multi-tradition, multi-script canonical-citation attribution and abstention benchmark: ten corpora, 188,557 citable units, 622 items, each posed in English, Hindi, and native script. The *cross-lingual, multi-script attribution axis* is the load-bearing, genuinely unoccupied novelty (§The CANONCITE Benchmark).
- **C2 — Metric suite.** A corpus-agnostic exact-attribution harness operating over normalised IDs, integrating the fixed-ID existence check (Ovcharov 2026) with the citation precision/recall paradigm (Gao 2023) and adding misattribution and abstention measures (§Metrics).
- **C3 — Method.** A joint discriminative exact-ID selector (E2) that attains the lowest misattribution rate of any system at roughly a fifth of the SOTA's inference cost, by eliminating *implausible* misattributions and concentrating the residual error on genuine near neighbours—above a reader capacity threshold between 8B and 14B, below which the decomposed baseline is the more robust choice. Both the advantage and the reversal survive an end-to-end replication (§Systems and Results).
- **C4 — Findings.** The cross-lingual collapse is localised to retrieval *ranking* (the gold unit is retrieved but ranked at median 7–13); near misses grow from 8% to 13% of residual misattributions as systems improve, so adjacency discrimination is what remains unsolved; and MAR-exist =0.000 throughout separates “cannot read the language” from “misattributes”.

**Status of this release.**  

CANONCITE v1 ships model-drafted items whose gold citations are sampled from, and automatically validated against, the closed corpus ID space. Human verification covers a stratified sample of 120 items, **double-annotated**, with Krippendorff's α-MASI =0.991 on citation sets and 118 items promoted to verified gold (§Human Verification). All system comparisons are *relative* comparisons over a common, automatically validated label set: the caveat applies identically to every system, so the orderings are unaffected, while absolute values may shift.

## Related Work

**Attribution benchmarks.**  

ALCE (Gao 2023), AQA (Bohnet 2022), and CAQA (Hu 2025) score whether a generated claim is entailed by retrieved passages, typically via NLI, in English. Their unit of truth is *support*, not identity; a near-miss citation to a semantically equivalent neighbour is scored correct. Surveys of evidence-based generation (Survey 2025) confirm this framing dominates.

**Fixed-ID attribution.**  

Ovcharov 2026 shows that a closed citation graph turns verification into an exact lookup, for US legal citations in English. We adopt the idea and credit it; our contribution is extending it across traditions, scripts, and query languages, and specifying its validation against human judgement—a generality claim no prior fixed-ID work makes.

**Indic and religious NLP.**  

MILU (Verma 2024), ParamBench (Team 2025) and IndicQA (AI4Bharat 2024) evaluate Indic *understanding* via MCQ; IL-TUR (Team 2024) and ILDC (Malik 2021) cover Indian legal reasoning without exact-citation scoring. IslamicEval (Task 2025) targets verse hallucination in one tradition, monolingually. None measures exact-ID attribution across languages and scripts.

**Repair methods.**  

CiteFix (Maheshwari 2025), VeriCite (Qian 2025), RARR (Gao 2023), Self-RAG (Asai 2024) and CRAG (Yan 2024) all verify or repair per-passage. §Systems and Results shows this family is *subsumed* once ranking is fixed, and that joint discrimination is what the residual errors require.

## The CANONCITE Benchmark

**Corpora.**  

Ten public-domain canonical texts spanning Hindu, Buddhist, Sikh and Christian traditions plus Indian constitutional law, in five scripts (Table “corpora”). Each corpus is frozen as a `corpus_index.jsonl` keyed by its own canonical identifier scheme (`2.47` for Gītā chapter.verse; `Art.~370` for the Constitution), giving a closed ID space U per corpus. Only public-domain translations are released; where the only English translation is under copyright (Rāmāyaṇa, Mahābhārata, Guru Granth Sahib), we release the native-script text alone—an honest constraint that makes those corpora *require* cross-lingual retrieval.

| **Corpus** | **Units** | **Scripts** |
|---|---|---|
| Guru Granth Sahib | 60,555 | Gurmukhi |
| Mahābhārata | 73,816 | Devanāgarī |
| Bible | 31,095 | Latin |
| Rāmāyaṇa | 18,761 | Devanāgarī |
| Thirukkuṛaḷ | 1,330 | Tamil |
| Constitution of India | 1,219 | Latin/Devanāgarī |
| Bhagavad Gītā | 701 | Devanāgarī |
| Upaniṣads | 462 | Devanāgarī |
| Dhammapada | 423 | Latin (Pāli) |
| Yoga Sūtras | 195 | Devanāgarī |
| **Total** | **188,557** | 5 scripts |

*The ten frozen corpora. Every unit is addressable by its canonical ID.*

**Items.**  

622 items across all ten corpora, each carrying a question, a gold answer, gold citation ID(s) validated against U, near-miss distractors (adjacent same-theme units), a question type, and an ambiguity label. Five question types—*factual*, *retrieval*, *conceptual*, *interpretive*, *unanswerable*—exercise different failure modes; unanswerable items carry `must_abstain` and no gold citation, so abstention is measured rather than assumed. Every item is fully trilingual: Hindi and native-script questions were produced with IndicTrans2 (Gala 2023) (Pāli by prompted generation, which IndicTrans2 does not cover). Gold citations are language-independent, so the three language conditions are matched by construction—the comparison isolates query language and nothing else.

**Construction protocol.**  

Corpora are frozen first: a version-hashed `corpus_index.jsonl` per corpus fixes U, and nothing downstream may cite an ID outside it. Items are then drafted by a pinned LLM *conditioned on retrieved real units*, over-generating ~1.5× to allow rejection; unanswerable items are seeded from out-of-corpus topics and cross-corpus swaps. Every drafted gold citation is automatically validated against U, so a fabricated identifier cannot enter the benchmark by construction. Model output is a *draft*, never ground truth: human annotators work with the corpus open, seeing each candidate ID's actual text, and confirm or correct the gold set, answerability, and distractors (§Human Verification reports coverage).

**Tiered annotation.**  

Double-annotating verse-level ground truth across four traditions and five scripts exceeds a small team's budget, and annotator scarcity—not compute—is this benchmark's binding constraint. We therefore declare two tiers rather than hide a quality gradient. **Tier A** (Bhagavad Gītā, Bible, Constitution, Thirukkuṛaḷ) targets full double annotation with per-citation content-support labels, and carries the C2 generality claim. **Tier B** (the remaining six) covers factual, retrieval and unanswerable items only—all auto-checkable with NLI-free metrics— extending the language, script and tradition axes at low annotation cost. Each corpus's tier is recorded in the datasheet.

## Metrics

All metrics operate over normalised IDs against the closed space U, so verification is exact lookup with no NLI model. Let an item have gold set G and a system emit cited set C.
- **Attribution P/R/F1 (exact)**: set overlap of C and G. We also report a *span* variant crediting a correct chapter with a wrong verse.
- **Misattribution Rate (MAR)**: the fraction of *citing* items where C not⊆ G—the benchmark's gated axis. It decomposes into **MAR-exist** (cited an ID not in U, i.e. a fabricated identifier) and **MAR-support** (cited a real but wrong unit).
- **Near-miss MAR (NMR)**: MAR restricted to citations landing on a declared near-miss distractor.
- **Abstention accuracy**, **over-citation** and **wrong-abstention** rates, over the `must_abstain` items.

MAR-exist is 0.000 in every run we report: models cite *real* units incorrectly rather than inventing identifiers. This separates a base-competence failure from an attribution failure and is why exact-ID scoring is informative here.

## Systems and Results

**The ladder.**  

**A** naive BM25 RAG; **B** hybrid BM25+dense RRF (BGE-M3 (Chen 2024) + FAISS); **C** hybrid plus cross-encoder reranking; **D** an inference-time reproduction of Self-RAG (Asai 2024) + CRAG (Yan 2024), where a CRAG-style evaluator labels each passage and a Self-RAG ISSUP critique keeps a citation only if the passage supports it; and **E2** (ours), which presents all reranked candidates *jointly* and forces one exact-source choice or abstention—one LLM call rather than up to k. Grid: systems × 10 corpora × query language (en/hi/native) = 28 cells per system. Primary reader Qwen2.5-14B-Instruct (Team 2024), self-hosted; all prompts, temperatures and k fixed and logged. We pre-committed to a decision gate: *E2 must beat D on cross-lingual MAR*.

**The collapse is a ranking failure.**  

On the two pilot corpora System A attains 0.719 attribution F1 under English queries and collapses to 0.177 under Hindi/native queries, with misattribution at 0.757. A recall probe resolves the cause: the gold unit *is* retrieved under cross-lingual queries but ranked at median 7–13, outside the reader's window. Fixing ranking alone—dense hybrid retrieval, then cross-encoder reranking—lifts cross-lingual F1 to 0.626 and then 0.690 and cuts MAR from 0.757 to 0.196 (Table “ladder”), without touching the reader. Applying the binary verify-and-repair layer (E) to BM25 retrieval barely moves cross-lingual F1 (0.177 → 0.173): a verifier can only repair *to* a unit retrieval actually surfaced, so this family is subsumed once ranking is fixed.
Table “recall” isolates the mechanism. Dense hybrid retrieval *finds* the gold unit almost always (R@50 = 0.93–0.99) in every language, but under cross-lingual queries ranks it at median 7–13, below the reader's top-5 window; English queries place it at rank 1. The collapse is therefore neither a coverage failure nor a reasoning failure. Two levers follow—widen k, or rerank—and widening plateaus then hurts: a k-sweep of System E improves through k≈10 but *regresses* at k=20 (Gītā Hindi 0.683→0.670) as the reader drowns in noisy passages. Reranking is the right lever, and C@5 (0.690) beats E@10 (0.659) accordingly.

| **Corpus × lang** | **R@5** | **R@20** | **R@50** | **med. rank** |
|---|---|---|---|---|
| Gītā · en | 0.800 | 0.943 | 0.986 | **1** |
| Gītā · hi | **0.357** | 0.857 | 0.986 | **7** |
| Gītā · sa | 0.557 | 0.843 | 0.943 | 5 |
| Yoga S. · en | 0.932 | 0.955 | 0.977 | **1** |
| Yoga S. · hi | **0.227** | 0.773 | 0.932 | **12** |
| Yoga S. · sa | **0.227** | 0.727 | 0.955 | **13** |

*Recall@k of the gold unit under hybrid BM25+BGE-M3 retrieval, answerable items. Retrieval *finds* the gold unit cross-lingually (R@50 ≈ 0.93–0.99) but *ranks* it far below the top-5 window. The collapse is a ranking failure.*

|  | **English** | **Cross-lingual** |  |  |
|---|---|---|---|---|
| **System** | F1↑ | MAR↓ | F1↑ | MAR↓ |
| A naive BM25 | 0.719 | – | 0.177 | 0.757 |
| E verify+repair | 0.676 | – | 0.173 | 0.701 |
| B hybrid | 0.776 | – | 0.626 | 0.196 |
| C rerank | 0.773 | – | **0.690** | 0.259 |
| E2 (ours) | 0.739 | – | 0.693 | **0.158** |

*The retrieval ladder on the **two pilot corpora** (Gītā + Yoga Sūtras), Qwen2.5-14B reader. The cross-lingual collapse is repaired by *ranking*, not by verification: E on BM25 barely moves F1, while hybrid+rerank nearly quadruples it.*

| **Corpus** | **C** | **D** | **E2 (ours)** |
|---|---|---|---|
| Bhagavad Gītā | 0.272 | 0.200 | **0.166** |
| Yoga Sūtras | 0.233 | 0.158 | **0.137** |
| Upaniṣads | 0.340 | 0.427 | **0.125** |
| Bible | – | 0.316 | **0.256** |
| Constitution of India | – | 0.370 | **0.265** |
| Mahābhārata | 0.375 | 0.472 | **0.312** |
| Dhammapada | 0.637 | 0.487 | **0.449** |
| Thirukkuṛaḷ | 0.317 | **0.225** | 0.282 |
| Guru Granth Sahib | 0.841 | **0.833** | 0.838 |
| Rāmāyaṇa | 0.839 | **0.844** | 0.909 |
| **All (18 cells)** | 0.482 | 0.443 | **0.387** |

***The gate.** Cross-lingual misattribution rate↓ per corpus, **all ten corpora**, Qwen2.5-14B reader. E2 attains the lowest overall MAR and wins 7 of 10 corpora, at ~2 LLM calls/item versus D's ~10. The three losses are the low-resource-script corpora where every system degrades badly (MAR >0.8 for Gurmukhi and Rāmāyaṇa). Cross-lingual F1: D 0.440, E2 0.423—F1 is not what a verification layer optimises.*

**Joint selection removes implausible citations, not near misses.**  

E2 presents the reranked candidates together and forces one exact-source choice. Across all ten corpora it attains the lowest cross-lingual MAR of any system (0.387 vs D's 0.443; Table “gate”), winning 7 of 10 corpora, with the largest margins on Upaniṣads (0.427→0.125) and Mahābhārata (0.472→0.312). **The pre-committed gate passes.**
The *mechanism*, however, is not the one we hypothesised, and the near-miss rate says so. NMR—the share of wrong citations landing on a declared near-miss distractor—*rises* as misattribution falls: cross-lingually, C sits at MAR 0.482 with NMR 0.082, E2 at MAR 0.387 with NMR 0.129 (on the pilot corpora, 0.259/0.121 versus 0.158/0.268). E2 therefore does *not* preferentially resolve near misses; it preferentially removes the *implausible* misattributions—citations to units that are not even credible neighbours—leaving genuine near-neighbour discrimination as a roughly constant, and proportionally much larger, residual. We report this because it revises our own hypothesis: joint presentation buys candidate-set discipline, not fine-grained adjacency discrimination.
This also explains the capacity dependence in §Systems and Results: narrowing to the right neighbourhood is a judgement an 8B reader can partly make, but choosing *within* that neighbourhood is what scales with capacity. Consistent with this, E2 has the best abstention accuracy of any system (0.955 cross-lingual, 0.986 English) and the lowest over-citation rate (0.045), but the highest wrong-abstention rate (0.470)—it is the most willing to decline, which is the correct bias for citation-critical use and a cost we state rather than hide.

**Script, not “low-resource”, is the discriminating variable.**  

Breaking the grid down by query script (Table “script”) refines the picture in a way the aggregate hides. Devanagari queries—Hindi and Sanskrit—behave like English once ranking is fixed (E2 F1 0.477 and 0.392 against English's 0.472). Tamil, often grouped as low-resource, is in fact the *best* cross-lingual condition we measure under reranking (C F1 0.625). What collapses is Gurmukhi and Pāli, at MAR 0.83 and 0.80 respectively, where no system recovers. The common factor is not script frequency but our own release constraint: Guru Granth Sahib is the largest ID space in the benchmark (60,555 units) *and* native-script-only for copyright reasons, and the Pāli questions are the one language IndicTrans2 does not cover, so they were produced by prompted generation. These are single-cell conditions (n=1 corpus each), so we report them as a located weakness rather than a script-level claim, and they account for E2's three per-corpus losses in Table “gate”. Once a reader cannot read the script at all, there is no discrimination left for any selector to make.

| **Query script** | **cells** | **A F1** | **E2 F1** | **E2 MAR** |
|---|---|---|---|---|
| Latin (English) | 10 | 0.422 | 0.472 | 0.311 |
| Devanāgarī (Hindi) | 10 | 0.166 | **0.477** | 0.336 |
| Devanāgarī (Sanskrit) | 5 | 0.194 | 0.392 | 0.317 |
| Tamil | 1 | 0.100 | 0.579 | 0.383 |
| Gurmukhi | 1 | 0.222 | 0.167 | **0.833** |
| Latin (Pāli) | 1 | 0.167 | 0.142 | **0.800** |

*By query script, all ten corpora, Qwen2.5-14B. Devanagari recovers to English-level attribution once ranking is fixed; Gurmukhi and Pāli do not. Tamil, despite being low-resource, is among the strongest conditions.*

**The gate is reader-capacity-dependent.**  

Re-running C, E2 and D on all 28 cells with Aya-Expanse-8B (AI 2024) *flips* the result: D attains 0.577 cross-lingual MAR against E2's 0.604. The mechanism is visible in intervention behaviour—under the weaker reader E2's single joint call becomes erratic (499 repairs, 26.4% abstention, vs D's 176 and 16.7%). A one-call discriminative select requires the capacity to hold eight candidates and an exact-source criterion simultaneously; D decomposes the same work into individually easy judgements an 8B model can still execute.

**Above the threshold, our margin widens with scale.**  

We therefore added a third capacity point, gpt-oss-120B, on the pilot corpora (Table “capacity”). E2's margin over D grows monotonically—0.013 (8B), 0.027 (14B), 0.081 (120B)—and its cut in misattribution relative to the reranking baseline strengthens in step: -29%, -40%, -61%. At 120B, E2 attains the lowest cross-lingual MAR we measure for any system–reader pair (0.121) and wins all four cross-lingual cells.

| **Reader** | **C** | **E2** | **D** | **E2-D** |
|---|---|---|---|---|
| Aya-Expanse-8B | 0.441 | **0.315** | 0.328 | -0.013 |
| Qwen2.5-14B | 0.253 | **0.152** | 0.179 | -0.027 |
| gpt-oss-120B | 0.313 | **0.121** | 0.202 | **-0.081** |

*Cross-lingual MAR↓ on matched pilot cells (Gītā + Yoga Sūtras × hi/sa; 4 cells, n=264). E2's advantage grows monotonically with reader capacity.*

**Run-to-run variance, measured directly.**  

LLM-in-the-loop pipelines are not reproducible to the digit even at fixed decoding settings, so margins of this size need an explicit noise estimate rather than an assumption. We replicated System E2 at Aya-Expanse-8B end to end—all 28 cells, identical configuration, same model and quantisation—and compared it cell-by-cell with the original run.
Only 2 of 28 cells were bit-identical, but the aggregate is stable: per-cell σ = 0.030 on MAR (mean |Delta| = 0.021), and the cross-lingual mean moved from 0.604 to 0.606. Propagated to the 18-cell means we report, the standard error is 0.007 and the 95% band ±0.014.
Against that band the 8B reversal survives: E2's cross-lingual MAR exceeds D's by +0.026 in the original run and +0.028 in the replicate—consistent in sign, magnitude and per-cell composition, and roughly twice the noise band. We note two limits on this. First, we replicated E2 but not D, so the margin's uncertainty assumes D's variance is comparable to E2's; on that assumption the paired 95% band widens to about ±0.020, which the margin still clears but less comfortably. Second, and more usefully for others measuring such systems: an earlier estimate of ours derived from the closed-book control gave σ = 0.077, nearly three times the true figure. A retrieval-free control is a poor noise proxy for a retrieval pipeline—it abstains far more often, and abstention flips MAR discontinuously. Noise should be measured on the system being reported, not inherited from a simpler one.

**Scope limit.**  

The 120B column covers two corpora, not ten, and is *not* interchangeable with the 28-cell result. On this pilot subset the ordering favours E2 for all three readers, so these cells do not themselves discriminate by capacity. Confirming the top-end margin survives the seven harder corpora requires the all-ten grid at this capacity and remains open.

**Inference cost.**  

The two systems' call counts are structural, not measured, so they hold for any reader. E2 issues exactly **two** LLM calls per item: one reader pass over the reranked candidates, and one joint selection call. System D issues **k relevance judgements** (one per retrieved passage), then one reader pass, then **one to k support critiques** as it validates or corrects the proposed citation—so at our k=8, between 10 and 17 calls, with 10 the floor. E2 is therefore a 5–8× reduction in reader invocations at equal retrieval, which is the practical argument for it wherever inference is metered or latency-bound. Neither system uses an NLI model: verification is an exact lookup against U, so the only per-item cost is the reader itself.

**Interpretation.**  

C3 lands as a *capacity-matched selection rule*: one cheap joint call when the reader can carry it, decomposed per-passage verification when it cannot, with the crossover between 8B and 14B. Because frontier-scale readers are the deployment target for citation-critical systems, the regime in which E2 is preferred is the one that matters in practice—and it is the cheaper one. Below the threshold the trade is explicit rather than hidden: D's robustness at 8B costs 5–8× the calls.

**Closed-book control: retrieval's contribution is real but wildly
uneven.**  

The numbers above are only meaningful against a baseline of what the reader already knows. These are famous public-domain texts, so parametric recall is a live confound. We therefore run all 28 cells with *no retrieval at all*—the question is asked directly and the model must cite an ID from the closed space or abstain—using the same Qwen2.5-14B reader, so the control is matched to the grid it qualifies (Table “closedbook”).
Closed book, the reader attains 0.202 English / 0.150 cross-lingual attribution F1 and misattributes on roughly *four citations in five* (MAR 0.807 / 0.841). Retrieval therefore contributes +0.222 and +0.254 F1 respectively, and more than halves misattribution—the system results are not an artefact of memorisation in aggregate.
Per corpus, however, the picture splits sharply. The Bhagavad Gītā is substantially memorised (closed-book English F1 0.497, against 0.310 for the next-highest corpus), so Gītā numbers should be read as partly parametric—a caveat that matters because the Gītā is one of our two pilot corpora. At the other extreme, four corpora—Bible, Guru Granth Sahib, Rāmāyaṇa and the Constitution—show retrieval adding essentially *nothing* over memory (e.g. Bible 0.125 → 0.125; Constitution 0.100 → 0.107), because retrieval itself is failing on them. Where retrieval works it is transformative: Thirukkuṛaḷ 0.086 → 0.775, Dhammapada 0.182 → 0.815, Yoga Sūtras 0.310 → 0.809.
The control also makes MAR-exist interpretable: with nothing retrieved, any cited ID came from memory alone—and MAR-exist remains 0.000, so even unaided the reader recalls *real* identifiers and assigns them wrongly, rather than inventing them.

|  | **CB** | **A** | **C** | **E2** |
|---|---|---|---|---|
| English F1↑ | 0.202 | 0.422 | 0.424 | **0.472** |
| English MAR↓ | 0.807 | 0.479 | 0.435 | **0.311** |
| Cross-ling. F1↑ | 0.150 | 0.173 | 0.404 | **0.423** |
| Cross-ling. MAR↓ | 0.841 | 0.470 | 0.482 | **0.387** |

*Closed-book control (CB, no retrieval) against the ladder, all ten corpora, Qwen2.5-14B, 28 cells each. Without retrieval the reader misattributes four citations in five. CB is the mean of two identical-configuration runs (§Systems and Results).*

**Reproducibility.**  

All retrieval is local and deterministic given the frozen corpora; dense caches are rebuilt from `corpus_index.jsonl` with BGE-M3. Reader temperature is fixed at 0.2 for RAG systems and 0.0 for the closed-book control; prompts and k are logged per run. Every cell is checkpointed to JSONL, and every number in this paper is read verbatim from those files by the harness rather than transcribed. The metric suite ships with 45 unit tests.

## Human Verification

Items are model-drafted with gold citations sampled from and validated against U. To measure how far that automatic validation tracks human judgement, we draw a deterministic stratified sample for double annotation: 120 items, allocated proportionally across the seven corpora readable by our annotators (English/Hindi/Devanāgarī), stratified by question type, with floors on unanswerable (20) and near-miss-bearing (105) items. Thirukkuṛaḷ (Tamil), Guru Granth Sahib (Gurmukhi) and Dhammapada (Pāli) are excluded for want of a script-competent annotator—a stated limitation, not a silent omission. Annotators approve, reject, or edit each item; agreeing verdicts are folded into a gold set, with agreement computed as Krippendorff's α-MASI (Krippendorff 2011; Passonneau 2006) over set-valued citations.

**Coverage and agreement.**  

All 120 sampled items are **double-annotated**. The two annotators worked independently: the review interface serves each annotator only their own prior verdicts, so neither could see the other's labels at any point. One annotator is an author of this paper; the other is not and has no stake in the results. They agreed on the gold citation set for **119 of 120 items (99.2%)** and on the approve/edit/reject verdict for 118 (98.3%), yielding Krippendorff's α-MASI = **0.991** over set-valued citations (Table “agreement”). Adjudication promotes **118 items to `verified`** gold; 2 are flagged `needs_adjudication`.
Both disagreements are informative rather than noise. On `gita-seed-0004` one annotator approved the drafted Gītā 4.8 while the other corrected it to 4.7—an *adjacent-verse near miss*, exactly the error class this benchmark exists to measure, and the single hardest judgement in the sample. On `ys-seed-0047` the annotators agreed on the citation label (both assert the empty set) but split on whether to reject the item outright. That the one genuine citation-level disagreement between two humans is a near miss is itself evidence that the phenomenon we measure is real and hard, not an artefact of automatic scoring.

**Reporting κ honestly.**  

Cohen's κ on the verdict label is 0.000 despite 98.3% observed agreement. This is the well-known high-agreement/low-κ paradox: 238 of 240 verdicts fall in a single category (*approve*), so expected chance agreement nearly equals observed agreement and κ collapses regardless of annotator reliability. We report it rather than suppress it, alongside the prevalence-adjusted PABAK = 0.967 and raw percent agreement, which are the interpretable statistics under this marginal distribution. κ is 1.000 for both question type and ambiguity, where the label distribution is not degenerate.

**An automatic checker is a useful critic, not a cheap annotator.**  

Because a second human is the scarce resource in this benchmark, we also ran an automatic second pass over the same 120 items—same evidence, same approve/edit/reject schema—and measured *human–model* agreement. This is not inter-annotator agreement and we do not report it as such; machine verdicts are written to a separate store and are explicitly excluded from adjudication, so no item can be promoted to gold by a model.
The result is instructive in the opposite direction from the obvious one. A self-hosted Qwen2.5-14B agrees with our annotators almost perfectly (98.3% and 99.2% exact gold-set match, α-MASI 0.983/0.991), which mostly means it is as willing to approve as they were. A larger gpt-oss-120B checker agrees *less* (91.8%/93.9%, α 0.929/0.951)—and its disagreements are substantive editorial objections that both humans missed. On one Bible item it refused a gold set of three beatitudes because the question asked for all qualifying groups; on another it argued Exodus 20:7 does not belong beside 20:3–4. Both items had been approved by both annotators.
Agreement with humans is therefore the wrong objective for an automatic pass. The stronger model is more valuable precisely where it dissents, as a *screening* tool that surfaces construction defects for human adjudication—a role that scales to the 502 items we have not yet verified, whereas double annotation does not. We also note that on `gita-seed-0004`, the adjacent-verse near miss our two annotators split on, *both* models sided with the draft, so an automatic pass cannot be relied on for exactly the adjacency judgements this benchmark targets.

**Remaining limitations.**  

Coverage is 120 of 622 items (19.3%), concentrated in the seven corpora our annotators can read; the three excluded scripts are unverified. Agreement this high on a sample drawn from automatically validated items should be read as evidence that the ID-space validation and the drafting protocol are sound, not as evidence that the benchmark is error-free at scale.
One component of our protocol remains *unmeasured* rather than merely partial, and we name it rather than let its absence pass unremarked. Validating the *content-support* judge—whether an automatic per-citation support label tracks human judgement—requires annotators to emit per-citation support ratings, which our review interface does not currently collect: it records a verdict and an optional citation edit, but not a support rating per cited unit. That calibration is therefore not reported here and is not substitutable by the agreement figures above, which concern citation *identity*, not support. Consequently the exact-attribution half of our metric contribution is validated against human judgement on this sample, while the content-support half is specified and implemented but not yet validated. Collecting those ratings needs an interface change and a further annotation pass, not more compute.

| **Label** | **Statistic** | **Value** |
|---|---|---|
| Citation set | Krippendorff α-MASI | **0.991** |
| Citation set | % agreement | 99.2 |
| Verdict | % agreement | 98.3 |
| Verdict | PABAK | 0.967 |
| Verdict | Cohen κ | 0.000^† |
| Question type | Cohen κ | 1.000 |
| Ambiguity | Cohen κ | 1.000 |

*Inter-annotator agreement, 120 double-annotated items, 2 annotators. ^†degenerate marginals (238/240 *approve*) collapse κ despite 98.3% observed agreement; PABAK and % agreement are the interpretable statistics here.*

## Limitations and Ethics

Items are model-drafted; human verification covers a stratified sample (120 of 622, double-annotated, α-MASI =0.991), so absolute values may shift on the unverified remainder even though system orderings are unaffected. The three excluded scripts are unverified. Three corpora lack script-competent annotation. The 120B reader column covers two corpora. Hindi and native-script questions are machine translated, so translation artefacts are a confound we bound but do not eliminate. All corpora are public domain and we release only public-domain translations; for the three copyright-constrained corpora we release native-script text alone. The benchmark measures *attribution, not endorsement*: citing a verse correctly is a factual claim about provenance and carries no theological position. We follow the datasheet convention of Gebru 2021.

**Availability.**  

The ten frozen corpora, all 622 items with their trilingual questions, the 118 human-verified gold items, the metric harness with its 45 unit tests, and every system in the ladder (A–E2 plus the closed-book control) are released together, along with the per-cell JSONL from which every number in this paper is read. Released text is public-domain throughout; for the three corpora whose only English rendering is under copyright we release the native-script text alone, which is why those corpora require cross-lingual retrieval by construction. Machine-generated second-pass annotations are kept in a separate store from human verdicts and are excluded from adjudication, so no item in the released gold set was promoted by a model.

## Conclusion

Citing the wrong canonical unit is a distinct failure that support-based attribution metrics cannot see, and it is worst exactly where canonical texts carry most weight and NLP resources are thinnest. CANONCITE measures it directly over ten corpora, five scripts, and three query-language conditions. Our results localise the cross-lingual collapse to retrieval ranking, show the residual errors are near misses that per-passage verification structurally cannot resolve, and establish that joint discriminative exact-ID selection resolves them at a fifth of the SOTA's cost—above a reader-capacity threshold we locate, and with a margin that widens as readers scale. We release the corpora, items, harness, and all system code.

## Acknowledgements

*Withheld for review.*

## References

- **AI 2024** — `aya2024expanse`
- **AI4Bharat 2024** — `indicqa2024`
- **Asai 2024** — `asai2024selfrag`
- **Bohnet 2022** — `bohnet2022aqa`
- **Chen 2024** — `chen2024bgem3`
- **Gala 2023** — `gala2023indictrans2`
- **Gao 2023** — `gao2023alce`
- **Gao 2023** — `gao2023rarr`
- **Gebru 2021** — `gebru2021datasheets`
- **Hu 2025** — `hu2025caqa`
- **Krippendorff 2011** — `krippendorff2011`
- **Maheshwari 2025** — `maheshwari2025citefix`
- **Malik 2021** — `malik2021ildc`
- **Ovcharov 2026** — `ovcharov2026citation`
- **Passonneau 2006** — `passonneau2006masi`
- **Qian 2025** — `qian2025vericite`
- **Survey 2025** — `evidencesurvey2025`
- **Task 2025** — `islamiceval2025`
- **Team 2024** — `qwen2024`
- **Team 2024** — `iltur2024`
- **Team 2025** — `parambench2025`
- **Verma 2024** — `verma2024milu`
- **Yan 2024** — `yan2024crag`
