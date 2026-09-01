# CANONCITE: A Multilingual, Multi-Tradition Benchmark for Canonical-Citation Attribution and Abstention

> Rendered from `canoncite.tex` by `tex2md.py`. The `.tex` is the submission artefact; regenerate this file rather than editing it.

## Abstract

When a model cites a canonical source, a scripture verse or a constitutional article, citing the *wrong* unit is a distinct and more damaging failure than citing nothing. Existing attribution benchmarks score whether a claim is supported by a retrieved passage; they cannot detect that the model named Gita 2.48 when the source was 2.47. We introduce **CANONCITE**, a benchmark for *exact-ID* citation attribution and abstention over ten public-domain canonical corpora spanning four traditions and five scripts (188,557 citable units), every question posed in English, Hindi and the corpus's native script. Instantiating a six-system ladder, we show the cross-lingual collapse is a *retrieval-ranking* failure: on our two pilot corpora, attribution F1 under non-English queries rises from 0.177 to 0.690 through hybrid and reranked retrieval alone, with the gold unit retrieved but ranked at median 7–13. A joint discriminative exact-ID selector then attains the lowest misattribution of any system at two LLM calls per item, but a paired bootstrap places that advantage precisely: significant on English queries under the coverage-corrected metric, and *directional rather than established* cross-lingually, where it depends on the resampling unit and on whether abstention is removed from the denominator. Contrary to our hypothesis, its gain comes from eliminating *implausible* citations rather than resolving near misses. Human verification covers a stratified 120-item sample (α-MASI 0.991, on a sample where annotators approved 99% of items).

## Introduction

Retrieval-augmented generation is now the default remedy for factual hallucination, and a mature literature evaluates whether a generated claim is *supported* by the passages a system retrieved (Gao 2023; Bohnet 2022; Hu 2025). That framing has a blind spot. In domains organised around a fixed, publicly known identifier scheme (scripture verses, statutes, constitutional articles, case law) the citation is not a pointer to evidence but a *claim about identity*. A model that answers a question about non-attachment correctly but attributes it to Bhagavad Gītā 2.48 instead of 2.47 has produced a fluent, well-supported, and false citation. Support-based metrics score it as a success: the neighbouring verse is on the same theme and entails much the same content.
This is most consequential where canonical texts matter most and NLP resources are thinnest: religious and legal corpora in Indian languages, queried in Hindi or the text's own script. Yet Indic benchmarks evaluate *understanding* via MCQ (Verma 2024; Team 2025; AI4Bharat 2024), and the one prior line exploiting fixed identifiers covers a single jurisdiction in a single language (Ovcharov 2026).

**Contributions.**  

We claim neither the fixed-ID idea (Ovcharov 2026), nor first religious verse-attribution (Task 2025), nor Indian scripture knowledge (Team 2025; Verma 2024). Our contributions are:
- **C1: Benchmark.** The first multilingual, multi-tradition, multi-script canonical-citation attribution and abstention benchmark: ten corpora, 188,557 citable units, 622 items, each posed in English, Hindi, and native script. The *cross-lingual, multi-script attribution axis* is the load-bearing, genuinely unoccupied novelty (§The CANONCITE Benchmark).
- **C2: Metric suite.** A corpus-agnostic exact-attribution harness operating over normalised IDs, integrating the fixed-ID existence check (Ovcharov 2026) with the citation precision/recall paradigm (Gao 2023) and adding misattribution and abstention measures (§Metrics).
- **C3: A characterised selection rule (secondary).** A joint discriminative exact-ID selector (E2) with the lowest misattribution of any system we test, at two LLM calls per item. It leads on misattribution in every condition we measure and is significantly better than the SOTA per item on English queries, but it *trails* that baseline on English F1 (0.472 vs 0.554), which cites far more often; and cross-lingually the advantage is not establishable at this scale, depending on the aggregation and the resampling unit. Its advantage is also capacity-gated, reversing below a threshold between 8B and 14B. We present E2 as a probe of *why* residual attribution errors are hard, not as a system we claim beats the state of the art.
- **C4: Findings.** The cross-lingual collapse is localised to retrieval *ranking* (the gold unit is retrieved but ranked at median 7–13); the near-miss share of residual misattributions grows from 8% to 13% as systems improve, reaching 1.8× the measured chance rate while remaining a minority; and MAR-exist =0.000 throughout separates “cannot read the language” from “misattributes”.

**Status of this release.**  

CANONCITE v1 ships model-drafted items whose gold citations are sampled from, and automatically validated against, the closed corpus ID space. Human verification covers a stratified sample of 120 items, **double-annotated**, with Krippendorff's α-MASI =0.991 on citation sets and 118 items promoted to verified gold (§Human Verification). All system comparisons are *relative* comparisons over a common, automatically validated label set: the caveat applies identically to every system, so the orderings are unaffected, while absolute values may shift.

## Related Work

**Attribution benchmarks.**  

ALCE (Gao 2023), AQA (Bohnet 2022), and CAQA (Hu 2025) score whether a generated claim is entailed by retrieved passages, typically via NLI, in English. Their unit of truth is *support*, not identity; a near-miss citation to a semantically equivalent neighbour is scored correct. Surveys of evidence-based generation (Survey 2025) confirm this framing dominates.

**Fixed-ID attribution.**  

Ovcharov 2026 shows a closed citation graph turns verification into an exact lookup, for US legal citations in English. We adopt and credit the idea; our contribution is extending it across traditions, scripts and query languages, a generality claim no prior fixed-ID work makes.

**Indic and religious NLP.**  

MILU (Verma 2024), ParamBench (Team 2025) and IndicQA (AI4Bharat 2024) evaluate Indic *understanding* via MCQ; IL-TUR (Team 2024) and ILDC (Malik 2021) cover Indian legal reasoning without exact-citation scoring. IslamicEval (Task 2025) targets verse hallucination in one tradition, monolingually. None measures exact-ID attribution across languages and scripts.

**Repair methods.**  

CiteFix (Maheshwari 2025), VeriCite (Qian 2025), RARR (Gao 2023), Self-RAG (Asai 2024) and CRAG (Yan 2024) verify or repair per-passage; we find the family largely subsumed once ranking is fixed.

## The CANONCITE Benchmark

**Corpora.**  

Ten public-domain canonical texts spanning Hindu, Buddhist, Sikh and Christian traditions plus Indian constitutional law, in five scripts. Each corpus is frozen as a `corpus_index.jsonl` keyed by its own canonical identifier scheme (`2.47` for Gītā chapter.verse; `Art.~370` for the Constitution), giving a closed ID space U per corpus. Only public-domain translations are released; where the only English translation is under copyright (Rāmāyaṇa, Mahābhārata, Guru Granth Sahib), we release the native-script text alone, an honest constraint that makes those corpora *require* cross-lingual retrieval.

| **Corpus** | **Units** | **Script** |
|---|---|---|
| Mahābhārata | 73,816 | Devanāgarī |
| Guru Granth Sahib | 60,555 | Gurmukhi |
| Bible | 31,095 | Latin |
| Rāmāyaṇa | 18,761 | Devanāgarī |
| Thirukkuṛaḷ | 1,330 | Tamil |
| Constitution of India | 1,219 | Latin/Dev. |
| Bhagavad Gītā | 701 | Devanāgarī |
| Upaniṣads | 462 | Devanāgarī |
| Dhammapada | 423 | Latin (Pāli) |
| Yoga Sūtras | 195 | Devanāgarī |
| **Total** | **188,557** | 5 scripts |

*The ten frozen corpora. Every unit is addressable by its canonical ID.*

**Items.**  

622 items across all ten corpora, each carrying a question, a gold answer, gold citation ID(s) validated against U, near-miss distractors (adjacent same-theme units), a question type, and an ambiguity label. Five question types (*factual*, *retrieval*, *conceptual*, *interpretive*, *unanswerable*) exercise different failure modes; unanswerable items carry `must_abstain` and no gold citation, so abstention is measured rather than assumed. Every item is fully trilingual: Hindi and native-script questions were produced with IndicTrans2 (Gala 2023) (Pāli by prompted generation, which IndicTrans2 does not cover). Gold citations are language-independent, so the three language conditions are matched by construction, the comparison isolates query language and nothing else.

**Construction protocol.**  

A version-hashed `corpus_index.jsonl` per corpus fixes U; nothing downstream may cite an ID outside it. Items are drafted by a pinned LLM *conditioned on retrieved real units*, over-generating ~1.5×; unanswerable items come from out-of-corpus topics and cross-corpus swaps. Every drafted citation is validated against U, so a fabricated identifier cannot enter by construction, and model output is a draft that annotators confirm or correct against the open corpus.

**Tiered annotation.**  

Annotator scarcity, not compute, is the binding constraint, so we declare two tiers rather than hide a quality gradient: Tier A (Gītā, Bible, Constitution, Thirukkuṛaḷ) targets full double annotation with per-citation support labels; Tier B covers auto-checkable item types only, extending the language and tradition axes cheaply. Tiers are recorded in the datasheet.

## Metrics

All metrics operate over normalised IDs against U, so verification is exact lookup with no NLI model. An item has gold set G; a system emits cited set C.
- **Attribution P/R/F1 (exact)**: set overlap of C and G, plus a *span* variant crediting a correct chapter with a wrong verse.
- **Misattribution Rate (MAR)**: fraction of *citing* items where C not⊆ G, decomposing into **MAR-exist** (an ID not in U: a fabricated identifier) and **MAR-support** (a real but wrong unit).
- **Near-miss MAR (NMR)**: the share of wrong citations landing on a declared distractor.
- **Abstention accuracy**, **over-citation** and **wrong-abstention**, over the `must_abstain` items.

MAR-exist is 0.000 in every run we report: models cite *real* units incorrectly rather than inventing identifiers. This separates a base-competence failure from an attribution failure and is why exact-ID scoring is informative here.

## Systems and Results

**The ladder.**  

**A** naive BM25 RAG; **B** hybrid BM25+dense RRF (BGE-M3 (Chen 2024) + FAISS); **C** hybrid plus cross-encoder reranking; **E** a binary per-candidate verify-and-repair layer, run as an ablation on BM25 retrieval only and therefore absent from the system tables; **D** an inference-time reproduction of Self-RAG (Asai 2024) + CRAG (Yan 2024), where a CRAG-style evaluator labels each passage and a Self-RAG ISSUP critique keeps a citation only if the passage supports it; and **E2** (ours), which presents all reranked candidates *jointly* and forces one exact-source choice or abstention, one LLM call rather than up to k. Grid: systems × 10 corpora × query language (en/hi/native) = 28 cells per system. Primary reader Qwen2.5-14B-Instruct (Team 2024), self-hosted; all prompts, temperatures and k fixed and logged. We pre-committed to a decision gate: *E2 must beat D on cross-lingual MAR*.

**The collapse is a ranking failure.**  

On the two pilot corpora System A attains 0.719 attribution F1 under English queries and collapses to 0.177 under Hindi/native queries, with misattribution at 0.757. A recall probe resolves the cause: the gold unit *is* retrieved under cross-lingual queries but ranked at median 7–13, outside the reader's window. Fixing ranking alone (dense hybrid retrieval, then cross-encoder reranking) lifts cross-lingual F1 to 0.626 and then 0.690 and cuts MAR from 0.757 to 0.196, without touching the reader. Applying the binary verify-and-repair layer (E) to BM25 retrieval barely moves cross-lingual F1 (0.177 → 0.173): a verifier can only repair *to* a unit retrieval actually surfaced, so this family is subsumed once ranking is fixed.
Table 2 isolates the mechanism. Dense hybrid retrieval *finds* the gold unit almost always (R@50 = 0.93–0.99) in every language, but under cross-lingual queries ranks it at median 7–13, below the reader's top-5 window; English queries place it at rank 1. The collapse is therefore neither a coverage failure nor a reasoning failure. Two levers follow (widen k, or rerank) and widening plateaus then hurts: a k-sweep of System E improves through k≈10 but *regresses* at k=20 (Gītā Hindi 0.683→0.670) as the reader drowns in noisy passages. Reranking is the right lever, and C@5 (0.690) beats E@10 (0.659) accordingly.

| **Corpus × lang** | **R@5** | **R@20** | **R@50** | **med. rank** |
|---|---|---|---|---|
| Gītā · en | 0.800 | 0.943 | 0.986 | **1** |
| Gītā · hi | **0.357** | 0.857 | 0.986 | **7** |
| Gītā · sa | 0.557 | 0.843 | 0.943 | 5 |
| Yoga S. · en | 0.932 | 0.955 | 0.977 | **1** |
| Yoga S. · hi | **0.227** | 0.773 | 0.932 | **12** |
| Yoga S. · sa | **0.227** | 0.727 | 0.955 | **13** |

*Recall@k of the gold unit under hybrid BM25+BGE-M3 retrieval, answerable items. Retrieval *finds* the gold unit cross-lingually (R@50 ≈ 0.93–0.99) but *ranks* it far below the top-5 window. The collapse is a ranking failure.*

|  | **F1**↑ | **MAR**↓ |  |  |
|---|---|---|---|---|
| **System** | en | x-ling | en | x-ling |
| closed-book | 0.202 | 0.150 | 0.807 | 0.841 |
| A naive BM25 | 0.422 | 0.173 | 0.479 | 0.470 |
| B hybrid | 0.440 | 0.416 | 0.464 | 0.446 |
| C rerank | 0.424 | 0.404 | 0.435 | 0.482 |
| D Self-RAG/CRAG | **0.554** | **0.440** | 0.344 | 0.443 |
| E2 (ours) | 0.472 | 0.423 | **0.311** | **0.387** |

*The full ladder by query condition, all ten corpora, Qwen2.5-14B, macro over cells (10 English, 18 cross-lingual). The English column is the control for every cross-lingual claim in this section.*

**The English condition, where D looks best on F1.**  

The control column of Table 3 contains the largest system gap in this paper, and it does not favour us: on English queries D reaches 0.554 attribution F1 against E2's 0.472. We say so plainly, and then explain it, because the explanation is the same mechanism this section is about. D cites on 67.8% of English items to E2's 51.1%; F1 rewards attempting and penalises declining, so a system that answers more often collects more correct citations, and more wrong ones. The asymmetry is sharper than those two figures suggest: D's citation coverage falls by 12.3 points from English to cross-lingual queries, E2's by 0.9, so D attempts disproportionately more in exactly the condition where attempting pays. Scored per item attempted, the ordering inverts and the margin is the clearest in the paper: E2 makes **0.085** wrong citations per English item against D's **0.153** and C's 0.141, a difference of -0.068 with a 95% interval of [-0.123,-0.017] that excludes zero, the only E2-versus-D comparison in this work that is significant under the coverage-corrected metric.
This also disposes of a rival reading of our whole method result. If E2's advantage were merely a well-tuned decline threshold, it should pay off where the reader is *weakest*; instead it is largest and only significant where the reader is *strongest*. That is consistent with the capacity pattern reported below and inconsistent with abstention-tuning as the explanation.

**Reranking's advantage does not replicate at scale.**  

A second disagreement between the pilot corpora and the full grid deserves the same treatment. On the pilot, reranking clearly beats plain hybrid retrieval (C 0.690 vs B 0.626 cross-lingual F1), which is the basis for our claim that reranking is the right lever. Across all ten corpora the ordering reverses (B 0.416 vs C 0.404 F1, and B 0.446 vs C 0.482 MAR), though neither difference is significant (F1 -0.012, CI [-0.076,+0.037]; MAR +0.036, CI [-0.067,+0.125]). The defensible claim is therefore narrower than the pilot suggests: *ranking* is the lever, and reranking is one way to fix ranking that is clearly better than BM25 but not distinguishable from hybrid dense retrieval at scale.

**Does E2 beat the baselines? A paired bootstrap.**  

Our margins are close enough to measurement noise that point estimates cannot carry the claim, so we test them, over *all 18* cross-lingual cells. Two conventions matter and we state them rather than let a subset do silent work. First, MAR is undefined when a system cites nothing: C cited nothing under Hindi queries for Bible and the Constitution, so macro comparisons involving C use the 16 cells where both systems are defined, while E2-vs-D uses all 18. Second, those same cells are perfectly *defined* for wrong-citations-per-item (zero wrong citations over n items is 0.000, the best possible score) so every per-item comparison uses all 18. Excluding them would drop the two cells where the baseline scores perfectly on the metric we introduced precisely to neutralise selectivity. One consequence: each paired margin is computed on the cells common to that *pair*, so it will not in general equal the difference of the two headline means. E2-vs-D uses all 18 and does reconcile (0.387-0.443=-0.057); E2-vs-C uses 16, on which the means are 0.402 and 0.482 rather than 0.387 and 0.482.

| **Pair** | **Metric** | **Margin** | **95% CI** |
|---|---|---|---|
| *cluster bootstrap over cells* |  |  |  |
| E2 vs D | macro MAR | -0.057 | [-0.129,-0.002] |
| E2 vs C | macro MAR | -0.080 | [-0.141,-0.024] |
| E2 vs D | wrong/item | -0.027 | [-0.059,+0.005] |
| E2 vs C | wrong/item | -0.016 | [-0.063,+0.033] |
| D vs C | macro MAR | -0.026 | [-0.067,+0.017] |
| D vs C | wrong/item | +0.012 | [-0.039,+0.072] |
| *item-level bootstrap* |  |  |  |
| E2 vs D | wrong/item | -0.027 | [-0.051,-0.004] |
| E2 vs C | wrong/item | -0.016 | [-0.039,+0.008] |

*Paired bootstrap (B=10,000), negative favours the first system. Significance depends on both the aggregation and the resampling unit. We omit macro~×~item-level, for which resampling items does not induce a well-defined distribution over per-cell rate averages.*

**Directional, not robust (cross-lingually).** On the 18 cross-lingual cells E2 leads on point estimates under both metrics (macro MAR 0.387 vs D 0.443, C 0.482; per item 0.139 vs C 0.154, D 0.166), but significance depends on choices a reader could make differently. Under macro MAR E2 beats both baselines; under the coverage-corrected metric the cluster bootstrap finds nothing significant, while an item-level bootstrap finds E2-vs-D significant ([-0.051,-0.004]) only by treating items as independent, ignoring the clustering corpus and language induce. With 18 clusters the cluster bootstrap is the conservative and appropriate choice, and we take its reading: **cross-lingually E2 leads on every point estimate but we cannot establish it at this scale.** (English is the exception and is treated above: there the per-item margin *is* significant, and D leads on F1.) We apply no multiple-comparison correction over these six tests; the E2-vs-D macro interval (upper bound -0.002) would not survive one.

**The pre-committed gate, adjudicated.**  

We pre-specified that E2 must beat D on cross-lingual MAR. **On its own terms it passes**: 0.387 versus 0.443, macro, which is the quantity we named. We nonetheless do not present that as the paper's result, because the analysis above convinced us the pre-specified metric was the wrong one (MAR's denominator counts only citing items, so it credits a system for declining) and under the corrected metric the margin is directional but not significant. Reporting the pass and stopping would have been defensible by the letter of our own protocol and misleading in substance.

**Aggregation, and abstention.**  

Two choices shape every margin, and we state both. First, MAR is a per-cell ratio, so averaging cells (macro) weights a 12-item Gurmukhi condition like an 80-item Bible one, while pooling over citing items (micro) weights by volume. It matters: the E2-versus-D cross-lingual margin is -0.057 macro but -0.011 micro. We report macro, because each corpus~×~language condition is an experimental unit of equal interest and pooling would let the two largest corpora settle a claim about cross-lingual generality, while naming the coincidence that macro is also the higher-variance estimator and the only aggregation under which our method result clears zero. That is part of why we read conservatively throughout.
Second, MAR's denominator counts only *citing* items, so a system that declines the hard ones can post a low rate without discriminating better, and E2 has the highest wrong-abstention rate of the three (0.470 vs D 0.409, C 0.410). We therefore also report wrong citations per *item attempted*, sum_c textMAR_c · n^textcite_c / sum_c n_c, whose denominator counts all items including declined ones. Worked example (Yoga Sūtras Hindi): n=50, n^textcite=38, textMAR=0.132, so 5 wrong citations over 50 items =0.100. This pools over cells, so multiplying the macro MAR quoted elsewhere by coverage will not reproduce it.
Cross-lingually E2 makes 0.139 wrong citations per item against C's 0.154 and D's 0.166, at citation coverages of 0.503, 0.448 and 0.556. Note what those coverages say: **C, not E2, is the most selective system**, and C also beats D per item, so selectivity and per-item accuracy do not track each other in the way the abstention objection assumes. (C's coverage is 0.448 rather than the 0.519 of the 16-cell subset precisely because the two cells where it cited nothing are included here, as they must be.) E2 attempts fewer items than D but more than C, and stays ahead of both once the advantage selectivity might confer is removed.

**The correction reorders the baselines.**  

D leads C on macro MAR (0.443 vs 0.482) but trails it per item (0.166 vs 0.154): the reproduced Self-RAG/CRAG pipeline emits *more* wrong citations per item than the reranking baseline it is built on top of, at five to eight times the LLM calls. Its lower MAR is bought by citing more often, which MAR's denominator does not charge it for. Neither margin is significant, so we claim no ordering, but the disagreement is a result about the verify-and-repair family rather than a curiosity about metrics, and it corroborates the E-on-BM25 ablation: once ranking is fixed, per-passage verification adds cost without reliably adding accuracy.

**The mechanism is not the one we hypothesised.**  

The near-miss rate says so. NMR (the share of wrong citations landing on a declared near-miss distractor) *rises* as misattribution falls: cross-lingually, C sits at MAR 0.482 with NMR 0.082, E2 at MAR 0.387 with NMR 0.129 (on the pilot corpora, 0.259/0.121 versus 0.158/0.268). E2 therefore does *not* preferentially resolve near misses; if anything the opposite. But the share must be read at its actual size: at NMR 0.129, **87% of E2's wrong citations do not land on a declared distractor at all**. Adjacency is a growing minority of the residual error, not its bulk, and we say so rather than describe the residue as concentrating on near neighbours. Two qualifications keep this from being over-read. The distractors are *model-declared* at item construction, so NMR measures adjacency as the drafting model conceived it, not as a philologist would. A rising *share* is partly arithmetic once the easy errors are gone, though the absolute near-miss rate also rises slightly (0.031 → 0.042 on the pilot), which is not automatic.
**Adjacency is over-represented, and we measure by how much.** A share is only interpretable against the chance of hitting a distractor at all. We therefore compute the base rate directly: over 228 pilot cross-lingual items, we rerank the candidate pool as the systems do and ask what fraction of the *non-gold* slots in the top-8 are declared distractors. It is **0.072**. Against that null, C's NMR of 0.082 is 1.1× chance and not distinguishable from it (z=0.5), whereas D's 0.115 is 1.6× (z=2.2) and E2's 0.129 is **1.8×** (z=2.7). So adjacency errors are genuinely over-represented among the residual errors of the stronger systems, and increasingly so as systems improve, while still accounting for a minority of them. The null assumes a wrong citation is uniform over non-gold candidates in the reranked window, and the base rate is measured on pilot conditions and applied throughout.
This also explains the capacity dependence reported below: narrowing to the right neighbourhood is a judgement an 8B reader can partly make, but choosing *within* that neighbourhood is what scales with capacity. Consistent with this, E2 has the best abstention accuracy of any system (0.955 cross-lingual, 0.986 English) and the lowest over-citation rate (0.045), but the highest wrong-abstention rate (0.470, same basis): it is the most willing to decline, which is the correct bias for citation-critical use and a cost we state rather than hide.

**Reader capacity, and how much of this is noise.**  

Swapping the reader for Aya-Expanse-8B (AI 2024) and gpt-oss-120B, holding retrieval and prompts fixed, the E2-minus-D cross-lingual MAR margin on matched pilot cells is -0.013, -0.027 and -0.081 at 8B, 14B and 120B; over the 18 cross-lingual cells of the full grid the 8B ordering reverses outright (E2 0.604 vs D 0.577). Three points of four cells each, without intervals: a direction, not an established trend.
To ask whether the 8B reversal is real, we replicated *both* systems at that reader end to end, all 28 cells each, identical configuration and quantisation. Aggregates are stable across runs (E2 0.604→0.606, D 0.577→0.583) with per-cell σ=0.030 for E2 and 0.019 for D, giving a paired 95% band of ±0.017 on an 18-cell mean with nothing assumed. The reversal clears it: the E2-minus-D margin is +0.026 and +0.023 across the two runs. One transferable caution: an earlier estimate of ours taken from the closed-book control gave σ=0.077, nearly three times either figure, a retrieval-free control abstains far more, and abstention moves MAR discontinuously. Noise should be measured on the system being reported.

**Inference cost, in calls and in tokens.**  

The call counts are structural, so they hold for any reader. E2 issues exactly **two** LLM calls per item: one reader pass over the reranked candidates, and one joint selection call. System D issues k relevance judgements (one per retrieved passage), one reader pass, then one to k support critiques, at our k=8, between 10 and 17 calls, with 10 the floor. That is a 5–8× difference in *invocations*.
Invocations are the flattering unit, so we report the other one. E2's two calls each carry *all* k candidates, whereas D's per-passage judgements carry one each. Estimating prompt tokens from the templates and measured passage lengths across five corpora, E2 uses ≈1,200 tokens per item against D's ≈2,300, **1.9×**, not 5–8×. Two qualifications: the token figure is estimated from templates, not metered; and D's k relevance judgements are batchable while E2's two calls are sequential, so under a parallel implementation D's latency disadvantage largely disappears and the argument for E2 is request count and tokens, not wall-clock. Neither system uses an NLI model: verification is an exact lookup against U.

**Closed-book control: retrieval's contribution is real but wildly
uneven.**  

These are famous public-domain texts, so parametric recall is a live confound. We therefore run all 28 cells with *no retrieval* (the question asked directly, the model citing from the closed space or abstaining) on the same Qwen2.5-14B reader, matching the control to the grid it qualifies.
Closed book the reader attains 0.202 English / 0.150 cross-lingual F1 and misattributes *four citations in five* (MAR 0.807/0.841); retrieval adds +0.222/+0.254 F1, so the results are not an aggregate memorisation artefact.
Per corpus the picture splits sharply. The Bhagavad Gītā is substantially memorised (closed-book English F1 0.497 against 0.310 for the next corpus), so its numbers are partly parametric, a caveat that matters because it is one of our two pilot corpora. Four corpora (Bible, Guru Granth Sahib, Rāmāyaṇa, Constitution) show retrieval adding essentially nothing over memory because retrieval itself fails on them; where retrieval works it is transformative (Thirukkuṛaḷ 0.086 → 0.775, Dhammapada 0.182 → 0.815).
MAR-exist remains 0.000 unaided: even from memory the reader recalls *real* identifiers and assigns them wrongly rather than inventing them.

## Human Verification

To measure how far the automatic ID-space validation tracks human judgement, we draw a deterministic stratified sample for double annotation: 120 items, allocated proportionally across the seven corpora our annotators can read (English/Hindi/Devanāgarī), stratified by question type, with floors on unanswerable (20) and near-miss-bearing (105) items. Thirukkuṛaḷ, Guru Granth Sahib and Dhammapada are excluded for want of a script-competent annotator, a stated limitation, not a silent omission.

**Coverage and agreement.**  

The two annotators worked independently: the review interface serves each only their own prior verdicts, so neither saw the other's labels. One is an author of this paper; the other is not and has no stake in the results. They agreed on the gold citation set for **119 of 120 items (99.2%)** and on the verdict for 118 (98.3%), giving Krippendorff's α-MASI =**0.991** (Krippendorff 2011; Passonneau 2006) (Table 5); adjudication promotes **118 items** to verified gold.
Both disagreements are informative. On `gita-seed-0004` one annotator approved the drafted Gītā 4.8 while the other corrected it to 4.7, an *adjacent-verse near miss*, exactly the error class this benchmark exists to measure. On `ys-seed-0047` they agreed on the citation (both empty) but split on rejecting the item. That the single citation-level disagreement between two humans is a near miss is itself evidence the phenomenon is real and hard, not an artefact of automatic scoring.

**Reporting κ honestly.**  

Cohen's κ on the verdict label is 0.000 despite 98.3% agreement, the high-agreement/low-κ paradox: 238 of 240 verdicts are *approve*, so expected chance agreement nearly equals observed and κ collapses regardless of reliability. We report it rather than suppress it, alongside PABAK =0.967 and raw agreement, which are the interpretable statistics here; κ is 1.000 for question type and ambiguity, where the marginals are not degenerate.

**An automatic checker is a critic, not a cheap annotator.**  

Because a second human is the scarce resource, we also ran an automatic pass over the same items and measured *human–model* agreement, not inter-annotator agreement: machine verdicts are stored separately and excluded from adjudication, so no item can be promoted to gold by a model. The result runs opposite to the obvious one. A self-hosted Qwen2.5-14B agrees almost perfectly (98.3%/99.2% exact match), which mainly means it is as willing to approve as our annotators; a larger gpt-oss-120B agrees *less* (91.8%/93.9%) and its dissents are substantive objections both humans missed, it refused a Bible gold set of three beatitudes because the question asked for all qualifying groups, and argued Exodus 20:7 does not belong beside 20:3–4. Agreement with humans is therefore the wrong objective for an automatic pass: the stronger model earns its place as a *screening* tool surfacing defects for adjudication, which scales to the 502 unverified items where double annotation does not. On the adjacency case our annotators split over, however, *both* models sided with the draft, so automation is unreliable for exactly the judgements this benchmark targets.

**Remaining limitations.**  

Coverage is 120 of 622 items (19.3%), concentrated in the seven corpora our annotators can read; the three excluded scripts are unverified. Agreement this high on a sample drawn from automatically validated items should be read as evidence that the ID-space validation and the drafting protocol are sound, not as evidence that the benchmark is error-free at scale.
One component is *unmeasured* rather than partial, and we name it. Validating the *content-support* judge needs per-citation support ratings, which our review interface does not collect, it records a verdict and an optional citation edit. That calibration is therefore absent and is not substitutable by the agreement above, which concerns citation *identity*. So the exact-attribution half of our metric contribution is human-validated on this sample; the content-support half is implemented but not validated, and closing it needs an interface change and another annotation pass, not compute.

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

Items are model-drafted; verification covers 120 of 622 (double-annotated, α-MASI =0.991), so absolute values may shift on the remainder though orderings are unaffected. Three corpora (Thirukkuṛaḷ, Guru Granth Sahib and Dhammapada) lack a script-competent annotator and are entirely unverified. The 120B column covers two corpora. All non-English questions are machine translated, and we *do not* bound that confound: with no natural-language queries anywhere, “cross-lingual collapse” and “translationese collapse” are not separated by our design. Two observations bear on it without resolving it (the collapse is localised to ranking rather than reading (Table 2), and Devanagari recovers to English-level attribution once ranking is fixed) neither of which is what degraded query fluency would predict. A natively-authored query set for one corpus would settle it and is the most valuable future addition.

**Ethics.**  

All corpora are public domain and we release only public-domain translations; where the sole English rendering is under copyright we release native-script text alone. The benchmark measures *attribution, not endorsement*: citing a verse correctly is a claim about provenance and carries no theological position, and no system here is intended to adjudicate religious meaning. Because the corpora span four traditions, we report per-corpus results without ranking traditions against one another, and the weakest conditions (Gurmukhi, Pāli) reflect our own release and translation constraints rather than any property of those texts. We document the release following the datasheet convention of Gebru 2021.

**Availability and reproducibility.**  

Retrieval is local and deterministic; reader temperature, prompts and k are fixed and logged. Every cell is checkpointed to JSONL and every number here is read from those files by the harness rather than transcribed. Corpora, items, the 118 verified gold items, the harness with its 45 tests and all systems are released together; released text is public-domain, with three corpora shipping native script alone for copyright. Machine annotations are stored apart from human verdicts and excluded from adjudication, so no released gold item was promoted by a model.

## Conclusion

Two results are solid. The cross-lingual attribution collapse is a *ranking* failure (retrieval finds the gold unit (R@50 0.93–0.99) and misranks it (median 7–13)) and a verify-and-repair layer cannot fix what retrieval never surfaced. And the residual error is not what we expected: joint selection removes implausible citations rather than adjacent ones, and near misses stay a minority (13%) of what remains, though at 1.8× a directly measured chance rate.
Our method result is deliberately narrow. Joint discriminative exact-ID selection attains the lowest misattribution of any system we test, at two LLM calls per item, and on English queries it makes significantly fewer wrong citations per item than the reproduced SOTA (-0.068, CI [-0.123,-0.017]), while *trailing* that system on English F1 (0.472 vs 0.554), because it cites far less often. Cross-lingually the advantage is directional but not established: significance depends on the aggregation and on whether cells or items are resampled, and the ordering reverses below a reader-capacity threshold between 8B and 14B. We offer it as a characterised probe of why near-neighbour attribution is hard, not as a system beating the state of the art. Settling that needs more cells; settling how much of the cross-lingual effect is translationese needs a natively-authored query set. We release the corpora, items, harness and all system code.

## Acknowledgements

*Withheld for review.*

---

# Appendix

## Per-corpus and per-script results

These tables are reported for auditability. We draw no per-corpus or per-script conclusions from them: cell-level uncertainty is not uniform (MAR's denominator ranges from 9 to 80 citing items across cells), and several differences here are smaller than the run-to-run σ=0.030 we measure in §Systems and Results.

**Script is not the same as low-resource.**  

Devanagari queries behave like English once ranking is fixed (E2 F1 0.477 Hindi, 0.392 Sanskrit, against English's 0.472). Hindi's 0.006 edge over English is far inside the σ=0.030 we measure, so we read those two conditions as indistinguishable rather than as a reversal of the collapse and Tamil is the *best* cross-lingual condition we measure (C F1 0.625); what collapses is Gurmukhi and Pāli (MAR 0.83, 0.80), both single-corpus conditions explained by our own release constraints, Guru Granth Sahib is the largest ID space and native-script-only for copyright, and Pāli is the one language IndicTrans2 does not cover.

| **Corpus** | **C** | **D** | **E2** |
|---|---|---|---|
| Bhagavad Gītā | 0.272 | 0.200 | 0.166 |
| Yoga Sūtras | 0.233 | 0.158 | 0.137 |
| Upaniṣads | 0.340 | 0.427 | 0.125 |
| Bible | – | 0.316 | 0.256 |
| Constitution of India | – | 0.370 | 0.265 |
| Mahābhārata | 0.375 | 0.472 | 0.312 |
| Dhammapada | 0.637 | 0.487 | 0.449 |
| Thirukkuṛaḷ | 0.317 | 0.225 | 0.282 |
| Guru Granth Sahib | 0.841 | 0.833 | 0.838 |
| Rāmāyaṇa | 0.839 | 0.844 | 0.909 |
| **All (18 cells)** | 0.482 | 0.443 | 0.387 |

*Cross-lingual MAR↓ per corpus, Qwen2.5-14B. Blank entries are cells where C cited nothing, leaving MAR undefined.*

| **Query script** | **cells** | **A F1** | **E2 F1** | **E2 MAR** |
|---|---|---|---|---|
| Latin (English) | 10 | 0.422 | 0.472 | 0.311 |
| Devanāgarī (Hindi) | 10 | 0.166 | 0.477 | 0.336 |
| Devanāgarī (Skt) | 5 | 0.194 | 0.392 | 0.317 |
| Tamil | 1 | 0.100 | 0.579 | 0.383 |
| Gurmukhi | 1 | 0.222 | 0.167 | 0.833 |
| Latin (Pāli) | 1 | 0.167 | 0.142 | 0.800 |

*By query script. Single-corpus conditions (n=1 cell) are not script-level claims.*

|  | **CB** | **A** | **C** | **E2** |
|---|---|---|---|---|
| English F1↑ | 0.202 | 0.422 | 0.424 | 0.472 |
| English MAR↓ | 0.807 | 0.479 | 0.435 | 0.311 |
| Cross-ling. F1↑ | 0.150 | 0.173 | 0.404 | 0.423 |
| Cross-ling. MAR↓ | 0.841 | 0.470 | 0.482 | 0.387 |

*Closed-book control (CB, no retrieval) against the ladder, all ten corpora, Qwen2.5-14B. CB is the mean of two identical-configuration runs.*

| **Reader** | **C** | **E2** | **D** | **E2-D** |
|---|---|---|---|---|
| Aya-Expanse-8B | 0.441 | 0.315 | 0.328 | -0.013 |
| Qwen2.5-14B | 0.253 | 0.152 | 0.179 | -0.027 |
| gpt-oss-120B | 0.313 | 0.121 | 0.202 | -0.081 |

*Cross-lingual MAR↓ on matched pilot cells (Gītā + Yoga Sūtras × hi/sa; 4 cells, n=264). Three points of four cells each, without intervals.*

## References

- **AI 2024** (`aya2024expanse`)
- **AI4Bharat 2024** (`indicqa2024`)
- **Asai 2024** (`asai2024selfrag`)
- **Bohnet 2022** (`bohnet2022aqa`)
- **Chen 2024** (`chen2024bgem3`)
- **Gala 2023** (`gala2023indictrans2`)
- **Gao 2023** (`gao2023alce`)
- **Gao 2023** (`gao2023rarr`)
- **Gebru 2021** (`gebru2021datasheets`)
- **Hu 2025** (`hu2025caqa`)
- **Krippendorff 2011** (`krippendorff2011`)
- **Maheshwari 2025** (`maheshwari2025citefix`)
- **Malik 2021** (`malik2021ildc`)
- **Ovcharov 2026** (`ovcharov2026citation`)
- **Passonneau 2006** (`passonneau2006masi`)
- **Qian 2025** (`qian2025vericite`)
- **Survey 2025** (`evidencesurvey2025`)
- **Task 2025** (`islamiceval2025`)
- **Team 2024** (`qwen2024`)
- **Team 2024** (`iltur2024`)
- **Team 2025** (`parambench2025`)
- **Verma 2024** (`verma2024milu`)
- **Yan 2024** (`yan2024crag`)
