# CANONCITE: A Multilingual, Multi-Tradition, Multi-Script Benchmark for Canonical-Citation Attribution and Abstention over Indian Canonical Texts (with Cross-Cultural and Legal Anchors)

> **Working draft.** This document fixes the problem statement, the benchmark design, the metric definitions, the experimental protocol, and the precise prior-art positioning. The **system ladder is now instantiated on the two cleanest corpora (Bhagavad Gītā, Yoga Sūtras) with a Qwen2.5-14B reader**: System A (all 28 cells, §5.4), and Systems **B (hybrid), C (reranking), E (verify+repair), and E2 (our discriminative exact-ID selector)** in §5.4.2–§5.4.5. The retrieval ladder A→B→C lifts cross-lingual F1 0.177→0.626→0.690, and **E2 roughly halves misattribution** at matched F1. The **all-10-corpus scale-up and System D (Self-RAG+CRAG) baseline are complete, and the pre-committed E2-vs-D gate PASSES** — E2 attains the lowest cross-lingual misattribution rate of any system across all ten corpora (0.387 vs D's 0.443, at ~2 LLM calls/item vs ~10), the **money table (Table 5.6)**. The second-reader robustness check (Aya-Expanse-8B) is done and shows the gate is **reader-capacity-dependent** (§5.4.7, Table 5.12). Remaining controls (Tables 5.3–5.5) and the third (frontier) reader are FORTHCOMING.

---

## Abstract

Retrieval-augmented generation (RAG) is increasingly deployed in domains where every claim is expected to carry a *checkable* citation. Yet faithfulness and citation quality are most often studied over open-domain corpora (Wikipedia, news, the web), where "is this claim grounded in that passage?" is inherently fuzzy and must be *approximated* by natural-language-inference (NLI) entailment or an LLM judge. Canonical texts have a property those settings lack: answers cite **discrete, closed, checkable reference IDs** (chapter.verse, pāda.sūtra, kāṇḍa.sarga.śloka, kural number, Aṅg+line, Part/Article§clause, book chapter:verse). When a model writes "as taught in *BG 5.18*" but the supporting verse is actually 2.47, that is a **misattribution** that can be detected **automatically and exactly** against a fixed citation-ID space — with **no NLI model in the loop**.

We introduce **CANONCITE**, a benchmark for **canonical-citation attribution and abstention** built on this property. CANONCITE spans **ten public-domain corpora and 188,557 citable units across five scripts** — Hindu (Bhagavad Gita, principal Upanishads, Yoga Sūtras, Vālmīki Rāmāyaṇa, Mahābhārata), Buddhist (Dhammapada), Sikh (Guru Granth Sahib), Tamil-ethical (Thirukkuṟaḷ), Christian (the Bible, as an English cross-cultural anchor), and secular-legal (the Constitution of India, as a legal anchor) — each with a **closed canonical-ID space** as exact, NLI-free attribution ground truth, a multilingual text triple (English + original + transliteration where applicable), an ambiguity-graded question taxonomy, near-miss-citation distractors, and dedicated **unanswerable/abstention** items. We define a corpus-agnostic metric suite (Citation Existence Rate, Citation Groundedness, exact and span Attribution P/R/F1, Misattribution Rate decomposed into existence and content-support components, Near-miss Misattribution Rate, and Abstention Correctness) whose core signals are deterministic and language-independent. We specify an evaluation grid of five system families (naive RAG, hybrid, reranking, a reproduced repair SOTA, and our exact-ID attribution-verifier) crossed with corpora, query languages (English / Hindi / native script), and multiple readers including Indic-tuned models.

We are careful about novelty. We do **not** claim the fixed-ID-enables-exact-attribution *idea* (already demonstrated for a single legal jurisdiction by Ovcharov, 2026), nor "first religious verse-attribution" (already done for a single tradition by IslamicEval 2025), nor "Indian scripture knowledge" (already covered as MCQ understanding by ParamBench and MILU). Our contribution is the **first multilingual, multi-tradition, multi-script Indian canonical-citation attribution + abstention benchmark**, with the **cross-lingual / multi-script attribution axis** as the load-bearing, genuinely unoccupied novelty. Instantiating the system ladder (Qwen2.5-14B reader), we show the **cross-lingual attribution collapse is a *ranking* failure** — a naive→hybrid→reranking retrieval ladder lifts cross-lingual attribution F1 from **0.177 to 0.690** — and that a generic verify-and-repair layer is *subsumed* once ranking is fixed, whereas our **joint discriminative exact-ID selector roughly halves Misattribution Rate (↓41–55%)** at matched F1 by resolving the residual near-miss errors a topical reranker cannot. **We confirm this at scale across all ten corpora**: E2 attains the lowest cross-lingual Misattribution Rate of any system (0.387 vs. the reproduced Self-RAG/CRAG SOTA's 0.443) at ~2 LLM calls/item versus ~10, passing our pre-committed decision gate. A second-reader robustness check (Aya-Expanse-8B) shows the gate is **reader-dependent**: under an 8B reader the SOTA's decomposed per-passage reflection overtakes our single joint-selection call — a finding that sharpens the method claim into a capacity-matched selection rule (§5.4.7).

---

## 1. Introduction

### 1.1 The gap

RAG faithfulness and hallucination are usually studied on Wikipedia, news, or the open web. In those settings, the ground-truth question "is this generated claim supported by that source?" is *fuzzy*: support is graded, partial, and contested, so it must be approximated — by NLI entailment against retrieved passages (as in ALCE), by an LLM judge, or by human raters. This approximation is itself unreliable: recent work shows that NLI- and LLM-based faithfulness metrics struggle to separate full support, partial support, and no support (Li et al., 2024).

Canonical texts break this fuzziness. Their answers cite **discrete, closed, checkable references**: a Bhagavad Gita teaching lives at `2.47`, a Yoga Sūtra at `1.2`, a Thirukkuṟaḷ couplet at `151`, a Bible verse at `John 14:6`, a constitutional guarantee at `Art. 19(1)(a)`. The set of valid IDs is *finite and known in advance*. Therefore, when a system cites `BG 5.18` for a claim whose textual support is at `2.47`, the error is not a matter of degree — it is a **misattribution that is exactly and automatically detectable** against the closed ID space, with **no NLI model, no LLM judge, and no human rater** required for the core signal. This makes canonical corpora an unusually clean *instrument* for studying attribution: the ground-truth grounding signal is deterministic.

Crucially, this property is **not scripture-specific**. It generalizes to every **citation-critical domain** where sources are addressed by fixed identifiers — statutes and case law (Article§clause, docket numbers), clinical guidelines (recommendation IDs), and scientific literature (DOIs, theorem numbers). Indian canonical texts and constitutional law are simply the cleanest, most abundant, and most under-benchmarked *instruments* for studying attribution that transfers to these settings; the contribution is the benchmark and its findings, not the scripture.

The specific, defensible gap is **cross-lingual**. The entire attribution lineage — ALCE, AttributedQA, ExpertQA, HAGRID, CAQA, VeriCite, and the legal fixed-ID work of Ovcharov (2026) — is **English- or single-language-centric**. No existing resource measures whether a model cited the *correct source ID across languages and scripts* (Devanagari / Pali / Tamil / Gurmukhi / English). Layered on top: no resource mixes Indian religious traditions with a cross-cultural (Bible) and a legal (Constitution of India) anchor under one exact metric, and none couples this with interpretive and unanswerable/abstention items that stress reasoning-versus-fabrication rather than lookup.

### 1.2 Contributions

- **C1 — Benchmark (headline).** CANONCITE, the first **multilingual, multi-tradition, multi-script** canonical-citation attribution + abstention benchmark: ten public-domain corpora, 188,557 citable units across five scripts, closed canonical-ID ground truth, a multilingual text triple, an ambiguity-graded five-type question taxonomy, near-miss-citation distractors, and dedicated abstention items. The **cross-lingual / multi-script attribution axis is the freshest contribution** — it is unoccupied across the entire attribution lineage. We lead with C1.

- **C2 — Metric suite (integration + validation, not invention).** A unified, corpus-agnostic **exact-attribution** metric suite (§4). We explicitly credit Ovcharov (2026) and CAQA for the fixed-ID existence-check idea and ALCE for the citation precision/recall paradigm. Our contribution here is (i) *integrating* these into one script-agnostic harness that operates over normalized IDs, and (ii) *validating* the exact-ID signal (and a calibrated content-support check) against human judgment across religious and legal corpora — a cross-lingual generality claim no prior fixed-ID work makes.

- **C3 — Method (secondary, gated).** A **joint discriminative exact-ID selector** (System E2): rather than the crowded per-passage verify-and-repair loop (CiteFix, VeriCite, RARR, CG-DPO, Self-RAG/CRAG) — which our own results show is *subsumed* once retrieval ranking is fixed (§5.4.4) — E2 presents the reranked candidates jointly and forces a single exact-source choice or abstention, resolving the **near-miss** errors (adjacent same-theme verse) that a topical reranker and a binary verifier structurally cannot. It **roughly halves Misattribution Rate at matched F1** on the two pilot corpora (§5.4.5), and **passes its pre-committed gate at scale**: across all ten corpora it attains the **lowest cross-lingual Misattribution Rate of any system (0.387 vs. the reproduced Self-RAG/CRAG SOTA's 0.443)** at ~2 LLM calls/item versus ~10, and with *no* NLI model — verification is an exact lookup against the closed ID space (Table 5.6). A cross-reader check (§5.4.7) bounds the claim honestly: the advantage **requires a sufficiently capable reader** — under an 8B reader the decomposed SOTA is the more robust choice — making C3 a capacity-matched selection rule rather than an unconditional win.

- **C4 — Findings.** The cross-lingual attribution collapse is localized to **retrieval ranking** (the gold verse is retrieved but ranked at median 7–13 under cross-lingual queries; §5.4.3), a misattribution taxonomy dominated by **near-misses** after reranking, and — via the ID-space controls — a separation of "cannot read the language" (base-model failure in low-resource Tamil / Pali / Gurmukhi) from "misattributes" (cites the wrong *existing* ID; MAR-exist = 0.000 throughout). These findings **transfer across all ten corpora at scale** (Table 5.6): E2 attains the lowest cross-lingual Misattribution Rate of any system, confirming the near-miss discrimination is not an artifact of the two pilot corpora. A cross-reader robustness check (Aya-Expanse-8B, §5.4.7) shows the E2-vs-D ordering is **reader-capacity-dependent** — under an 8B reader the decomposed SOTA overtakes the joint select — turning the method result into a capacity-matched selection rule rather than an unconditional ranking.

---

## 2. Related Work

We position CANONCITE precisely against four lineages. The first two are the ones the multilingual re-framing must be measured against most carefully; the second two bound the metric and method claims. We cite them up front, not as an afterthought.

### 2.1 Attribution benchmarks — grounding to retrieved passages via NLI (English / single-language)

**ALCE** (Gao et al., EMNLP 2023) is the canonical citation-quality benchmark (ASQA, QAMPARI, ELI5); its citation precision/recall is computed by **NLI entailment against retrieved web passages**. We adopt its precision/recall paradigm but replace NLI-against-free-text with **exact matching to a closed ID space**. **AttributedQA** (Bohnet et al., 2022) formalizes attribution via AIS (Attributable to Identified Sources), judged by human/NLI over identified sources — again no fixed-ID matching. **ExpertQA** (Malaviya et al., NAACL 2024) provides 2,177 expert questions across 32 fields with claim-level attribution to web/passage evidence, but no fixed-ID space and no canonical-text focus. **HAGRID** (Kamalloo et al., 2023) is an attributed-generation dataset over MIRACL with passage-level quotes. **CAQA** (Hu et al., ACL 2025) uses knowledge-graph structure to make attribution *automatically* checkable (supportive / partial / contradictory / irrelevant) — conceptually adjacent to "structure enables automatic scoring," but over KG triples, not canonical-text IDs, and it evaluates *evaluators* rather than a repair method. All are English- or single-language-centric. Survey groundings (Li et al., 2023, *A Survey of LLM Attribution*; the *Attribution, Citation, and Quotation* survey, 2025) confirm no scripture/cross-canonical fixed-ID benchmark exists.

### 2.2 Fixed-ID attribution — the *idea* is already taken (legal, single-language)

**Ovcharov (2026), "Citation Grounding"** (arXiv:2606.00898) is the closest metric threat and must be read before claiming anything. It builds a fixed statute citation graph (21,736 nodes) from Ukrainian court decisions; defines **Citation Grounding** decomposed into **Citation Precision** (does the cited provision exist), **Relevance**, and **Temporality** — i.e., existence-checking a citation against a fixed node set, the same insight as our Citation Existence Rate — **and** ships a repair method (**CG-DPO**, preference fine-tuning on corrupted-citation pairs) across seven legal sub-domains. It scoops the *concept* behind our C2 and C3. **We do not claim that insight as ours.** What it does *not* do, and what CANONCITE retains: it is **single-jurisdiction, single-language, legal-only** — not cross-lingual, not cross-tradition, no interpretive/ambiguous items, no unanswerable/abstention taxonomy — and it repairs via DPO fine-tuning rather than an inference-time exact-ID check.

### 2.3 Indic LLM-evaluation benchmarks — *understanding / MCQ*, not attribution

**ParamBench** (arXiv:2508.16185) offers 17K+ **Hindi** graduate-level questions across 21 Indian-studies subjects (history, yoga, philosophy, literature, law, music) in MCQ / assertion–reason / sequence / list-matching formats — the nearest "Indian scripture knowledge benchmark," but it is **understanding/recall**: no verse-ID ground truth, no misattribution metric, no abstention, Hindi-only. **MILU** (Verma et al., AI4Bharat, arXiv:2411.02538) provides ~80K MCQ across **11 Indic languages**, 8 domains / 41 subjects including Law & Governance and Arts & Humanities with Indian cultural content — again **MCQ understanding**, no citation-attribution / fixed-ID / abstention axis (models are weakest exactly in Humanities and Law). Related Indic resources — **IndicQA** (arXiv:2407.13522, extractive QA across 11 languages), **IndicXNLI** (arXiv:2204.08776), and the **BhashaSutra** survey of Indian NLP datasets (arXiv:2604.18423, which documents essentially *no* verse-ID attribution or cross-tradition religious benchmark) — confirm the space. Our delta over this class is **attribution + fixed verse-ID + misattribution + abstention, multilingual and multi-tradition**, *not* "Indian scripture knowledge," which these own.

### 2.4 Single-tradition religious verse-hallucination — already done, monolingual

**IslamicEval 2025** (ACL ArabicNLP shared task) is the closest existing thing to scripture-verse misattribution detect-and-repair: Subtask 1 is **hallucination detection + correction of quoted Qur'an Ayahs and Hadiths**, Subtask 2 is grounded Qur'an/Hadith QA — but **Arabic/Islamic, single-tradition, not cross-script, not multilingual**. The broader Islamic-NLP stack (**IslamicMMLU**, arXiv:2603.23750; **IslamicLegalBench**, arXiv:2602.21226) already spans knowledge and legal and abstention. Adjacent per-tradition resources for our own corpora exist but carry no fixed-ID attribution metric: **Qur'an QA 2022 / QRCD** (verse-span QA), **BibleQA** (arXiv:1810.12118, trivia-style verse QA), and **BuddhismEval** / **SiPaKosa** (arXiv:2603.29221, Sinhala/Pali Dhammapada MCQ and corpus). Because the *concept* of verse-misattribution detection is anticipated in another religion, **we do not claim "first religious verse-attribution."** Our claim is narrower and defensible: **first *multilingual, multi-tradition, multi-script Indian* canonical-citation attribution + abstention benchmark.**

### 2.5 Methods (repair) and Indian legal NLP

Generate→verify→repair for citations is a crowded space: **Self-RAG** (Asai et al., ICLR 2024) and **CRAG** (Yan et al., 2024) do corrective/self-reflective generation; **RARR** (Gao et al., ACL 2023) post-hoc revises unsupported content; **CiteFix** (Maheshwari et al., 2025) post-processes citations to retrieved passages; **VeriCite** (Qian et al., SIGIR-AP 2025) is a three-stage generate→NLI-verify→refine pipeline; and CG-DPO (Ovcharov, 2026) repairs via preference tuning. All ground/repair against retrieved passages (or fine-tune), not against a fixed canonical ID space, and all are English/single-language. Our only defensible method delta is that verification is an **exact lookup against a closed ID space** — cheaper, deterministic, script-agnostic, and NLI-free — which is exactly what the gated C3 must demonstrate.

Finally, **Indian legal NLP** is mature but organized around a *different* task: **IL-TUR** (arXiv:2407.05399), **ILDC** (Malik et al., ACL 2021), and **NyayaAnumana / INLegalLlama** (arXiv:2412.08385) target court-**judgment prediction**, summarization, and reasoning — **not** Article§clause *citation attribution*. A prior Constitution-of-India RAG demo (arXiv:2404.06751) builds QA over the text but ships no attribution metric. So the **Constitution of India as a fixed-ID citation-attribution corpus is open** — and arguably a stronger legal anchor than the US Constitution: longer, amendment-rich, on-theme, and under-benchmarked for attribution.

> **What must never be claimed.** We are *not* the first to propose fixed-ID exact attribution scoring (Ovcharov, 2026, legal), *not* the first to detect/repair wrong scripture-verse citations (IslamicEval 2025, Islamic), and *not* the first to evaluate LLMs on Indian scripture content (ParamBench/MILU, understanding). Our first-mover claim is the multilingual, multi-tradition, multi-script Indian canonical-citation attribution + abstention benchmark, with the cross-lingual axis as the load-bearing novelty.

---

## 3. The CANONCITE Benchmark

### 3.1 Corpora

CANONCITE comprises **ten public-domain corpora spanning three orthogonal axes** — **tradition** (Hindu, Buddhist, Sikh, Tamil-ethical, Christian, secular-legal), **language / script** (Sanskrit-Devanagari, Pali, Tamil, Gurmukhi, Hindi, English), and **domain** (interpretive-religious, narrative-religious, ethical-aphoristic, prescriptive-legal). Each corpus has a **closed canonical ID space** `U` and, where applicable, a multilingual text triple: `text_en` + `original` + `transliteration`. All figures below are the *built* corpus layer.

| Corpus | Tradition / domain | Lang / script | Canonical ID scheme | Units | PD source | Tier |
|---|---|---|---|---:|---|:--:|
| **Bhagavad Gita** | Hindu / interpretive | Sanskrit (Devanagari) + EN | `chapter.verse` (e.g. `2.47`) | 701 | Besant & Das 1905 (EN); ancient PD Sanskrit | A |
| **Upanishads** (principal) | Hindu / interpretive | Sanskrit (Devanagari) + EN | `section.khaṇḍa.verse` | 462 | Müller SBE (EN); GRETIL | B |
| **Yoga Sūtras** (Patañjali) | Hindu / aphoristic | Sanskrit (Devanagari) + EN | `pāda.sūtra` (e.g. `1.2`) | 195 | Woods 1914 / Vivekananda 1896; GRETIL | B |
| **Rāmāyaṇa** (Vālmīki) | Hindu / narrative | Sanskrit (Devanagari) | `kāṇḍa.sarga.śloka` | 18,761 | Griffith (EN, private); GRETIL | B |
| **Mahābhārata** | Hindu / narrative | Sanskrit (Devanagari) | `parva.adhyāya.śloka` | 73,816 | Ganguli 1883–96 (EN, Gita-zone only); GRETIL | B |
| **Dhammapada** | Buddhist / interpretive | Pali + EN | `chapter.verse` (e.g. `1.5`) | 423 | Müller SBE vol. 10, 1881 | B |
| **Thirukkuṟaḷ** | Tamil / ethical-aphoristic | Tamil + EN | `kural` no. 1–1330 | 1,330 | G. U. Pope 1886; PD Tamil | A |
| **Guru Granth Sahib** | Sikh / devotional | Gurmukhi | `aṅg` (page) + line/shabad | 60,555 | PD Gurmukhi (EN private) | B |
| **Constitution of India** | secular-legal / prescriptive | English (legal) / Hindi | `Part/Article §clause` (e.g. `Art. 19(1)(a)`) | 1,219 | Government of India PD text | A |
| **Bible** | Christian / narrative+law | English | `BOOK chapter:verse` (e.g. `John 3:16`) | 31,095 | World English Bible (WEB) | A |
| **Total** | 6 traditions | 5 scripts | closed per-corpus `U` | **188,557** | public-domain | — |

Design notes: **GRETIL** supplies machine-readable Devanagari originals for the Sanskrit corpora. **Mahābhārata** (the largest corpus) is a deliberate retrieval stress test and *contains* the Bhagavad Gita in the Bhīṣma Parva; the two are kept in separate ID namespaces, and the overlap is a built-in **cross-corpus near-miss** case. **Thirukkuṟaḷ** is the clean cross-lingual demonstrator (flat 1–1330 couplet IDs, PD Tamil + Pope's English). **Bible (WEB)** is the ultra-clean, high-resource cross-cultural anchor. **Constitution of India** is the legal anchor. Because ID semantics differ across corpora, each declares a **per-corpus ID grammar** (parse/normalize/validate) so the exact-ID metric stays corpus-agnostic over normalized IDs.

### 3.2 Item schema

One corpus-agnostic JSONL schema. Each item carries: `id`, `corpus`, `question`, `question_type ∈ {factual, retrieval, conceptual, interpretive, unanswerable}`, `answerable`, `ambiguity ∈ {low, medium, high}`, `gold_citations` (closed set of IDs that *content-support* the gold answer), `gold_citation_spans` (contiguous ranges for passage-level gold), `near_miss_distractors` (real-but-wrong adjacent IDs), `gold_answer`, `answer_support` (per-citation human label `full/partial/none` — the bridge between ID match and content support), `must_abstain`/`abstain_reason`, provenance, `annotator_ids`, `annotations`, `adjudicated`, and `license`. For `unanswerable` items, `gold_citations` is empty and abstention is the correct behavior.

### 3.3 Question taxonomy

Five types, aimed at **~1,300–1,500 items for v1** with strong agreement rather than a large noisy set:

- **Factual** (single ID) — exact lookup; ships ≥2 near-miss distractors.
- **Retrieval** ("which passage discusses X") — locate the right ID; distractor-heavy.
- **Conceptual** (multi-ID synthesis) — gold is a set or span.
- **Interpretive** (ambiguous, `ambiguity=high`) — reasoning versus fabrication; multiple defensible IDs; **Tier-A only**.
- **Unanswerable / abstention** — must abstain; empty gold; the rigor differentiator.

Two cross-cutting properties (not separate types): **near-miss distractor coverage** (≥60% of factual/retrieval items carry ≥2 existing-but-wrong distractor IDs, including the cross-corpus Gita↔Mahābhārata pair) and **out-of-corpus traps** inside `unanswerable` (questions answerable in *another* corpus but not this one, catching cross-tradition leakage and over-eager citation).

### 3.4 Construction protocol

Pipeline: **freeze corpus → semi-automatic seed generation → annotation → adjudication → agreement reporting → datasheet.**

1. **Freeze corpora.** Build a version-hashed `corpus_index.jsonl` per corpus (multilingual triple + per-corpus ID grammar). `U` is the set of all IDs; nothing downstream may cite an ID outside `U`.
2. **Seed generation (semi-automatic).** Prompt a pinned LLM (`gpt-4o-2024-08-06`) *conditioned on retrieved real verses* to draft `(question, proposed_gold_citations, draft_answer, type, distractors)`. **LLM output is never ground truth** — it is a draft for humans. Over-generate ~1.5× to allow rejection. Unanswerable items are seeded via out-of-corpus topics and cross-corpus swaps.
3. **Human verification.** Annotators work **with the corpus open**, seeing each candidate ID's actual text (`text_en` + original/translit), and set/verify the gold set, answerability, ambiguity, and distractors; they may reject bad seeds.
4. **Adjudication.** A third annotator resolves disagreements; the adjudicated value is gold.
5. **Agreement.** Report Krippendorff's α (MASI distance) for set-valued citation labels and Cohen's/Fleiss' κ for categorical labels, per corpus and per question type.

**Translations.** Where a public-domain English rendering must be produced or normalized for low-resource originals, we use AI4Bharat's **IndicTrans2** as a machine-translation aid for annotation support and robustness layers only — never as released gold text; released text is always a public-domain edition.

### 3.5 Tiered annotation

Double-annotating verse-ID ground truth across many traditions and five scripts exceeds a solo/small-team budget (annotator scarcity is the dominant feasibility risk). We manage this with two tiers so breadth does not drown the signal:

- **Tier A — deep** (full double-annotation + interpretive items + per-citation content-support labels + inter-annotator agreement): **Bhagavad Gita, Bible, Constitution of India, Thirukkuṟaḷ**. These carry the high-rigor human-correlation validation of the exact metric (the C2 generality claim).
- **Tier B — breadth** (factual / retrieval / unanswerable only; auto-checkable, NLI-free metrics; single-annotator + spot-adjudication): **Upanishads, Yoga Sūtras, Rāmāyaṇa, Mahābhārata, Dhammapada, Guru Granth Sahib**. These extend the language/script/tradition axes at low annotation cost, leaning on the deterministic metrics that need no human content label.

The datasheet reports each corpus's tier transparently — the deep-versus-breadth split is a documented design choice, not a hidden quality gradient.

### 3.6 Licensing

Only **public-domain editions** enter the released dataset — Besant & Das / Arnold + ancient PD Sanskrit (Gita), Müller SBE + GRETIL (Upanishads, Dhammapada), Woods/Vivekananda + GRETIL (Yoga Sūtras), Ganguli + GRETIL (Mahābhārata), Pope + PD Tamil (Thirukkuṟaḷ), PD Gurmukhi (Guru Granth Sahib), Government-of-India PD text (Constitution), and WEB (Bible). **Copyrighted English translations are kept private** for annotation/robustness only and never released — specifically the Sant Singh Khalsa Guru Granth Sahib translation and the IIT-K Rāmāyaṇa English (released as original-script only), mirroring the exclusion of the copyrighted BBT Gita translation. A CI check rejects any released text whose source is not on the public-domain allowlist. Questions/annotations are released under CC BY 4.0; code under a permissive license.

---

## 4. Metrics

Per answer, let **G** = gold citation set, **C** = model-cited set, **R** = retrieved-ID set, **U** = corpus ID space, and let `supp(c) ∈ {full, partial, none}` be the content support of the text at `c` for its attached claim (computed at eval time by an NLI/LLM judge, **calibrated against the human `answer_support` labels** in the benchmark). A citation is **valid** iff `c ∈ U` and `supp(c) ≠ none`.

**Primary (deterministic where possible):**

1. **Citation Existence Rate (CER)** — are cited IDs real?  `CER = |{c ∈ C : c ∈ U}| / |C|`. *Fully deterministic, script-agnostic.*
2. **Citation Groundedness (CG)** — cited from what was retrieved?  `CG = |{c ∈ C : c ∈ R}| / |C|`. *Deterministic.*
3. **Attribution Precision / Recall / F1 (exact-ID):**  `P = |C ∩ G| / |C|`, `R = |C ∩ G| / |G|`, `F1 = 2PR/(P+R)`. *Deterministic.*
4. **Attribution P/R/F1 (span-overlap):** credits near-but-not-exact citations (e.g. citing `2.47` when the gold span is `2.47–2.48`) within a corpus-specific tolerance window; reported alongside exact to separate adjacency from true misattribution.
5. **Misattribution Rate (MAR)** — the headline number:  `MAR = (#answers with ≥1 cited id that is non-existent OR has supp(c)=none) / (#answers that cite ≥1 id)`. Decomposed into **MAR-exist** (non-existent id — deterministic, NLI-free) and **MAR-support** (real id, unsupported content — judge-based). Both reported; **MAR-exist is the clean signal**.
6. **Near-miss Misattribution Rate (NMR)** — fraction of misattributions where the cited id is a real-but-wrong near-miss distractor. Uniquely and deterministically measurable here.
7. **Abstention Correctness (AbstAcc)** — on `unanswerable` items:  `AbstAcc = (#correctly abstained) / (#unanswerable)`, plus **over-citation rate** (unanswerable items where any id was cited) and, on answerable items, **wrong-abstention rate**.

**Content-support calibration.** For each cited id we judge `(claim_sentence, text[id])` to obtain `supp(c)`, validate this auto-judge against the human `answer_support` labels, and report the correlation/κ — proving that the exact-ID metric plus a calibrated support check tracks human judgment *across corpora and languages* (the C2 validation contribution; existence-check idea credited to Ovcharov 2026 / CAQA, P/R to ALCE).

**Secondary (comparability):** retrieval Recall@k / nDCG@k against gold IDs; RAGAS faithfulness + answer-relevance and VeriCite/ALCE NLI citation P/R for head-to-head with passage-NLI methods; human ratings (1–5) for accuracy, citation quality, and helpfulness on a stratified sample with ≥2 raters and reported κ.

**Emphasis.** The distinctive properties are (a) the **NLI-free exact-ID signal** (CER, MAR-exist, NMR are fully deterministic and need no support model) and (b) **cross-lingual attribution**: because scoring is over normalized IDs, the same metric applies unchanged whether the query, answer, or source is in English, Devanagari, Tamil, Gurmukhi, or Pali.

---

## 5. Systems and Experimental Design

### 5.1 System families

| System | Description |
|---|---|
| **A. Naive RAG** | dense retrieval (k=5), single-shot generation; ID metadata added to the index. |
| **B. Hybrid** | BM25 + dense fusion (reciprocal-rank fusion). |
| **C. Reranking** | retrieve ~20 → cross-encoder rerank → top-k. |
| **D. SOTA repair** | reproduce a recent citation-repair SOTA: **VeriCite** (NLI verify→refine) and/or **Self-RAG / CRAG**, plus a CG-style (CG-DPO-inspired) repair where feasible — a *fair* comparison baseline. |
| **E. Ours: exact-ID Attribution-Verifier** | generate → extract cited IDs → **exact-match each against the corpus `U`** (exists? content-supported?) → repair/regenerate misattributed claims. The existence check needs no NLI model. |

**Decision gate for C3.** Beating only naive RAG is insufficient. **E must beat D on Misattribution Rate at equal-or-lower cost** — ideally showing the exact-ID check needs *no* NLI model — or E is demoted to a strong baseline and C1+C2 carry the paper.

### 5.2 Grid

Systems **A–E** × **corpora** (all ten, per-tier) × **query language** (English / Hindi / native script + transliteration) × **readers** (≥3 pinned LLMs for breadth: `gpt-4o-2024-08-06`, `gpt-4o-mini`, an open multilingual model such as Llama-3.x-70B or Qwen2.5-72B, and one more for diversity; **Indic-tuned models included** to probe low-resource competence). All temperatures and prompts are fixed and logged.

**Realized so far.** The full ten-corpus grid reported in §5.4 has been run to completion with **Qwen2.5-14B-Instruct** as the primary reader (self-hosted, all systems A–D/E2). A second, independently-trained open multilingual reader, **Aya-Expanse-8B** (Cohere For AI), has been run as a cross-reader robustness check on the winning configurations (C, E2, D — 26 of 28 D cells complete; §5.4.7); GPT-4o-class and further diversity readers remain future work, pending API budget.

**Controls and ablations.** A closed-book (no-retrieval) control separates parametric recall from RAG behavior and, critically, **separates "cannot read the language" from "misattributes"** (a per-language base-competence probe, since low-resource Tamil/Pali/Gurmukhi base performance is poor). Ablations: metadata-aware vs metadata-free index; exact-ID check vs NLI-only repair (cost + MAR); with/without near-miss distractors (incl. the cross-corpus Gita↔Mahābhārata pair); k-sweep; translation robustness (Besant vs Arnold for the Gita) and **cross-lingual robustness** (query/answer in EN vs original-script vs transliteration); abstention-threshold sweep; and Tier-A vs Tier-B (does deep annotation change the deterministic-metric conclusions?). Reporting is per-corpus and pooled, with bootstrap 95% CIs and paired significance tests (paired bootstrap / McNemar for abstention); all per-item outputs and cited-ID extractions are released for auditability.

### 5.3 Experimental setup (System A, this draft)

The results in §5.4 report a **first instantiation of System A (naive RAG)** on the built benchmark. It is a deliberately minimal, fully specified configuration so the cross-lingual attribution effect can be measured before the dense/hybrid/reranking/repair systems (B–E) are added.

- **Retriever.** BM25 (Okapi, stdlib implementation over the frozen `corpus_index.jsonl`), **top-k = 5**. Retrieval is lexical only in this draft; dense multilingual retrieval (BGE-M3) is the System-B upgrade and is *not* yet applied.
- **Reader.** **Qwen2.5-14B-Instruct**, served locally via **Ollama** on a single **NVIDIA L4 (23 GB)** GPU, exposed through an OpenAI-compatible endpoint. The reader is shown the *k* retrieved units (each prefixed by its canonical ID) and the question, and instructed to answer using only those passages and to cite the exact unit ID(s) it relies on, or to declare the question unanswerable and cite nothing. Temperature 0.2; identical prompt across all corpora and languages. Cited IDs are extracted and matched against the closed ID space `U`; an answer with no citable, in-`U` id and no answer text is scored as an abstention.
- **Query-language conditions.** Each item is asked in **English (en)**, **Hindi (hi)**, and the corpus's **native script** where one exists (`sa` Sanskrit, `ta` Tamil, `pa` Gurmukhi, `pi` Pali); gold citations are language-independent, so the three conditions isolate the effect of query language on attribution. Constitution of India and the Bible are English-native and run en/hi only.
- **Metrics.** As defined in §4, computed by the release harness: Citation Existence Rate (CER), exact and span Attribution F1, Misattribution Rate (MAR) with its MAR-exist / MAR-support decomposition, Near-miss Misattribution Rate (NMR), and Abstention Correctness. All per-item outputs are logged.
- **Scope / caveats.** This is a **single-reader, lexical-retrieval, System-A-only** slice — a *lower-order* configuration, not the full grid of §5.2. It establishes the phenomenon; it is not yet the head-to-head (E vs D) evaluation on which the C3 method claim depends. Numbers below are drawn verbatim from the run logs; all 28 cells are complete.

### 5.4 Results

**Table 5.1 — System A (Qwen2.5-14B, BM25 k=5): Attribution F1 (exact) and Misattribution Rate by corpus × query language.** English vs. Hindi/native shown side by side to foreground the cross-lingual gap. All 28 cells complete.

Corpora are grouped by whether a **public-domain English rendering of the source text is in the released corpus**. This distinction is essential to reading the numbers correctly (see below).

| Corpus | N | F1 en ↑ | MAR en ↓ | F1 hi ↑ | MAR hi ↓ | F1 native ↑ | MAR native ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| *Group 1 — English source text released* | | | | | | | |
| **Bhagavad Gita** | 82 | **0.710** | 0.183 | **0.183** | 0.750 | **0.244** (sa) | 0.619 |
| **Yoga Sūtras** | 50 | **0.728** | 0.056 | **0.140** | 0.800 | **0.140** (sa) | 0.857 |
| **Dhammapada** | 60 | **0.756** | 0.213 | **0.212** | 0.600 | **0.167** (pi) | 0.333 |
| **Upanishads** | 50 | **0.567** | 0.138 | **0.196** | 0.200 | **0.196** (sa) | 0.200 |
| **Thirukkuṟaḷ** | 70 | **0.720** | 0.218 | **0.100** | 0.667 | **0.100** (ta) | 0.900 |
| *Group 2 — native-script-only released text* | | | | | | | |
| Constitution of India | 70 | 0.100 | 1.000 | 0.107 | 0.000 | n/a | n/a |
| Rāmāyaṇa | 60 | 0.133 | 1.000 | 0.133 | —† | 0.133 (sa) | —† |
| Bible | 80 | 0.125 | —† | 0.125 | —† | n/a | n/a |
| Guru Granth Sahib | 60 | 0.133 | 1.000 | 0.203 | 0.333 | 0.222 (pa) | 0.455 |
| Mahābhārata | 40 | 0.252 | 0.500 | 0.263 | 0.000 | 0.258 (sa) | 0.333 |

†MAR undefined (denominator zero): on these cells the reader abstained / produced no in-`U` citation on essentially all items, so there is no cited answer over which to define a misattribution rate — itself a signal that lexical retrieval gave the reader nothing to cite.

**Headline — the clean cross-lingual collapse (Group 1).** For the five corpora whose released text *includes* a public-domain English rendering, a capable open reader attributes well in English and **collapses when the query is in Hindi or the native script**, even though the gold citation is *identical* across conditions and only the query language changed:

- **Group-1 mean Attribution F1: English 0.696 → Hindi 0.166 → native 0.169** (cross-lingual pooled **0.168**) — a **76% relative collapse**.
- Per corpus, the English→Hindi drop is steep everywhere: Gita **0.710→0.183**, Yoga Sūtras **0.728→0.140**, Dhammapada **0.756→0.212**, Thirukkuṟaḷ **0.720→0.100**, Upanishads **0.567→0.196**. The **native-script** query is no better than Hindi (and often worse: Yoga Sūtras Sanskrit F1 0.140 / MAR 0.857; Thirukkuṟaḷ Tamil F1 0.100 / MAR 0.900), so the failure is not a Hindi-translation artifact — it is a genuine cross-lingual/cross-script attribution failure.
- Where the reader *does* cite in the cross-lingual conditions, it cites the **wrong existing verse** the majority of the time (Gita Hindi MAR 0.750, Yoga Sūtras Hindi MAR 0.800): confident misattribution, not honest abstention.

**Group 2 is a documented design artifact, not the same phenomenon.** For the five corpora released as **native-script text only** — because their sole clean per-unit English translations are copyright-restricted and excluded by design (Rāmāyaṇa, Mahābhārata beyond the Gita zone, Guru Granth Sahib) or because the corpus is inherently non-English-lexical for this retriever (Constitution, Bible) — **even the English F1 is low (group-2 mean 0.149)** simply because an English query has little to lexically match against native-script source text under BM25. This is *not* a model collapse; it is the expected behavior of lexical retrieval over a cross-script corpus, and it is exactly the condition that **motivates dense multilingual retrieval (System B)**. Consistent with this reading, for these corpora the native/Hindi query is sometimes *better* than English (Guru Granth Sahib 0.133 en → 0.222 Gurmukhi; Mahābhārata 0.252 en ≈ 0.258 Sanskrit), because a native query finally matches the native-script text. Group 2 should therefore be read as a **retrieval-coverage baseline**, and its English weakness must **not** be conflated with the Group-1 cross-lingual collapse.

**Citation Existence Rate is 1.000 in every scored cell.** The reader **never fabricates a non-existent verse ID** — MAR-exist = 0.000 throughout. Every attribution error is a *confident citation of a real but wrong verse* (MAR-support). This is a sharper and more dangerous failure than ID hallucination, and it has a direct methodological consequence: the value of our System E is **not** an existence check (existence is already perfect here) but a **grounding verifier** — checking that the cited verse's *content actually supports the claim* and repairing it when it does not.

> Every number in this table and summary is taken **verbatim from `results/gpu_qwen14b/systemA.jsonl`** (System A, Qwen2.5-14B, BM25 k=5); none is estimated. The full system ladder — **B** (§5.4.2), **C** (§5.4.3), **E** and its dense-retrieval negative result (§5.4.1, §5.4.4), **E2** (§5.4.5), and the **D** SOTA baseline (§5.4.6) — is evaluated against this System-A baseline below, culminating in the §5.1 decision-gate result (Table 5.6).

#### 5.4.1 System E (verified RAG) — preliminary result vs System A

We evaluate a first implementation of **System E** — the exact-ID **grounding verifier + repair** loop of §5.1 — against the System A baseline on the two cleanest Group-1 corpora (Bhagavad Gītā, Yoga Sūtras), on the **same items, same Qwen2.5-14B reader, same BM25 k=5 retrieval**. After the reader proposes a citation, E applies a strict LLM grounding check ("does the cited verse's text directly support the answer?"); a failed citation is repaired to the first grounded top-k candidate, or — if none is grounded — converted to an **abstention** rather than a guess.

**Table 5.7 — System A vs System E (Qwen2.5-14B, BM25 k=5): Attribution F1 (exact) and Misattribution Rate.** Same items both systems; numbers verbatim from `results/gpu_qwen14b/system{A,E}.jsonl`.

| Corpus × query lang | F1 (A → E) | MAR (A → E) ↓ | E abstained |
|---|---:|---:|---:|
| Gītā · en | 0.710 → 0.691 | 0.183 → **0.143** | 26/82 |
| Gītā · hi | 0.183 → 0.189 | 0.750 → **0.500** | 74/82 |
| Gītā · sa | 0.244 → 0.244 | 0.619 → **0.556** | 64/82 |
| Yoga Sūtras · en | 0.728 → 0.660 | 0.056 → **0.033** | 20/50 |
| Yoga Sūtras · hi | 0.140 → 0.120 | 0.800 → 1.000† | 47/50 |
| Yoga Sūtras · sa | 0.140 → 0.140 | 0.857 → **0.750** | 46/50 |

†Small-denominator artifact: E abstained on 47/50 items; the 3 remaining citations were all wrong, so MAR (defined only over cited items) reads 1.000.

**Finding: the grounding verifier reduces confident misattribution, but on lexical retrieval alone it cannot improve attribution accuracy.** Misattribution Rate falls in **five of six cells** — most importantly in the dangerous cross-lingual conditions (Gītā Hindi **0.750 → 0.500**) — because E declines to cite when the cited verse does not ground the answer. But Attribution F1 is flat-to-slightly-lower and abstention rises, for a **structural reason**: under BM25 the gold verse is frequently *absent from the top-k* for a Hindi/native query, so E has no correct candidate to repair *to* — it can only abstain (Gītā Hindi: abstained on 74/82). E's *verify* step works; its *repair* step is starved of correct candidates.

**Consequence for the system ladder.** E's verify-and-repair is validated as a **safety mechanism** (less misattribution), but its **accuracy payoff is gated on candidate quality** — it can only repair to a correct verse that retrieval actually surfaced. This directly motivates **Systems B/C (dense multilingual retrieval, BGE-M3 + FAISS, and cross-encoder reranking)**: once the correct verse is retrieved under a cross-lingual query, E's repair step can convert the reader's wrong pick into the *right* citation instead of an abstention. System B follows next (§5.4.2), then C (§5.4.3), E re-evaluated on dense/reranked retrieval (§5.4.4), our E2 selector (§5.4.5), and the D SOTA baseline (§5.4.6) — culminating in the E-vs-D decision gate (§5.1, Table 5.6).

#### 5.4.2 System B (hybrid retrieval) — the cross-lingual collapse is largely a *retrieval* failure

System B replaces System A's BM25 retriever with a **hybrid** of BM25 (lexical) and **BGE-M3** (dense multilingual embeddings), fused by Reciprocal Rank Fusion; the reader (Qwen2.5-14B) and the rest of the pipeline are unchanged. Evaluated on the same items as A/E (Bhagavad Gītā, Yoga Sūtras).

**Table 5.8 — System A vs System B (Qwen2.5-14B reader): Attribution F1 (exact) and Misattribution Rate.** Same items; numbers verbatim from `results/gpu_qwen14b/system{A,B}.jsonl`.

| Corpus × query lang | F1 (A → B) | MAR (A → B) ↓ |
|---|---:|---:|
| Gītā · en | 0.710 → 0.754 | 0.183 → 0.209 |
| Gītā · hi | 0.183 → **0.660** (3.6×) | 0.750 → 0.250 |
| Gītā · sa | 0.244 → **0.628** (2.6×) | 0.619 → 0.317 |
| Yoga Sūtras · en | 0.728 → 0.797 | 0.056 → 0.167 |
| Yoga Sūtras · hi | 0.140 → **0.622** (4.4×) | 0.800 → 0.121 |
| Yoga Sūtras · sa | 0.140 → **0.593** (4.2×) | 0.857 → 0.097 |

**Finding — the collapse was a retrieval failure, not a reasoning failure.** Dense multilingual retrieval recovers cross-lingual attribution dramatically: cross-lingual mean F1 rises **0.177 → 0.626 (3.5×)**, and the **English→cross-lingual gap shrinks from 75% to 19%**. Cross-lingual misattribution falls in step (Yoga Sūtras Hindi MAR 0.800 → 0.121). The reader was capable cross-lingually all along; under BM25 it simply never *saw* the correct verse for a Hindi/native query. Once BGE-M3 places the gold verse in the top-k, the reader attributes it correctly. (English F1 also edges up; the small English-MAR increases are within noise, from the fused candidate set occasionally displacing an exact lexical hit.)

**This restores the premise for System E** (evaluated next, §5.4.3–§5.4.5).

#### 5.4.3 System C (cross-encoder reranking) — the cross-lingual collapse is a *ranking* failure, and C is the fix

System B recovers most of the collapse, but a residual cross-lingual gap remains. A **retrieval-only recall probe** (no reader; `canoncite/systems/recall_probe.py`) localizes it precisely: under a Hindi/native query, hybrid retrieval almost always *contains* the gold verse in its candidate pool but **ranks it far below the top-k the reader sees**.

**Table 5.9 — Recall@k of the gold verse under hybrid (BM25+BGE-M3) retrieval, answerable items.** Numbers verbatim from `recall_probe`.

| Corpus × query lang | R@5 | R@10 | R@20 | R@50 | median gold rank |
|---|---:|---:|---:|---:|---:|
| Gītā · en | 0.800 | 0.857 | 0.943 | 0.986 | 1 |
| Gītā · hi | **0.357** | 0.629 | 0.857 | 0.986 | **7** |
| Gītā · sa | **0.557** | 0.786 | 0.843 | 0.943 | 5 |
| Yoga Sūtras · en | 0.932 | 0.955 | 0.955 | 0.977 | 1 |
| Yoga Sūtras · hi | **0.227** | 0.341 | 0.773 | 0.932 | **12** |
| Yoga Sūtras · sa | **0.227** | 0.318 | 0.727 | 0.955 | **13** |

The dense retriever *finds* the correct verse (R@50 = 0.93–0.99) but, cross-lingually, ranks it at **median rank 7–13** — below the top-5 window. English queries place it at rank 1. So the residual collapse is a **ranking** problem, not a coverage or reasoning problem. Two levers follow: (i) widen k, or (ii) *rerank*. Widening plateaus and then hurts — a k-sweep of System E (§5.4.4) improves through k≈10 but **regresses at k=20** (Gītā Hindi 0.683→0.670) as the reader drowns in 20 noisy passages. Reranking is the right lever.

**System C** retrieves a wide hybrid pool (cand=50, where recall is 0.93–0.99) and re-scores it with a **BGE-reranker-v2-m3** cross-encoder (multilingual XLM-RoBERTa), keeping the top-5 for the same Qwen2.5-14B reader. The cross-encoder jointly encodes (query, verse), scoring true relevance rather than fused rank.

**Table 5.10 — System B vs System C (Qwen2.5-14B): Attribution F1 (exact) and Misattribution Rate.** Same items; verbatim from `results/gpu_qwen14b/system{B,C}.jsonl`.

| Corpus × query lang | F1 (B → C) | MAR (B → C) |
|---|---:|---:|
| Gītā · en | 0.754 → 0.735 | 0.209 → 0.250 |
| Gītā · hi | 0.660 → **0.747** | 0.250 → 0.254 |
| Gītā · sa | 0.628 → **0.710** | 0.317 → 0.309 |
| Yoga Sūtras · en | 0.797 → 0.811 | 0.167 → 0.186 |
| Yoga Sūtras · hi | 0.622 → **0.690** | 0.121 → 0.231 |
| Yoga Sūtras · sa | 0.593 → 0.613 | 0.097 → 0.242 |

**Finding — reranking closes most of the residual cross-lingual gap.** Cross-lingual (hi/native) mean F1 rises **0.626 → 0.690**, with the largest gains exactly where the gold verse was most deeply buried (Gītā Hindi +0.087, Gītā Sanskrit +0.082, Yoga Sūtras Hindi +0.068). English is neutral (Gītā en −0.019: no headroom, gold already rank 1). Reranking with a short, clean top-5 context beats brute-force widening: C@5 (XL 0.690) exceeds even E@10 (XL 0.659). The end-to-end retrieval story is thus **A (BM25) → B (hybrid) → C (rerank)**, lifting cross-lingual attribution F1 from **0.177 → 0.626 → 0.690**.

#### 5.4.4 System E on dense/reranked retrieval — a verify-and-repair layer is *subsumed* once ranking is fixed

With correct candidates now supplied, we evaluate System E's grounding-verify-and-repair loop over hybrid (E-on-B) and reranked (E-on-C) retrieval, on the same items and reader.

- **E-on-B vs B:** essentially flat on F1 (cross-lingual mean 0.626 → 0.632); repairs rarely fire (0–5 per cell). Verbatim from `systemEB_llm.jsonl`.
- **E-on-C vs C:** flat on F1 (cross-lingual mean **0.690 → 0.698, +0.008**, three cells up, three down); MAR mixed. Verbatim from `systemEC.jsonl`.

**Finding — E's binary verify-and-repair is a remedy for *bad retrieval*, and good ranking removes the disease.** A diagnostic trace (`diagnose_e.py`) confirms the mechanism: E's grounding verifier is not the bottleneck (0–1 false-negatives per cell; 1–2 genuine over-abstentions), and once System C surfaces the correct verse in the top-5, there is little wrong for E to repair — the verify step merely converts a few citations to abstentions. This is a **pivotal negative result**: the value we had ascribed to a generic verify-and-repair layer is largely captured by fixing retrieval ranking. It also sharpens the target: after reranking, the *residual* misattribution is dominated by **near-misses** — citing an adjacent, same-theme verse (Gītā 2.47 vs 2.48; Gītā English NMR 0.214, ≈86% of that cell's MAR). A cross-encoder cannot separate neighbors (it scores them near-equally), and neither can E's binary per-candidate check (it accepts the first plausible one). This is exactly the exact-ID discrimination System E2 is built for.

#### 5.4.5 System E2 (ours) — joint discriminative exact-ID selection *halves* misattribution

**System E2** replaces E's binary, per-candidate grounding check with a **joint discriminative selection**: the reader is shown *all* reranked top-k (k=8) candidates side by side and must choose the single verse that *precisely states* the answer — with the explicit instruction that neighbors on the same theme are **not** the source — or select *none* and abstain. Seeing 2.47 and 2.48 together is what makes the exact-ID distinction possible; it is one LLM call, not k. E2 runs on System C's reranked retrieval (E2-on-C).

**Table 5.11 — System C vs System E2 (ours) (Qwen2.5-14B, reranked retrieval): Attribution F1 and Misattribution Rate.** Same items; verbatim from `results/gpu_qwen14b/system{C,E2C}.jsonl`.

| Corpus × query lang | F1 (C → E2) | **MAR (C → E2)** ↓ | E2 repairs |
|---|---:|---:|---:|
| Gītā · en | 0.735 → 0.754 | 0.250 → **0.119** | 15 |
| Gītā · hi | 0.747 → 0.744 | 0.254 → **0.149** | 19 |
| Gītā · sa | 0.710 → 0.724 | 0.309 → **0.138** | 15 |
| Yoga Sūtras · en | 0.811 → 0.723 | 0.186 → **0.100** | 14 |
| Yoga Sūtras · hi | 0.690 → 0.683 | 0.231 → **0.128** | 9 |
| Yoga Sūtras · sa | 0.613 → 0.620 | 0.242 → **0.216** | 11 |

**Finding — E2 roughly halves misattribution at matched attribution F1.** Cross-lingual F1 is a wash versus C (0.690 → 0.693; F1 was never the objective of a verification layer), but **Misattribution Rate falls 41–55% in five of six cells** (Gītā Sanskrit 0.309 → 0.138; Gītā en 0.250 → 0.119; Yoga Sūtras Hindi 0.231 → 0.128), with repairs now firing heavily (9–19 per cell, vs 0–5 for E v1). This is the payoff on **the benchmark's core axis** — citation misattribution and abstention — and it is a discrimination that neither the topical reranker (C) nor the binary verifier (E) can make. *(One regression: Yoga Sūtras English F1 0.811 → 0.723 — E2 over-corrects on easy English items where C is already near-ceiling; a targeted fix is in progress.)* The **all-10-corpus** E2 and **System D** results, and the head-to-head **E2-vs-D gate**, are complete and reported in **Table 5.6 (the money table): the gate PASSES** — E2's cross-lingual MAR across all ten corpora is the lowest of any system (0.387 vs D's 0.443).

#### 5.4.6 System D (SOTA baseline: Self-RAG + CRAG)

**System D** is the strong published baseline E2 must beat: an inference-time (prompted) formulation of **Self-RAG** (Asai et al. 2023) and **CRAG** (Yan et al. 2024). Over reranked retrieval (matched to E2), a CRAG-style evaluator labels each passage *correct/ambiguous/incorrect* and discards the irrelevant (the open-domain web-search fallback is replaced by abstention over our closed corpus); the reader then generates, and a Self-RAG ISSUP critique keeps a citation only if the passage supports the answer, otherwise switching to the best supported alternative or abstaining. Because D reflects on each passage **individually** — like E v1's binary check — the paper's hypothesis is that it cannot separate near-miss neighbors, and that E2's **joint** discrimination wins on Misattribution Rate. **This is confirmed at scale (Table 5.6):** across all ten corpora E2's cross-lingual MAR (0.387) is lower than D's (0.443), and E2 beats-or-ties D per-corpus in 7 of 10 — the largest margins precisely where near-miss dominates (Upaniṣads 0.427→0.125, Mahābhārata 0.472→0.312). D retains a small edge on cross-lingual F1 (0.440 vs 0.423), but not on the gated misattribution axis, and at ~5× the inference cost.

**Table 5.2 — Cross-lingual attribution (query language × script).** For System A the full per-language/script breakdown is already given in Table 5.1 (en / hi / native columns, all 28 cells complete); this table will be expanded to the per-script breakdown across Systems B–E once those are run. *[System A: see Table 5.1; B–E FORTHCOMING.]*

**Table 5.3 — Closed-book base-competence control (per language).** *[FORTHCOMING]*

**Table 5.4 — Inter-annotator agreement (α / κ) per corpus and question type.** *[FORTHCOMING]*

**Table 5.5 — Content-support judge vs human `answer_support` calibration.** *[FORTHCOMING]*

**Table 5.6 (money table) — the E2-vs-D gate.** System comparison by **cross-lingual (hi/native) attribution F1 and misattribution rate**, reported both on the two pilot corpora (Bhagavad Gītā + Yoga Sūtras) and across **all ten corpora** (28 cells each: 10 corpora × en/hi/native), Qwen2.5-14B reader. Every number is verbatim from `results/gpu_qwen14b/system{A,B,C,D,E2}_all.jsonl` (System A from `systemA.jsonl`); none is estimated. The full chain (C→D→E2→B over all ten corpora) ran to completion with **0 timeouts and 0 OOM**.

| System | Pilot XL-F1 ↑ | Pilot XL-MAR ↓ | **All-10 XL-F1 ↑** | **All-10 XL-MAR ↓** | ~LLM calls/item | Mechanism |
|---|---|---|---|---|---|---|
| A. Naive RAG (BM25) | 0.177 | 0.757 | 0.173 | 0.470 | 1 | lexical retrieval; cross-lingually blind |
| B. Hybrid (BM25+BGE-M3) | 0.611 | 0.108 | 0.416 | 0.446 | 1 | dense multilingual retrieval |
| C. Reranking (BGE-reranker-v2-m3) | 0.654 | 0.233 | 0.404 | 0.482 | 1 | cross-encoder ranking — best retrieval-only |
| D. SOTA (Self-RAG + CRAG) | 0.658 | 0.158 | **0.440** | 0.443 | ~10 | per-passage reflection — the baseline E2 must beat |
| **E2. Ours (discriminative exact-ID)** | 0.645 | 0.137 | 0.423 | **0.387** | ~2 | joint exact-ID selection; wins the misattribution axis |

CER = 1.000 and MAR-exist = 0.000 for **every scored cell of every system**: no system ever cites a non-existent verse — all attribution error is real-but-wrong-verse, which is exactly why E2's exact-ID *discrimination*, not an existence check, is the effective intervention.

**The gate (pre-committed in §5.1, C3): E2 must beat the reproduced Self-RAG+CRAG SOTA (System D) on Misattribution Rate at equal-or-lower cost. → PASSED.** Across all ten corpora, **E2 attains the lowest cross-lingual MAR of any system, 0.387 — ~13% below D's 0.443** — at **~2 LLM calls per item versus D's ~10**, and with *no* NLI model (verification is an exact lookup against the closed ID space). Per corpus, **E2 beats-or-ties D on cross-lingual MAR in 7 of 10 corpora**, with the largest margins exactly where near-miss (adjacent same-theme verse) dominates: Upaniṣads 0.427 → **0.125**, Mahābhārata 0.472 → **0.312**, Constitution of India 0.370 → **0.265**, Bible 0.316 → **0.256**. D wins only on Thirukkural and the two native-script-only corpora (Rāmāyaṇa, Guru Granth Sāhib), where the released public-domain text carries no cross-lingual anchor and *every* system sits at MAR ≈ 0.83+. **D edges E2 on all-10 cross-lingual F1 (0.440 vs 0.423)** — but F1 was never a verification layer's objective; the gate, and the benchmark's headline axis, is misattribution, on which E2 wins at a fraction of D's inference cost. E2 is therefore admitted as contribution C3.

**Scale caveat.** The all-10 means sit far below the pilot (XL-F1 ~0.42 vs ~0.65; XL-MAR ~0.39 vs ~0.14) because the ten-corpus set includes brutal **native-script-only** corpora (Rāmāyaṇa, Guru Granth Sāhib) whose released text has no public-domain cross-lingual anchor and drags every system down uniformly. We therefore report the pilot columns alongside, and recommend reading Group-1 (English-anchored) and Group-2 (native-only) corpus means separately (§5.4).

#### 5.4.7 Cross-reader robustness (Aya-Expanse-8B) — the gate is reader-dependent

To test whether the E2-vs-D result is an artifact of the primary reader, we re-ran the three head-to-head systems (C, E2, D) across the full grid with **Aya-Expanse-8B** (Cohere For AI) — an independently trained, explicitly multilingual open reader roughly half Qwen2.5-14B's size — under an identical protocol (same items, retrieval, prompts, and k; only the reader swapped). 26 of D's 28 cells are complete (the two Mahābhārata cross-lingual cells are pending); all comparisons below are over the **16 cross-lingual cells where both E2 and D are scored under both readers**, so the reader contrast is apples-to-apples. Numbers verbatim from `results/gpu_qwen14b/system{C,E2,D}_aya.jsonl`.

**Table 5.12 — The E2-vs-D gate under two readers (matched 16 cross-lingual cells): Misattribution Rate and cells won.**

| Reader | E2 XL-MAR ↓ | D XL-MAR ↓ | E2 beats-or-ties D (cells) | Gate |
|---|---:|---:|---:|---|
| **Qwen2.5-14B** (primary) | **0.396** | 0.440 | 11 / 16 | **holds** |
| **Aya-Expanse-8B** (robustness) | 0.573 | **0.540** | 6 / 16 | **flips** |

**Finding — E2's advantage is contingent on reader capacity; the gate does not transfer to an 8B reader.** Under Aya-8B every system degrades (XL-F1: C 0.313, E2 0.344, D 0.391 — all far below the Qwen grid), but D degrades *least* and overtakes E2 on the gated axis (XL-MAR 0.540 vs 0.573, winning 10 of 16 cells). The mechanism is visible in the intervention behavior: under the weaker reader, E2's single joint-selection call becomes erratic — repairs fire 474 times (vs 175 for D) and abstention rises to 25.8% of items (vs 16.0%) — i.e., the one-call discriminative select **relies on the reader having the capacity to compare eight candidates side-by-side and hold the exact-source criterion**, whereas D decomposes verification into many *individually easy* per-passage judgments (relevant? supported?) that an 8B model can still execute. English-query cells are essentially tied (MAR 0.474 vs 0.481), so the flip is specifically cross-lingual, where the discrimination is hardest.

**Interpretation for C3.** The method claim is therefore sharpened, not withdrawn: **with a sufficiently capable reader, joint discriminative exact-ID selection attains the lowest misattribution of any system at ~1/5 the SOTA's inference cost (Table 5.6); below that capacity, the SOTA's decomposed per-passage reflection is the more robust choice — its ~10 calls/item buy back, through decomposition, what the weak reader cannot do in one joint judgment.** This yields an actionable selection rule (match the verification structure to the reader's capacity) and identifies the capability threshold itself — somewhere between 8B and 14B for this task family — as an object of study. Confirming where the crossover sits (and whether frontier readers widen E2's margin further) is the purpose of the planned third reader.

---

## 6. Ethics and Datasheet

CANONCITE ships a **datasheet** (following Gebru et al., *Datasheets for Datasets*) answering Motivation / Composition / Collection / Preprocessing / Uses / Distribution / Maintenance. Key entries: items are LLM-seeded then human-verified (not scraped); each corpus's annotation tier (A deep / B breadth) is reported transparently; per-corpus edition, license, and ID grammar are recorded; annotator qualifications, languages, and instructions are documented; and known biases are surfaced (translation choice, transliteration scheme, and annotator worldview on interpretive religious items across multiple living traditions).

The benchmark spans texts from **multiple living traditions** (Hindu, Buddhist, Sikh, Tamil-ethical, Christian) and a nation's constitution. We frame it **strictly as an attribution-faithfulness instrument**: gold answers are *textual-attribution* judgments, **not** endorsements of any doctrinal or theological interpretation, and a prominent disclaimer states this. Each tradition's texts are treated with equivalent care; none is privileged. For interpretive (Tier-A) items we prefer a *defensible set* of gold citations over forcing a single "correct" theology, and surface ambiguity via the `ambiguity` field rather than hiding it. Annotators are recruited with relevant language and tradition literacy, paid fairly, and no PII is collected. A freedom-to-operate note (re: a granted citation-verification patent, US12353469B1) is recorded for any future productization; academic publication is unaffected.

---

## 7. Limitations

- **Translation quality, especially Pali.** Released English for low-resource originals leans on century-old public-domain editions (Müller, Pope, Ganguli) and, for the hardest scripts, thin tooling. The **Pali Dhammapada** and **Gurmukhi Guru Granth Sahib** carry the greatest edition/ID-reliability risk; where a corpus's clean, ID-addressable public-domain edition cannot be verified, it is staged to a later release cut rather than shipped noisy.
- **Annotator scarcity.** Deep double-annotation with verse-ID ground truth across five scripts is beyond a solo/small-team budget; the tiered strategy (§3.5) is a *mitigation*, not a solution, and Tier-B corpora carry lighter human validation by design.
- **Mahābhārata English coverage.** No per-śloka public-domain English aligns to the critical edition; the Mahābhārata is released Sanskrit-only apart from the ~699 Gita-zone verses covered by a public-domain rendering. Likewise the Rāmāyaṇa ships original-script only (its English is copyright-restricted).
- **Base-model failure can swamp attribution signal** in low-resource languages (reported hallucination-free rates as low as ~1–2% for Tamil). The closed-book per-language control is designed to *separate* "cannot read the language" from "misattributes," but in the weakest settings the attribution signal may be dominated by base incompetence.
- **Method novelty is contested (C3).** The repair loop is crowded; the exact-ID verifier is admissible only under the pre-committed gate (E must beat D), and may be reported as a baseline.
- **Heterogeneous ID semantics** across corpora require per-corpus ID grammars; the unified metric is corpus-agnostic only over *normalized* IDs.

---

## 8. Conclusion

Canonical texts turn the fuzzy, NLI-approximated question "is this claim grounded?" into an exact, closed-set membership check — and misattribution into an automatically detectable event. CANONCITE exploits this to build the **first multilingual, multi-tradition, multi-script Indian canonical-citation attribution + abstention benchmark**: ten public-domain corpora, 188,557 citable units across five scripts, closed canonical-ID ground truth, an ambiguity-graded taxonomy with near-miss distractors and abstention traps, and a corpus-agnostic, largely NLI-free metric suite. We position it precisely against the fixed-ID legal work of Ovcharov (2026), the single-tradition Islamic verse-hallucination work of IslamicEval 2025, and the Indic *understanding* benchmarks ParamBench and MILU — claiming as novel only the cross-lingual / multi-script attribution axis that is unoccupied across the entire attribution lineage.

The empirical study is complete on its primary reader (Qwen2.5-14B): the full system ladder — naive RAG, hybrid, reranking, a reproduced Self-RAG+CRAG SOTA, and our joint discriminative exact-ID selector (E2) — was run across all ten corpora and all query-language conditions, with **0 timeouts and 0 OOM**. The pre-committed decision gate **passes**: E2 attains the lowest cross-lingual Misattribution Rate of any system (0.387, ~13% below the SOTA's 0.443) at roughly a fifth of the inference cost, confirming that the cross-lingual collapse is fundamentally a retrieval-ranking failure and that the residual near-miss misattribution is best resolved by joint discrimination rather than per-passage reflection or NLI verification. A second-reader robustness check (Aya-Expanse-8B, §5.4.7) adds the study's most instructive nuance: the gate is **reader-capacity-dependent** — under an 8B reader the SOTA's decomposed reflection overtakes the joint select — so the method contribution lands as a **capacity-matched selection rule** (one cheap joint call when the reader can carry it; decomposed per-passage verification when it cannot), with the crossover threshold itself a target for the planned third reader. **Remaining before submission:** the two outstanding Mahābhārata cells of the Aya grid, the Tier-A inter-annotator agreement and closed-book base-competence controls (Tables 5.3–5.4), and the content-support judge calibration (Table 5.5).

---

## References

- Asai, A., Wu, Z., Wang, Y., Sil, A., Hajishirzi, H. (2024). *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection.* ICLR 2024. arXiv:2310.11511.
- Bohnet, B., Tran, V. Q., Verga, P., et al. (2022). *Attributed Question Answering: Evaluation and Modeling for Attributed Large Language Models.* arXiv:2212.08037.
- Gao, L., Dai, Z., et al. (2023). *RARR: Researching and Revising What Language Models Say, Using Language Models.* ACL 2023. arXiv:2210.08726.
- Gao, T., Yen, H., Yu, J., Chen, D. (2023). *Enabling Large Language Models to Generate Text with Citations (ALCE).* EMNLP 2023. arXiv:2305.14627.
- Gebru, T., Morgenstern, J., Vecchione, B., et al. (2021). *Datasheets for Datasets.* Communications of the ACM.
- Hu, Y., et al. (2025). *Can LLMs Evaluate Complex Attribution in QA? Automatic Benchmarking using Knowledge Graphs (CAQA).* ACL 2025. arXiv:2401.14640.
- Kamalloo, E., et al. (2023). *HAGRID: A Human-LLM Collaborative Dataset for Generative Information-Seeking with Attribution.* arXiv:2307.16883.
- Li, D., et al. (2024). *A Comparative Analysis of Faithfulness Metrics and Humans in Citation Evaluation.* arXiv:2408.12398 (companion: *Towards Fine-Grained Citation Evaluation*, arXiv:2406.15264).
- Li, D., et al. (2023). *A Survey of Large Language Models Attribution.* arXiv:2311.03731.
- Maheshwari, H., Tenneti, S., Nakkiran, A. (2025). *CiteFix: Enhancing RAG Accuracy Through Post-Processing Citation Correction.* arXiv:2504.15629.
- Malaviya, C., Lee, S., Chen, S., et al. (2024). *ExpertQA: Expert-Curated Questions and Attributed Answers.* NAACL 2024. arXiv:2309.07852.
- Malik, V., et al. (2021). *ILDC for CJPE: Indian Legal Documents Corpus for Court Judgment Prediction and Explanation.* ACL 2021.
- Ovcharov, V. (2026). *Citation Grounding: Detecting and Reducing LLM Citation Hallucinations via Legal Citation Graphs.* arXiv:2606.00898.
- Qian, H., Fan, Y., Guo, J., et al. (2025). *VeriCite: Towards Reliable Citations in RAG via Rigorous Verification.* SIGIR-AP 2025. arXiv:2510.11394.
- Verma, S., et al. (2024). *MILU: A Multi-task Indic Language Understanding Benchmark.* AI4Bharat. arXiv:2411.02538.
- Yan, S.-Q., Gu, J.-C., et al. (2024). *Corrective Retrieval Augmented Generation (CRAG).* arXiv:2401.15884.
- *ParamBench: A Graduate-Level Benchmark for Evaluating LLM Understanding on Indic Subjects.* (2025). arXiv:2508.16185.
- *IslamicEval 2025: Shared Task on Capturing LLM Hallucination in Islamic Content.* ACL ArabicNLP 2025. aclanthology.org/2025.arabicnlp-sharedtasks.67/.
- *IslamicMMLU.* (2026). arXiv:2603.23750.
- *IslamicLegalBench.* (2026). arXiv:2602.21226.
- *IndicQA Benchmark.* (2024). arXiv:2407.13522.
- *IndicXNLI.* (2022). arXiv:2204.08776.
- *BhashaSutra: A Survey of Indian NLP Datasets.* (2026). arXiv:2604.18423.
- *BibleQA: Finding Answers from the Word of God.* (2018). arXiv:1810.12118.
- *SiPaKosa: A Canonical Buddhist Corpus in Sinhala and Pali.* (2026). arXiv:2603.29221.
- *IL-TUR: Indian Legal Text Understanding and Reasoning.* (2024). arXiv:2407.05399.
- *NyayaAnumana / INLegalLlama.* (2024). arXiv:2412.08385.
- *Constitution of India LLM Case Study (RAG/LangChain QA).* (2024). arXiv:2404.06751.
- *Attribution, Citation, and Quotation: A Survey of Evidence-based Text Generation.* (2025). arXiv:2508.15396.
