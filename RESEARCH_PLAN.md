# Research Plan — A Multilingual, Multi-Tradition Canonical-Citation Benchmark for RAG

**Working title:** *CANONCITE: A Multilingual, Multi-Tradition, Multi-Script Benchmark for Canonical-Citation Attribution and Abstention over Indian Canonical Texts (with Cross-Cultural and Legal Anchors)*

**Working benchmark name:** **CANONCITE** (tentative; alt: CiteCanon, ATTRIB-QA)

**Strategy (decided):** **Benchmark-anchored** — the dataset is the contribution; the metric suite and method are supporting. De-risk via arXiv + a workshop, then extend toward a top-tier venue (**NeurIPS Datasets & Benchmarks** track or **ACL resource track**). **Multi-corpus, multilingual from the start.**

**Scope (decided + prior-art-verified, 2026-06-30).** CANONCITE is a **multilingual, multi-tradition, multi-script benchmark for canonical-citation attribution + abstention over Indian canonical texts**, plus a **cross-cultural anchor** (Bible, English) and a **legal anchor** (Constitution of India). It spans **three orthogonal novelty axes**:
> **(1) tradition** — Hindu (Gita, Upanishads, Yoga Sutras, Ramayana, Mahabharata), Buddhist (Dhammapada), Sikh (Guru Granth Sahib), Tamil ethical (Thirukkural), Christian (Bible), and secular-legal (Constitution of India);
> **(2) language / script** — Sanskrit (Devanagari), Pali, Tamil, Gurmukhi, Hindi, English, with transliteration where applicable;
> **(3) domain** — interpretive-religious, narrative-religious, ethical-aphoristic, and prescriptive-legal.
>
> Every corpus carries `text_en` + the original (Sanskrit/Pali/Tamil/Gurmukhi/Hindi) + transliteration where applicable, with a **fixed, closed canonical-ID space** (chapter.verse, pada.sutra, kanda.sarga.shloka, kural-no., Ang+line, Part/Article§clause, book chapter:verse) as exact, NLI-free attribution ground truth.

> **Re-anchoring note (post prior-art review, 2026-06-29; multilingual vetting 2026-06-30).** Two live lit reviews (see `RELATED_WORK.md` and `RELATED_WORK_MULTILINGUAL.md`) constrain the novelty surface. (a) The *idea* "fixed citation IDs enable exact, NLI-free attribution scoring" is **already demonstrated in the legal domain** by Ovcharov 2026 ("Citation Grounding," arXiv:2606.00898), which also ships a metric suite **and** a repair method (CG-DPO) — so we **do not** claim that insight as ours. (b) Scripture-verse misattribution detection+repair **already exists for another tradition** — **IslamicEval 2025** (ACL ArabicNLP; Qur'an Ayah/Hadith) — so we **do not** claim "first religious verse-attribution benchmark." (c) Indic LLM-evaluation benchmarks (**ParamBench**, **MILU**) already cover Hindu scripture/philosophy/law content, but as *MCQ understanding*, not attribution. The verified verdict: the **multilingual / multi-script fixed-ID attribution axis is genuinely unoccupied** and **strengthens** novelty. So **C1 (the benchmark) = NOVEL** (with the cross-lingual axis the freshest contribution); **C2 (metrics) = PARTIAL**; **C3 (method) = PARTIAL/contested**. This plan re-anchors on **C1**, with C2 reframed as *integration + human-correlation validation* and C3 required to *either beat a real SOTA or be explicitly secondary*. See the buildable spec in **`BENCHMARK_DESIGN.md`**.

---

## 1. The gap and why it's publishable

RAG faithfulness/hallucination is usually studied on Wikipedia/news, where "is this grounded?" is fuzzy and must be approximated (NLI, LLM-judge). Canonical texts have a property those settings lack: **answers cite discrete, checkable references** (chapter.verse, surah:ayah, book chapter:verse, article§clause). When a model writes *"as taught in BG 5.18"* but the supporting verse is 2.47, that is a **misattribution** detectable **automatically and exactly** against a fixed citation ID space — no NLI needed.

That property is attractive but, crucially, **is not ours to claim as a new insight** (see §1.1). Our publishable gap is narrower, more defensible, and now sharpened by the multilingual re-framing: **no existing resource measures canonical-citation attribution *across languages, scripts, and traditions* — and the entire attribution lineage (ALCE, CAQA, VeriCite, Citation Grounding) is English- or single-language-centric. A cross-lingual / multi-script fixed-canonical-ID citation-attribution benchmark does not exist anywhere.** Layered on top: no resource mixes Indian religious traditions (Hindu, Buddhist, Sikh, Tamil-ethical) with a cross-cultural (Bible) and a legal (Constitution of India) anchor under one exact metric, and none includes the interpretive and unanswerable/abstention items that stress reasoning-vs-fabrication rather than lookup. That **multilingual, multi-tradition, multi-script, interpretive, abstention-aware** benchmark is the headline contribution (**C1**), and **the cross-lingual/multi-script axis is the freshest, most clearly first-mover part of it**. Indian canonical texts and constitutional law are the cleanest *instruments* for studying attribution that generalizes to every **citation-critical domain** (statutes, clinical guidelines, scientific papers); the contribution is the benchmark and its findings, not the scripture.

### 1.1 Prior-art positioning (read this before claiming anything)

The novelty surface is constrained by **four** lineages we cite **up front**, not as an afterthought. The first two (Indic-understanding and single-tradition verse-misattribution) are the ones the multilingual re-framing must be positioned against precisely.

**(A) Indic LLM-evaluation benchmarks — *understanding / MCQ*, NOT attribution.**
- **ParamBench (arXiv:2508.16185)** — 17K+ **Hindi** graduate-level questions across 21 Indian-studies subjects (history, yoga, philosophy, literature, **law**, music) from a nationwide entrance exam, in MCQ / assertion–reason / sequence / list-matching formats. It is the nearest "Indian scripture knowledge benchmark," but it is **understanding/recall — no verse-ID ground truth, no misattribution metric, no abstention, Hindi-only**.
- **MILU (arXiv:2411.02538; AI4Bharat)** — ~80K MCQ across **11 Indic languages**, 8 domains / 41 subjects incl. **Law & Governance** and **Arts & Humanities** with Indian cultural content. Again **MCQ understanding — no citation-attribution / fixed-ID / abstention** axis (models are weakest exactly in Humanities + Law).
- Reviewers will ask "how is this not another Indic benchmark?" The answer leans on **attribution + fixed verse-ID + misattribution + abstention** (which ParamBench/MILU lack), **not** "Indian scripture knowledge" (which they own).

**(B) Scripture-verse misattribution — already done, in *another* tradition (single-tradition, monolingual).**
- **IslamicEval 2025 (ACL ArabicNLP shared task; aclanthology.org/2025.arabicnlp-sharedtasks.67/)** — Subtask 1 = **hallucination detection + correction of quoted Qur'an Ayahs and Hadiths**; Subtask 2 = grounded Qur'an/Hadith QA. This is the closest existing thing to scripture-verse misattribution detect+repair, **but Arabic/Islamic, single-tradition, not cross-script, not multilingual**. Our *concept* is therefore anticipated in another religion. So **our claim is NOT "first religious verse-attribution"** — it is **"first multilingual, multi-tradition, multi-script Indian canonical-citation attribution + abstention benchmark."**

**(C) The fixed-ID attribution lineage — the *idea* is already taken (in legal), and it is English-only.**
- **Ovcharov 2026, "Citation Grounding" (arXiv:2606.00898)** is the closest metric threat. It builds a fixed statute citation graph from Ukrainian court decisions, defines **Citation Grounding / Citation Precision / Relevance / Temporality** (existence-checking a cited provision against a fixed node set — the same insight as our Citation Existence Rate), **and** ships a repair method (**CG-DPO**) across 7 legal sub-domains. It **scoops the *concept*** behind C2 and C3. What it does **not** do, and what we retain: it is **single-jurisdiction, single-language legal only — not cross-lingual, not cross-tradition, no interpretive/ambiguous items, no unanswerable/abstention taxonomy**, and it uses DPO fine-tuning rather than an inference-time check.
- **CAQA** (Hu et al., ACL 2025; arXiv:2401.14640) uses knowledge-graph structure to make attribution automatically checkable — adjacent idea, different (triple) structure.
- **Indian legal NLP does judgment-prediction/summarization, not constitutional citation attribution.** **IL-TUR** (arXiv:2407.05399), **ILDC** (ACL 2021), and **NyayaAnumana / INLegalLlama** (arXiv:2412.08385) are mature but organized around court-judgment prediction, summarization, and reasoning — **not** Article§clause *citation attribution*. So the **Constitution of India as a fixed-ID citation-attribution legal corpus is open** (and arguably more defensible than the US Constitution: longer, amendment-rich, under-benchmarked for attribution, and on-theme Indian).

**(D) The attribution-benchmark lineage — grounds to *retrieved passages via NLI*, English/single-language.**
- **ALCE** (Gao et al., EMNLP 2023; arXiv:2305.14627) — citation precision/recall via **NLI entailment against retrieved web passages** (the paradigm we adapt, not exact-ID).
- **AttributedQA** (Bohnet et al., 2022; arXiv:2212.08037) — AIS framing; attribution to identified sources judged by human/NLI.
- **ExpertQA** (Malaviya et al., NAACL 2024) — 2,177 expert questions across 32 fields, claim-level attribution to web/passage evidence.
- **HAGRID** (Kamalloo et al., 2023), **CAQA**, and the verify-then-repair methods (**RARR**, **CiteFix**, **VeriCite**, **Self-RAG**, **CRAG**) all ground/repair against **retrieved passages**, *not* a fixed canonical ID space — and all are **English/single-language**.

**Precisely how this work differs:**
1. **Cross-lingual / multi-script fixed-canonical-ID attribution — the freshest, genuinely unoccupied axis.** The entire attribution lineage above is English/single-language; no benchmark scores whether a model cited the correct source ID *across languages and scripts* (Devanagari/Pali/Tamil/Gurmukhi/English). This is the single best reason to adopt the re-framing.
2. **Multi-tradition Indian + cross-cultural + legal** canonical-ID attribution under one exact metric — Hindu × Buddhist × Sikh × Tamil-ethical × Christian × secular-legal — a combination no resource occupies; prior fixed-ID work is single-domain legal, and prior verse-misattribution work is single-tradition Islamic.
3. **Interpretive + unanswerable/abstention taxonomy** with **near-miss citation distractors** — the least-covered axis among competitors, and the one fixed-ID scoring measures uniquely well.
4. A test of the **generality of NLI-free fixed-ID attribution beyond English legal** — we *validate* (not invent) that the exact-ID metric transfers across languages, scripts, and traditions, and *correlate it with human judgment* across corpora.

> ⚠️ We are **not** the first to propose fixed-ID exact attribution scoring (Ovcharov 2026, legal), nor the first to detect/repair wrong scripture-verse citations (IslamicEval 2025, Islamic), nor the first to evaluate LLMs on Indian scripture content (ParamBench/MILU, understanding). Any language claiming those as novel must be removed from drafts. Our first-mover claim is the **multilingual, multi-tradition, multi-script Indian canonical-citation attribution + abstention benchmark**, with the **cross-lingual/multi-script axis as the load-bearing novelty**.

---

## 2. Contributions (claims the paper will make)

Ordered by weight. **C1 is the headline and must carry the paper on its own.**

- **C1 — Benchmark (HEADLINE, NOVEL):** CANONCITE, the first **multilingual, multi-tradition, multi-script canonical-citation** QA set — Indian religious (Gita, Upanishads, Yoga Sutras, Ramayana, Mahabharata, Dhammapada, Thirukkural, Guru Granth Sahib), a cross-cultural anchor (Bible), and a secular-legal anchor (Constitution of India) — with **verse/sutra/Ang/kural/article-section-level attribution ground truth** across Sanskrit/Pali/Tamil/Gurmukhi/Hindi/English, an **interpretive/ambiguity-graded** question taxonomy, and dedicated **unanswerable/abstention** and **near-miss-citation distractor** items. This combination is unoccupied in the prior art (`RELATED_WORK.md` §5, `RELATED_WORK_MULTILINGUAL.md` §5). **The cross-lingual / multi-script axis is the freshest contribution** — it does not exist anywhere in the attribution lineage. *Lead with this.*
- **C2 — Metric suite (PARTIAL — integration + validation, not invention):** a unified, cross-corpus **exact-attribution** metric suite (§4). We **explicitly credit** Ovcharov 2026 / CAQA for the fixed-ID-enables-exact-scoring idea and the ALCE lineage for precision/recall. Our contribution here is (i) **integrating** these into one corpus-agnostic harness and (ii) **validating it against human judgment** (correlation of exact-ID metrics with annotator support ratings) across religious + legal corpora — a generality claim no prior fixed-ID work makes.
- **C3 — Method (PARTIAL/contested — must beat real SOTA or be secondary):** an inference-time **attribution-verification agent** that exact-matches cited IDs against the corpus and repairs misattributions. This loop is **crowded** (CiteFix, VeriCite, RARR, CG-DPO, Self-RAG/CRAG). It is admissible **only if** it **beats a real SOTA** (VeriCite / Self-RAG / CG-style repair) on Misattribution Rate at lower/equal cost, demonstrating the determinism/cost advantage of exact-ID checking over NLI repair. **If it does not, C3 is reported as a strong baseline** and C1+C2 carry the paper.
- **C4 — Findings:** a misattribution **taxonomy** + failure analysis, and the first evidence that misattribution behavior (and any repair) **transfers across languages, scripts, and traditions** — Indian-religious, cross-cultural, and secular-legal canonical corpora — under one exact metric. A key sub-finding: separating "can't read the language" (base-model failure in low-resource Tamil/Pali/Gurmukhi) from "misattributes" (cites the wrong existing ID).

---

## 3. Benchmark design (the anchor)

### 3.1 Corpora (multilingual, multi-tradition from day one; all public-domain editions)

Full v1 roster (ID schemes, public-domain sources, per-corpus feasibility/risk, and the tiered-annotation split) lives in **`BENCHMARK_DESIGN.md` §1**. Summary axes:

| Corpus | Tradition / domain | Language(s) / script | Citation ID space | Tier |
|---|---|---|---|---|
| **Bhagavad Gita** | Hindu / interpretive | Sanskrit (Devanagari) + EN | `chapter.verse` | A (v0) |
| **Upanishads (principal)** | Hindu / interpretive | Sanskrit + EN | `section.khanda.verse` | B |
| **Yoga Sutras of Patanjali** | Hindu / aphoristic | Sanskrit + EN | `pada.sutra` | B |
| **Ramayana (Valmiki)** | Hindu / narrative | Sanskrit + EN | `kanda.sarga.shloka` | B |
| **Mahabharata** | Hindu / narrative | Sanskrit + EN | `parva.adhyaya.shloka` | B (largest; retrieval stress) |
| **Dhammapada** | Buddhist / interpretive | Pali + EN | `chapter.verse` | B |
| **Thirukkural** | Tamil / ethical-aphoristic | Tamil + EN | `kural` (1–1330) | A (clean demonstrator) |
| **Guru Granth Sahib** | Sikh / devotional | Gurmukhi + EN | `ang` + line/shabad | B (hardest) |
| **Constitution of India** | secular-legal | Hindi / EN | `Part/Article §clause` | A (legal anchor) |
| **Bible** | Christian / narrative+law | English | `BOOK chapter:verse` | A (cross-cultural anchor) |

Each corpus carries `text_en` + the original (Sanskrit/Pali/Tamil/Gurmukhi/Hindi) + transliteration where applicable. **v0 = Gita-only** (unchanged); **v1 = the Tier-A deep set + the auto-checkable Tier-B breadth set** (see §3.5 and `BENCHMARK_DESIGN.md` §1/§3). **Constitution of India** replaces the US Constitution as the legal anchor (on-theme Indian, under-benchmarked for attribution — `RELATED_WORK_MULTILINGUAL.md` §4).

> Licensing note: the repo currently ships *Bhagavad-gita As It Is* (Prabhupada/BBT) — **copyrighted**. For any public benchmark, **switch to public-domain translations** (Telang SBE / Arnold for the Gita; Müller SBE, Griffith, Ganguli, Pope, GRETIL originals, WEB, Government-of-India text — see `BENCHMARK_DESIGN.md` §1/§7). Keep BBT only for private experiments, never in the released dataset.

### 3.2 Item schema (corpus-agnostic)
```json
{
  "id": "gita-0001",
  "corpus": "bhagavad_gita",
  "question": "What does the text teach about acting without attachment to results?",
  "question_type": "conceptual",          // factual | retrieval | conceptual | ethical | interpretive
  "gold_citations": ["2.47", "2.48"],     // canonical IDs; may be a set or a span
  "gold_answer": "…",                       // reference answer grounded in gold_citations
  "answerable": true,                        // some items are deliberately unanswerable
  "ambiguity": "low",                       // low | medium | high (interpretive items = high)
  "annotator_ids": ["a1","a2"],
  "adjudicated": true
}
```

### 3.3 Question taxonomy (per corpus, target counts for v1)
- **Factual** lookup (single ID) — 80
- **Verse/section retrieval** ("which passage discusses X") — 80
- **Conceptual** (multi-ID synthesis) — 80
- **Ethical / guidance** (interpretive, multi-ID, may be ambiguous) — 80
- **Unanswerable / out-of-corpus** (must abstain) — 40 (trap items, critical for top-tier rigor)

Per-corpus targets above apply to **Tier-A** corpora; **Tier-B** corpora are smaller (≈100–150 items, factual/retrieval/abstention-weighted, auto-checkable). See §3.5 and `BENCHMARK_DESIGN.md` §3 for the tier-aware count table. (Workshop-grade ≈ 300–500 total; top-tier wants 1k+ with human validation.)

### 3.4 Construction protocol (rigor = the difference)
1. **Verse corpus extraction** → structured `{id, text, sanskrit?, translation, source}` per corpus (Phase 1).
2. **Seed generation** — draft questions semi-automatically (LLM-proposed, ID-grounded) **then human-verify** — never ship LLM-only ground truth.
3. **Double annotation** — ≥2 annotators per item; report **inter-annotator agreement** (Cohen's/Krippendorff's). Adjudicate disagreements.
4. **Negative/trap items** — unanswerable + near-miss citations (e.g., gold 2.47, distractor 5.18) to measure misattribution directly.
5. **Datasheet** (Gebru et al.) + licensing + intended-use + limitations doc.

### 3.5 Feasibility & tiered annotation (the real risk is cost, not novelty)

`RELATED_WORK_MULTILINGUAL.md` §6 is explicit: **the dominant risk of the multilingual re-framing is feasibility — annotator scarcity and uneven text/ID availability — not novelty.** Double-annotating verse-ID ground truth across 8 traditions and 5 scripts is beyond a solo/small-team budget (ParamBench/MILU had AI4Bharat-scale institutional backing). We manage this with a **two-tier annotation strategy** so that breadth does not drown the signal under shallow annotation:

- **Tier A — deep annotation** (full double-annotation + interpretive items + per-citation content-support labels + inter-annotator agreement): **Bhagavad Gita, Bible, Constitution of India, Thirukkural**. These are the clean, license-safe, annotator-reachable corpora that carry the high-rigor claims (human-correlation validation of the exact metric).
- **Tier B — breadth** (factual / retrieval / unanswerable items only; auto-checkable metrics — CER, exact-attribution, MAR-exist, NMR, abstention; single-annotator + spot-adjudication): **Upanishads, Yoga Sutras, Ramayana, Mahabharata, Dhammapada, Guru Granth Sahib**. These extend the language/script/tradition axes at low annotation cost, leaning on the **deterministic, NLI-free** metrics that need no per-citation human support label.

The **datasheet reports each corpus's tier transparently**, so the deep-vs-breadth split is a documented design choice, not a hidden quality gradient. Per-corpus feasibility/risk notes (text+ID+OCR availability, annotator scarcity, ID-scheme heterogeneity) and the **v1-vs-full-release split** are specified in `BENCHMARK_DESIGN.md` §1 and §3. Known bottlenecks: **Guru Granth Sahib** (Gurmukhi tooling early-stage; reliable Ang/line IDs are the constraint) and **Pali Dhammapada** (script/edition availability) are the hardest; **Constitution of India / Bible / Gita / Thirukkural** are clean. Heterogeneous ID semantics (chapter.verse vs Ang.line vs kural-no. vs Part/Article§clause vs pada.sutra) require a **per-corpus ID grammar in the schema** — solvable, but explicit.

---

## 4. Metrics (discrete, verifiable — C2: integrate + validate, do not claim as new)

> **Credit, up front:** the exact-existence-check idea is **Ovcharov 2026** (Citation Precision against a fixed node set) and **CAQA**; the precision/recall paradigm is **ALCE**. We integrate and *validate* these cross-corpus, we do not claim to have invented them. Full definitions/formulas live in `BENCHMARK_DESIGN.md` §5; the summary below is the paper-facing list.

Let gold citations `G`, model-cited `C`, retrieved IDs `R`, corpus ID set `U`.

- **Citation Existence Rate (CER):** `|{c ∈ C : c ∈ U}| / |C|` — are cited IDs real?
- **Citation Groundedness (CG):** `|{c ∈ C : c ∈ R}| / |C|` — cited from what was actually retrieved?
- **Attribution Precision / Recall / F1:** `C` vs `G` (exact ID match; report span-overlap variant too).
- **Misattribution Rate (MAR):** fraction of answers containing ≥1 cited ID that is non-existent **or** unsupported by its content (content check via NLI/LLM-judge as a *secondary* signal).
- **Abstention correctness:** on unanswerable items, did the system abstain?
- **Standard RAG metrics** for comparability: Recall@k / nDCG@k (retrieval), RAGAS faithfulness + answer-relevance, and **human** accuracy/citation-quality (1–5).

The headline number: **MAR reduction** of the proposed method vs baselines, holding answer-relevance constant.

---

## 5. Systems (C3) — grounded in the current repo

Current code = **System A (Naive dense RAG)** baseline: LangChain + `all-MiniLM-L6-v2` → Pinecone cosine k=5, OpenAI completion, Krishna-persona prompt, **no metadata**.

| System | Description | Build effort vs current |
|---|---|---|
| **A. Naive RAG** | dense k=5, current pipeline | reuse (add ID metadata) |
| **B. Hybrid** | BM25 + dense fusion (RRF) | add `rank_bm25` + fusion |
| **C. Reranking** | retrieve 20 → cross-encoder → top-k | add cross-encoder (sentence-transformers) |
| **D. Real SOTA repair** | reproduce a recent citation-repair SOTA: **VeriCite** (NLI verify→refine) and/or **Self-RAG / CRAG**; plus a **CG-style** repair (CG-DPO-inspired) where feasible | new (fair comparison; **required**) |
| **E. Ours: Attribution-Verifier** | generate → extract cited IDs → exact-match each against corpus (exists? content-supported?) → repair/regenerate misattributed claims (LangGraph) | new — secondary contribution |

> **Decision gate for C3:** beating *only* Naive RAG is not enough. **E must beat D** (VeriCite / Self-RAG / CRAG / CG-style) on Misattribution Rate at equal-or-lower cost — ideally showing the exact-ID check needs **no NLI model** — or the method is demoted to a strong baseline and **C1+C2 carry the paper**. Add **CiteFix** and **VeriCite** as method baselines, not just Self-RAG/CRAG.

---

## 6. Reuse map (audit-grounded)
- **Reuse:** PDF/text loading, embedding+Pinecone wiring, LLM call structure, Flask API, frontend (demo).
- **Refactor (critical, blocks everything):** structured **verse/section parsing with canonical-ID metadata** carried into the index — without this there is no benchmark and no attribution metric.
- **Build new:** BM25/hybrid, cross-encoder reranker, Self-RAG/CRAG baseline, the verifier agent (LangGraph), the **evaluation harness** (metrics in §4), benchmark store + loaders, datasheet.
- **Add deps:** `rank_bm25`, `langgraph`, a cross-encoder model, `ragas`/`deepeval` (secondary), `scikit-learn` (agreement stats). Modernize the OpenAI call (`gpt-4o`/`gpt-4o-mini` chat) and pin model versions for reproducibility.

---

## 7. Phased timeline

**Phase 0 — Lit review & novelty check (1–2 wk).** Confirm the gap vs ALCE/ExpertQA/AttributedQA **and** the multilingual constraints (ParamBench/MILU = understanding; IslamicEval 2025 = single-tradition verse-misattribution; Indian legal NLP = judgment prediction); lock the precise novelty statement (multilingual/multi-script attribution); line up an advisor/co-author and **per-language annotator access** (top venues rarely take unaffiliated solo first papers).

**Phase 1 — Foundation (2–3 wk).** Structured corpus parsers with **per-corpus ID grammar** for the Tier-A set (Gita, Bible, Constitution of India, Thirukkural) first, then Tier-B sources (public-domain editions + GRETIL originals); `text_en` + original + transliteration; canonical-ID metadata into the index; benchmark schema + storage; reproducible config.

**Phase 2 — Benchmark v1 (3–4 wk).** Tier-A **double human annotation** + adjudication + interpretive/trap items; Tier-B single-annotator factual/retrieval/abstention items with spot-adjudication; datasheet (reports each corpus's tier). (This is the publishable core.)

**Phase 3 — Systems (3–4 wk).** Implement A–E; the evaluation harness (§4 metrics).

**Phase 4 — Experiments (2–3 wk).** All systems × all corpora × ≥3 LLMs; ablations; human eval; failure taxonomy.

**Phase 5 — Write & derisk (3–4 wk).** Paper draft → **arXiv** → **workshop** submission for feedback.

**Phase 6 — Extend to top-tier.** Add corpora/scale, strengthen baselines + human study per workshop feedback → NeurIPS D&B / ACL.

---

## 8. Risks & mitigations
- **Metric/idea scooped by Ovcharov 2026 (legal fixed-ID + repair)** → *acknowledged, not a blocker.* Cite up front (§1.1); re-anchor on the **multilingual/multi-tradition benchmark + interpretive/abstention design** (C1) and **human-correlation validation** of the exact metric across languages, neither of which the legal paper does. Never claim the NLI-free-exact insight as ours.
- **"Just another Indic benchmark" (ParamBench/MILU)** → those are MCQ *understanding* with no verse-ID, no misattribution, no abstention; our delta is **attribution + fixed-ID + abstention**, multilingual/multi-tradition. State this in the abstract.
- **"First religious verse-attribution" is blocked (IslamicEval 2025)** → never make that claim; claim the **multilingual, multi-tradition, multi-script Indian** instantiation with explicit fixed-ID metrics.
- **Feasibility / annotator scarcity (the dominant risk)** → **tiered annotation** (§3.5): deep double-annotation only for Tier-A (Gita, Bible, Constitution of India, Thirukkural); auto-checkable single-annotator breadth for Tier-B. Verify a clean, license-safe, ID-addressable edition exists **before** committing each corpus; stage Gurmukhi/Pali as extensions if access slips.
- **Base-model failure swamps attribution signal in low-resource languages (Tamil ~1–2% hallucination-free)** → design separates "can't read the language" from "misattributes"; report the closed-book control and per-language base competence alongside MAR.
- **Heterogeneous ID semantics** → per-corpus ID grammar in the schema (`BENCHMARK_DESIGN.md` §1); keep the exact-ID metric corpus-agnostic over normalized IDs.
- **Method doesn't beat SOTA (E≤D)** → pre-committed gate: demote C3 to a baseline; benchmark + validated metrics still carry a D&B / resource-track paper.
- **Solo/unaffiliated author at top venue** → secure an advisor + per-language annotators (Phase 0); arXiv+workshop is the fallback that still has real value.
- **Copyright** → public-domain editions only in the released dataset (Telang/Arnold, Müller, Griffith, Ganguli, Pope, GRETIL, WEB, Government-of-India text).
- **Compute/API cost** → budget the systems×corpora×LLMs grid; cache aggressively; use `gpt-4o-mini` + open multilingual models (Llama-3.x/Qwen2.5) for breadth.

---

## 9. Immediate next step — the v0 milestone

Ship the **v0 artifact** specified in `BENCHMARK_DESIGN.md` §8 (unchanged): the **structured Gita verse-corpus + canonical-ID schema** (`text_en` + Sanskrit + transliteration), **60–100 fully double-annotated Gita items** (spanning all question types incl. unanswerable + near-miss distractors), and the **metric harness** computing CER/CG/Attribution-P/R/F1/MAR/Abstention. This single shippable artifact validates the schema, the per-corpus ID grammar, the annotation protocol (with a real inter-annotator agreement number), and the metrics end-to-end on one corpus before scaling to the Tier-A deep set (Bible, Constitution of India, Thirukkural) and the Tier-B breadth set. It is de-risking and publishable-on-its-own as a demo/workshop artifact.
