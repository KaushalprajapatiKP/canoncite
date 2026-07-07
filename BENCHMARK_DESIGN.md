# BENCHMARK_DESIGN — CANONCITE

**A multilingual, multi-tradition, multi-script canonical-citation attribution + abstention benchmark for retrieval-augmented QA, over Indian canonical texts (with cross-cultural and legal anchors).**

This is the buildable spec for the headline contribution (**C1**) of `RESEARCH_PLAN.md`. It is concrete enough to start construction. It assumes the honest prior-art positioning in `RELATED_WORK.md` and `RELATED_WORK_MULTILINGUAL.md`: we do **not** claim the fixed-ID-enables-exact-attribution *idea* (Ovcharov 2026, legal), nor "first religious verse-attribution" (IslamicEval 2025, Islamic), nor "Indian scripture knowledge" (ParamBench/MILU, MCQ understanding). We claim the **first multilingual, multi-tradition, multi-script Indian canonical-citation attribution + abstention benchmark**, plus integration and **human-correlation validation** of the metric suite. The **cross-lingual / multi-script axis is the freshest novelty** — it is unoccupied across the entire (English/single-language) attribution lineage.

Design principles:
1. **Exact, deterministic ground truth.** Every item has gold citation IDs from a closed, public canonical ID space, so attribution can be scored without NLI — across scripts.
2. **Content-support is checked separately from ID match.** A cited ID can be *real* yet *not support the claim*; the metrics and annotation separate these (see §5).
3. **Public-domain only.** No copyrighted translation enters the released dataset (see §7).
4. **Three novelty axes by design, not convenience.** Corpora span **tradition** (Hindu, Buddhist, Sikh, Tamil-ethical, Christian, secular-legal) × **language/script** (Sanskrit/Devanagari, Pali, Tamil, Gurmukhi, Hindi, English) × **domain** (interpretive-religious, narrative-religious, ethical-aphoristic, prescriptive-legal) to argue generality.
5. **Multilingual text triple.** Each corpus carries `text_en` + the `original` (Sanskrit/Pali/Tamil/Gurmukhi/Hindi) + `transliteration` (IAST/ISO-15919/romanization) where applicable.
6. **Feasibility-managed via tiered annotation** (see §1.5): deep annotation for a clean Tier-A set, auto-checkable breadth for Tier-B — so the multilingual scope does not drown the signal under shallow annotation.

---

## 1. Corpora (v1 roster — multilingual, multi-tradition, all public-domain editions)

Ten corpora spanning **tradition × language/script × domain**. Each has a closed canonical ID space `U_corpus` and a multilingual text triple (`text_en` + `original` + `transliteration` where applicable). **v0 = Gita only** (unchanged, §8). **v1 = the Tier-A deep set + the Tier-B breadth set** (annotation tiers in §1.5; release staging in §1.6). Sources are public-domain; **flags** mark availability/feasibility risks that must be resolved before a corpus is committed.

| Corpus | Tradition / domain | Lang / script | Canonical ID scheme | Public-domain EN source | Original-text source | Tier |
|---|---|---|---|---|---|---|
| **Bhagavad Gita** | Hindu / interpretive | Sanskrit / Devanagari + EN | `chapter.verse` (18 ch, **701 v** incl. 13.35; e.g. `2.47`) | **Besant & Das**, 1905 (PD, printed verse-by-verse — the v0 release source; Telang SBE 1882 is PD but *continuous prose with no inline verse numbers*, unsplittable to 700 verses without fabricating boundaries — see `data/corpora/bhagavad_gita/VALIDATION.md`); Arnold 1885 retained as a 2nd-translation robustness layer | **gita/gita** open dataset (Devanagari + IAST; ancient PD text) | A *(v0 ✅ built)* |
| **Upanishads (principal)** | Hindu / interpretive | Sanskrit / Devanagari + EN | per-Upanishad `section.khanda.verse` | **Max Müller**, SBE vols. 1 & 15 (PD) | **GRETIL** | B |
| **Yoga Sutras of Patanjali** | Hindu / aphoristic | Sanskrit / Devanagari + EN | `pada.sutra` (4 padas; e.g. `1.2`) | **J.H. Woods**, *The Yoga-System of Patañjali*, 1914 (PD) / **Vivekananda**, *Raja Yoga*, 1896 (PD) | **GRETIL** | B |
| **Ramayana (Valmiki)** | Hindu / narrative | Sanskrit / Devanagari + EN | `kanda.sarga.shloka` | **R.T.H. Griffith** (PD) | **GRETIL** | B |
| **Mahabharata** | Hindu / narrative | Sanskrit / Devanagari + EN | `parva.adhyaya.shloka` | **K.M. Ganguli**, 1883–96 (PD, sacred-texts.com) | **GRETIL** | B *(largest)* |
| **Dhammapada** | Buddhist / interpretive | Pali + EN | `chapter.verse` (26 ch, 423 v; e.g. `1.5`) | **Max Müller**, SBE vol. 10, 1881 (PD, verse-numbered) | **Pali** (Tipitaka / GRETIL — *flag: Pali availability/edition risk*) | B |
| **Thirukkural** | Tamil / ethical-aphoristic | Tamil + EN | `kural` no. 1–1330 | **G.U. Pope**, 1886 (PD) | Tamil source (classical, PD) | A *(clean demonstrator)* |
| **Guru Granth Sahib** | Sikh / devotional | Gurmukhi + EN | `ang` (page) + line/shabad | public-domain EN translation | Gurmukhi source (*flag: hardest — annotator-scarce, line-ID tooling early-stage*) | B |
| **Constitution of India** | secular-legal, prescriptive | Hindi / EN | `Part/Article §clause` (e.g. `Art. 21`; `Art. 19(1)(a)`) | **Government of India** public-domain text (EN) | Hindi official text (PD) | A *(legal anchor)* |
| **Bible** | Christian / narrative+law | English | `BOOK chapter:verse` (e.g. `John 3:16`) | **World English Bible (WEB)** — PD, machine-readable; 66-book canon freezes `U` | (English anchor — no separate original layer) | A *(cross-cultural anchor)* |

**Notes & cross-corpus design:**
- **GRETIL** (Göttingen Register of Electronic Texts in Indian Languages) supplies machine-readable Devanagari originals for all Sanskrit corpora; it is the single most important original-text source.
- **Mahabharata is the largest corpus (~100k shloka)** → a deliberate **retrieval stress test** for the index. It also **contains the Bhagavad Gita** (Bhishma Parva, adhyayas ~25–42). The two are kept in **separate ID namespaces** (`bhagavad_gita` `2.47` vs `mahabharata` `bhishma.<adhyaya>.<shloka>`); the overlap is a **deliberate cross-corpus near-miss case** — a model asked a Gita question may (mis)cite the Mahabharata locus or vice versa, which the benchmark scores directly.
- **Thirukkural** is the **clean multilingual demonstrator**: a flat 1–1330 couplet ID space, public-domain Tamil + Pope's English — the lowest-risk non-Sanskrit corpus and ideal for the cross-lingual claim.
- **Constitution of India** replaces the US Constitution as the legal anchor (on-theme Indian, under-benchmarked for attribution; Indian legal NLP does judgment-prediction/summarization, not constitutional citation — `RELATED_WORK_MULTILINGUAL.md` §4). Note Indian-article sub-clause IDs like `Art. 19(1)(a)`.
- **Bible (WEB)** stays as the high-resource, ultra-clean-ID, large-scale **cross-cultural anchor**.

**ID-space construction (per corpus, frozen artifact):** produce a `corpus_index.jsonl` with one row per atomic citable unit, carrying the multilingual triple:
```json
{"corpus":"bhagavad_gita","id":"2.47","unit":"verse","text_en":"...","original":"कर्मण्येवाधिकारस्ते ...","translit":"karmaṇy evādhikāras te ...","script":"Devanagari","lang":"san","translation_source":"Besant_1905","original_source":"gita/gita","chapter":2,"verse":47,"tokens":33}
```
> **v0 field-name note:** the built Gita `corpus_index.jsonl` currently uses `sanskrit`/`transliteration`/`sanskrit_source`/`source_urls` (Gita-specific) rather than the generic `original`/`translit`/`script`/`lang` triple shown above. These will be normalized to the generic multilingual schema when the shared corpus loader + the non-Sanskrit corpora (Tamil, Gurmukhi, Pali) land — the generic names are required once `script`/`lang` vary.

`U_corpus` = the set of all `id` values. This file is the single source of truth for "does this citation exist" and for retrieval indexing. Frozen with a version hash. Because ID semantics differ across corpora (`chapter.verse` vs `pada.sutra` vs `kanda.sarga.shloka` vs `ang`+line vs `kural`-no. vs `Part/Article§clause`), each corpus declares a **per-corpus ID grammar** (parse/normalize/validate regex) so the exact-ID metric stays corpus-agnostic over normalized IDs.

> **Drop from release:** the repo currently ships *Bhagavad-gita As It Is* (Prabhupada/BBT) — **copyrighted**. Use Telang/Arnold (+ GRETIL Sanskrit) in the released set. BBT may stay only in private, unreleased experiments.

### 1.5 Tiered annotation strategy

Double-annotating verse-ID ground truth across 8 traditions and 5 scripts is beyond a solo/small-team budget (`RELATED_WORK_MULTILINGUAL.md` §6 names annotator scarcity as the dominant risk). We go broad **without shallow annotation drowning the signal** via two tiers:

- **Tier A — deep:** full **double-annotation** + **interpretive items** + per-citation **content-support labels** (`full/partial/none`) + **inter-annotator agreement** reporting. Corpora: **Bhagavad Gita, Bible, Constitution of India, Thirukkural**. These carry the high-rigor claims (human-correlation validation of the exact metric; the C2 generality contribution).
- **Tier B — breadth:** **factual / retrieval / unanswerable** items only, scored by **auto-checkable, NLI-free metrics** (CER, exact-attribution P/R/F1, MAR-exist, NMR, abstention) — **single-annotator + spot-adjudication**, no per-citation human support label required. Corpora: **Upanishads, Yoga Sutras, Ramayana, Mahabharata, Dhammapada, Guru Granth Sahib**. These extend the language/script/tradition axes at low annotation cost.

**The datasheet (§7) reports each corpus's tier transparently** — the deep-vs-breadth split is a documented design decision, not a hidden quality gradient. Tier-B items deliberately avoid `interpretive` and per-citation `answer_support` (which need expensive multi-annotator judgment) and lean on the deterministic metrics that need no human content label.

### 1.6 Per-corpus feasibility / risk and v1-vs-full-release split

| Corpus | EN text | Original / script | OCR / ID-scheme risk | Annotator scarcity | Tier | Release |
|---|---|---|---|---|---|---|
| **Bhagavad Gita** | clean (Telang/Arnold) | clean (GRETIL) | low — flat `ch.verse` | low | A | **v1 (v0 seed)** |
| **Bible** | clean (WEB) | n/a (English) | very low — ultra-clean IDs | low | A | **v1** |
| **Constitution of India** | clean (Govt of India) | Hindi official | low; sub-clause IDs `19(1)(a)` need grammar | low–med | A | **v1** |
| **Thirukkural** | clean (Pope) | clean Tamil, flat 1–1330 | low | medium (Tamil verse literacy) | A | **v1** |
| **Upanishads** | clean (Müller SBE) | clean (GRETIL) | med — per-Upanishad `section.khanda.verse` heterogeneity | medium | B | **v1** |
| **Yoga Sutras** | clean (Woods/Vivekananda) | clean (GRETIL) | low — `pada.sutra` | medium | B | **v1** |
| **Ramayana** | clean (Griffith) | clean (GRETIL) | med — large `kanda.sarga.shloka` | medium | B | **v1** |
| **Mahabharata** | clean (Ganguli) | clean (GRETIL) | **high scale (~100k shloka)**; Gita namespace overlap | medium | B | **v1 (retrieval stress)** |
| **Dhammapada** | clean (Müller SBE) | **flag: Pali edition/script availability** | med | medium | B | **v1 if Pali verified, else full-release** |
| **Guru Granth Sahib** | PD EN translation | **flag: Gurmukhi tooling early-stage; reliable Ang/line IDs are the bottleneck** | **high** | **high (Gurmukhi annotators scarce)** | B | **full-release (stage as extension)** |

**v1 = Tier-A (4) + Tier-B that have a verified clean, license-safe, ID-addressable edition** (Upanishads, Yoga Sutras, Ramayana, Mahabharata, Dhammapada-if-Pali-verified). **Full release adds Guru Granth Sahib** (and Dhammapada if Pali slips to a later cut). Each corpus is committed only after its clean, ID-addressable, public-domain edition is confirmed.

---

## 2. Item schema (JSON)

One canonical schema across all corpora. Stored as JSONL, one item per line.

```json
{
  "id": "gita-0123",
  "corpus": "bhagavad_gita",
  "question": "What does the Gita teach about performing one's duty without attachment to the results of action?",
  "question_type": "conceptual",
  "answerable": true,
  "ambiguity": "low",
  "gold_citations": ["2.47", "2.48"],
  "gold_citation_spans": [{"id_start":"2.47","id_end":"2.48"}],
  "near_miss_distractors": ["5.18", "3.19"],
  "gold_answer": "One should perform prescribed action while renouncing attachment to its fruits; the right to action never extends to its results (2.47), and equanimity in success and failure is called yoga (2.48).",
  "answer_support": [
    {"citation":"2.47","support":"full","rationale":"states the right is to action, not to fruits"},
    {"citation":"2.48","support":"full","rationale":"defines yoga as evenness, abandoning attachment"}
  ],
  "must_abstain": false,
  "abstain_reason": null,
  "provenance": {"seed":"llm_proposed","seed_model":"gpt-4o-2024-08-06","verified":true},
  "annotator_ids": ["a1","a2"],
  "annotations": [
    {"annotator":"a1","gold_citations":["2.47","2.48"],"answerable":true,"ambiguity":"low"},
    {"annotator":"a2","gold_citations":["2.47","2.48"],"answerable":true,"ambiguity":"low"}
  ],
  "adjudicated": true,
  "adjudicator":"a3",
  "license":"public-domain",
  "version":"v0.1"
}
```

**Field notes:**
- `question_type ∈ {factual, retrieval, conceptual, interpretive, unanswerable}`.
- `gold_citations`: closed set of canonical IDs that *content-support* the gold answer. For interpretive items this is the *defensible* set agreed by annotators, possibly several valid IDs.
- `gold_citation_spans`: contiguous ranges where the gold is a passage (e.g. a Gita argument spanning 2.47–2.48, or `Art. I, §8` clauses).
- `near_miss_distractors`: real, existing IDs that are *plausible but wrong* (topically adjacent), used to measure near-miss misattribution. Required for `retrieval`/`factual` items.
- `answer_support`: per-citation human label `full | partial | none` — the bridge between *ID match* and *content support* (see §5). Drives the content-support check.
- `must_abstain`/`abstain_reason`: for `unanswerable` items, the correct behavior is abstention; `gold_citations` is empty.

### Per-question-type examples

**factual** (single ID):
```json
{"id":"bible-0007","corpus":"bible","question":"In which verse does Jesus say 'I am the way, the truth, and the life'?","question_type":"factual","answerable":true,"ambiguity":"low","gold_citations":["John 14:6"],"near_miss_distractors":["John 8:12","John 11:25"],"gold_answer":"John 14:6.","must_abstain":false}
```

**retrieval** ("which passage discusses X"):
```json
{"id":"const-0031","corpus":"constitution_of_india","question":"Which article guarantees the freedom of speech and expression?","question_type":"retrieval","answerable":true,"ambiguity":"low","gold_citations":["Art. 19(1)(a)"],"near_miss_distractors":["Art. 19(1)(b)","Art. 21"],"gold_answer":"Article 19(1)(a) guarantees the freedom of speech and expression.","must_abstain":false}
```

**conceptual** (multi-ID synthesis):
```json
{"id":"gita-0123","corpus":"bhagavad_gita","question":"What does the Gita teach about acting without attachment to results?","question_type":"conceptual","answerable":true,"ambiguity":"low","gold_citations":["2.47","2.48"],"near_miss_distractors":["5.18"],"gold_answer":"...","must_abstain":false}
```

**interpretive** (ambiguous, multiple defensible citations — Tier-A only):
```json
{"id":"kural-0045","corpus":"thirukkural","question":"How does the Thirukkural characterize the value of forbearance toward those who wrong you?","question_type":"interpretive","answerable":true,"ambiguity":"high","gold_citations":["151","152","156"],"near_miss_distractors":["311"],"gold_answer":"It praises patient endurance of insult as a lasting virtue that ultimately surpasses the offender (151–156).","must_abstain":false}
```

**unanswerable / out-of-corpus** (must abstain, empty gold):
```json
{"id":"const-0099","corpus":"constitution_of_india","question":"What does the Constitution of India say about the regulation of cryptocurrency exchanges?","question_type":"unanswerable","answerable":false,"ambiguity":"low","gold_citations":[],"near_miss_distractors":["Art. 19(1)(g)"],"gold_answer":"The Constitution does not address this; the system should abstain rather than cite an article.","must_abstain":true,"abstain_reason":"topic_not_in_corpus"}
```

---

## 3. Question taxonomy & target counts (tier-aware)

Aim **~1,200–1,500 items for v1** with strong agreement, not a huge noisy set. **Tier-A corpora** carry the full five-type taxonomy (incl. interpretive + per-citation support); **Tier-B corpora** are smaller (≈100–150 items) and **factual/retrieval/abstention-weighted** (auto-checkable, no interpretive items — §1.5).

**Tier A (deep, ~270/corpus):**

| Type | What it tests | Gita | Bible | Constitution of India | Thirukkural | Notes |
|---|---|---:|---:|---:|---:|---|
| **factual** (single ID) | exact lookup | 60 | 60 | 50 | 60 | each ships ≥2 near-miss distractors |
| **retrieval** ("which passage…") | locate the right ID | 60 | 60 | 50 | 60 | distractor-heavy |
| **conceptual** (multi-ID synthesis) | synthesize across verses | 60 | 60 | 40 | 50 | gold is a set/span |
| **interpretive** (ambiguous) | reasoning vs fabrication | 50 | 50 | 30 | 40 | `ambiguity=high`; multiple defensible IDs |
| **unanswerable / abstention** | must abstain | 40 | 40 | 30 | 40 | empty gold; the rigor differentiator |
| **Per-corpus total** | | **270** | **270** | **200** | **250** | full double-annotation + support labels |

**Tier B (breadth, ~100–150/corpus; factual/retrieval/abstention only, auto-checkable):**

| Type | Upanishads | Yoga Sutras | Ramayana | Mahabharata | Dhammapada | Guru Granth Sahib | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| **factual** (single ID) | 50 | 45 | 50 | 60 | 50 | 40 | near-miss distractors |
| **retrieval** ("which passage…") | 50 | 45 | 50 | 60 | 50 | 40 | distractor-heavy; Mahabharata = retrieval stress |
| **unanswerable / abstention** | 30 | 30 | 30 | 30 | 30 | 30 | empty gold |
| **Per-corpus total** | **130** | **120** | **130** | **150** | **130** | **110** | single-annotator + spot-adjudication |

**Approx. v1 grand total:** Tier-A ≈ **990** + Tier-B (excl. SGGS, staged) ≈ **660** → **~1,300–1,500 items**. Scales by raising per-type counts; SGGS (Tier-B) is full-release (§1.6).

**Two cross-cutting item properties (not separate types):**
- **near-miss-citation distractor coverage:** ≥60% of `factual`/`retrieval` items carry ≥2 existing-but-wrong distractor IDs, enabling direct measurement of near-miss misattribution (gold `2.47` vs distractor `5.18`). **Cross-corpus near-miss:** Gita-vs-Mahabharata (Bhishma Parva) loci are a built-in distractor pair (§1).
- **out-of-corpus traps** inside `unanswerable`: questions answerable in *another* corpus but not this one (e.g., ask the Constitution of India a Gita question, or a Thirukkural question of the Dhammapada) — catches cross-corpus and cross-tradition leakage and over-eager citation.

---

## 4. Construction protocol

Pipeline: **freeze corpus → semi-automatic seed generation → annotation (tier-dependent) → adjudication → agreement reporting → datasheet**. The protocol below is the **Tier-A** path (deep); **Tier-B** uses the same Steps 0–1 then a lighter Step 2′ (single-annotator + spot-adjudication, factual/retrieval/abstention only — no per-citation `answer_support`, no interpretive items; §1.5). Tier-B relies on the **deterministic** ID-existence/exact-match metrics, which need no human content label.

**Step 0 — Freeze corpora (§1).** Build `corpus_index.jsonl` per corpus (with the `text_en`/`original`/`translit` triple and a per-corpus ID grammar); version-hash it. Nothing downstream may cite an ID outside `U`.

**Step 1 — Seed generation (semi-automatic, LLM-proposed, ID-grounded).**
For each corpus, prompt an LLM (e.g. `gpt-4o-2024-08-06`, pinned) with *retrieved real verses* to draft candidate `(question, proposed_gold_citations, draft_answer, question_type, proposed_distractors)`. Generation is **conditioned on actual passage text** so proposals are grounded, but **LLM output is never ground truth** — it is a draft for humans. Unanswerable items are seeded by (a) asking about out-of-corpus topics and (b) cross-corpus swaps. Over-generate ~1.5× target to allow rejection.

**Step 2 — Double human annotation (Tier A; ≥2 annotators/item).**
Each annotator independently, **with the corpus open**, sets: `answerable`, `gold_citations` (verifying each cited ID exists in `U` and *content-supports* the answer), `answer_support` per citation (`full/partial/none`), `ambiguity`, and validates/edits `near_miss_distractors`. Annotators may **reject** an item (bad/ungrounded seed). Annotation UI shows the candidate IDs' actual text (`text_en` + original/translit) so support is judged against the source, not memory.

**Step 2′ — Single-annotator pass (Tier B).** One annotator with the corpus open verifies `gold_citations` exist in `U` and locate the right unit, sets `answerable`, and validates `near_miss_distractors`, for factual/retrieval/abstention items only. No per-citation `answer_support`, no interpretive items. A senior adjudicator **spot-checks** a sample (see quality gates).

**Step 3 — Adjudication.** For Tier A, a third annotator resolves disagreements (citation-set mismatch, answerable/abstain conflict, ambiguity-grade conflict); adjudicated value is gold; `adjudicated=true`. For Tier B, the spot-adjudicator resolves flagged/sampled items.

**Step 4 — Inter-annotator agreement (report explicitly).**
- **Citation-set agreement:** report **Krippendorff's α (MASI distance for set-valued labels)** — correct stat for overlapping-set annotations; target **α ≥ 0.67** (acceptable), aim **≥ 0.80**.
- **Categorical labels** (`answerable`, `question_type`, `ambiguity`): **Cohen's κ** (2 annotators) / **Fleiss' κ** (>2); target **κ ≥ 0.6** (substantial), aim **≥ 0.8**.
- **Per-citation support label** (`full/partial/none`): weighted **κ**; target **≥ 0.6**.
Report agreement per corpus and per question type (interpretive will be lower — that is informative, not disqualifying). **Agreement is computed on Tier-A corpora** (double-annotated) and on the **double-annotated spot-check sample** of each Tier-B corpus (a per-corpus reliability estimate even where the bulk is single-annotated).

**What is human-verified vs auto:**
| Element | Auto | Human-verified |
|---|---|---|
| Citation ID *exists* in `U` | ✅ deterministic check | spot-check only |
| Citation *content-supports* answer | ✗ (LLM draft only) | ✅ **required** (`answer_support`) |
| `answerable` / `must_abstain` | LLM proposes | ✅ double-annotated |
| `ambiguity` grade | LLM proposes | ✅ double-annotated |
| Near-miss distractor *is wrong but plausible* | LLM proposes | ✅ verified |
| Final gold citation set | ✗ | ✅ adjudicated |

**Quality gates before release:** ≥95% of gold IDs exist in `U` (the rest are bugs → fixed); Tier-A agreement targets met; **≥20% of each Tier-B corpus re-checked by a senior adjudicator** (vs ≥20% spot-audit + full double-annotation for Tier A); held-out 50-item sanity audit per corpus.

---

## 5. Metric definitions (precise)

Per answer: let **G** = gold citation set, **C** = model-cited set, **R** = retrieved-ID set, **U** = corpus ID space. Define **content-support** `supp(c) ∈ {full, partial, none}` = whether the *text at id c* supports the specific claim it is attached to (auto via NLI/LLM-judge at eval time; **calibrated against the human `answer_support` labels** in the benchmark — this calibration is a C2 contribution). A citation is **valid** iff `c ∈ U` AND `supp(c) ≠ none`.

**Primary (exact, deterministic where possible):**

1. **Citation Existence Rate (CER)** — are cited IDs real?
   `CER = |{c ∈ C : c ∈ U}| / |C|` (define `=1` if `C=∅` on answerable, flagged separately). *Fully deterministic.*

2. **Citation Groundedness (CG)** — cited from what was retrieved?
   `CG = |{c ∈ C : c ∈ R}| / |C|`. *Deterministic.*

3. **Attribution Precision / Recall / F1 — exact-ID variant** (against gold set):
   `P_exact = |C ∩ G| / |C|`, `R_exact = |C ∩ G| / |G|`, `F1_exact = 2PR/(P+R)`. *Deterministic.*

4. **Attribution P/R/F1 — span-overlap variant** (credits near-but-not-exact, e.g. cite `2.47` when gold span is `2.47–2.48`): treat each id as covering its unit; match `c` to `g` if their spans overlap or are within a corpus-specific tolerance window (e.g. ±1 verse, same chapter; for Constitution, same section). Report alongside exact to show how much "error" is adjacency vs true misattribution.

5. **Misattribution Rate (MAR)** — the headline number:
   `MAR = (# answers with ≥1 cited id that is non-existent OR has supp(c)=none) / (# answers that cite at least one id)`.
   Decompose: **MAR-exist** (non-existent id, deterministic) + **MAR-support** (real id, unsupported content, judge-based). Report both; MAR-exist is the clean, NLI-free signal.

6. **Near-miss Misattribution Rate (NMR)** — fraction of misattributions where the cited id is a *near-miss distractor* (real, adjacent, wrong). Uniquely measurable here; a key differentiator.

7. **Abstention Correctness** — on `unanswerable` items:
   `AbstAcc = (# correctly abstained) / (# unanswerable)`. Also report **over-citation rate** = fraction of unanswerable items where the system cited any id (the failure mode). On answerable items, report **wrong-abstention rate**.

**Content-support check (how ID-match ≠ content-support is enforced):** for every cited id, run an NLI/LLM-judge over `(claim_sentence, text[id])` to get `supp(c)`. Validate this auto-judge against the human `answer_support` labels in the released set and **report the correlation/κ** — i.e., we prove the exact-ID metric plus a calibrated support check tracks human judgment across corpora (the C2 generality/validation contribution; credit Ovcharov 2026/CAQA for the existence-check idea, ALCE for P/R).

**Secondary (comparability):**
- **Retrieval:** Recall@k, nDCG@k against gold IDs (k ∈ {1,5,10,20}).
- **Faithfulness:** RAGAS faithfulness + answer-relevance; **VeriCite/ALCE NLI citation P/R** for head-to-head with passage-NLI methods.
- **Human ratings (1–5):** answer accuracy, citation quality, helpfulness — on a stratified sample (≥150 items/system), ≥2 raters, report κ.

---

## 6. Evaluation protocol

**Systems (from `RESEARCH_PLAN.md` §5):** A Naive RAG, B Hybrid (BM25+dense RRF), C Reranking (cross-encoder), **D real SOTA repair (VeriCite and/or Self-RAG/CRAG; CG-style where feasible)**, **E ours (exact-ID Attribution-Verifier)**.

**LLMs (pinned versions, ≥3 for breadth):** `gpt-4o-2024-08-06` + `gpt-4o-mini`, an open **multilingual** model (Llama-3.x-70B or Qwen2.5-72B, both strong on Indic), and one more (Claude / Mistral) for diversity. All temperatures and prompts fixed and logged.

**Grid:** systems × corpora × LLMs, reported per (corpus, language/script, question_type). Closed-book (no retrieval) control to separate parametric recall from RAG behavior — and, critically, to **separate "can't read the language" from "misattributes"** (a per-language base-competence probe, since low-resource Tamil/Pali/Gurmukhi base performance is poor; `RELATED_WORK_MULTILINGUAL.md` §6).

**Baselines that matter:** E is admissible **only if it beats D** on MAR at equal-or-lower cost (decision gate, `RESEARCH_PLAN.md` §2/§5). Otherwise E is reported as a baseline and C1+C2 carry the paper.

**Ablations:** (i) metadata-aware vs metadata-free index; (ii) exact-ID check vs NLI-only repair (cost + MAR); (iii) with/without near-miss distractors in retrieval (incl. the cross-corpus Gita↔Mahabharata pair); (iv) k sweep; (v) translation-robustness (Telang vs Arnold for Gita) **and cross-lingual robustness** (query/answer in EN vs original-script vs transliteration) — does misattribution change with language/script?; (vi) abstention threshold sweep; (vii) Tier-A vs Tier-B (does deep annotation change the deterministic-metric conclusions?).

**Reporting:** per-corpus and pooled; bootstrap 95% CIs; significance (paired bootstrap / McNemar for abstention). Release all per-item model outputs + cited-ID extractions for auditability.

---

## 7. Datasheet, licensing & ethics

**Datasheet (Gebru et al. "Datasheets for Datasets"):** ship `DATASHEET.md` answering Motivation / Composition / Collection process / Preprocessing / Uses / Distribution / Maintenance. Key entries: items are LLM-seeded then human-verified (not scraped); **each corpus's annotation tier (A deep / B breadth) is reported transparently** (§1.5); per-corpus edition + license + ID grammar; annotators' qualifications, languages, and instructions; known biases (translation choice, script/transliteration scheme, annotator worldview on interpretive religious items across multiple traditions); intended use = *evaluating citation attribution*, **not** doctrinal/theological authority for any tradition.

**Licensing:**
- **Released text:** public-domain editions only — Telang/Arnold SBE + GRETIL (Gita), Müller SBE + GRETIL (Upanishads, Dhammapada), Woods/Vivekananda + GRETIL (Yoga Sutras), Griffith + GRETIL (Ramayana), Ganguli + GRETIL (Mahabharata), Pope + classical Tamil source (Thirukkural), public-domain EN + Gurmukhi (Guru Granth Sahib), Government-of-India public-domain text (Constitution of India), WEB (Bible). Record edition + source URL + retrieval date per corpus in `corpus_index.jsonl`, for **both** the `translation_source` and the `original_source` (GRETIL etc.).
- **Annotations/questions:** release under **CC BY 4.0** (or CC BY-SA to match SBE-derived norms); code under MIT/Apache-2.0.
- **Avoid copyrighted translations:** explicit checklist — **no BBT/Prabhupada**, no NIV/ESV/other in-copyright Bibles, no in-copyright Gita/Tamil/Sanskrit/Gurmukhi translations. A CI check rejects any released text whose `translation_source` or `original_source` is not on the public-domain allowlist.
- **Per-corpus license verification before commit:** confirm each edition's public-domain status (esp. **Pali Dhammapada** and **Gurmukhi SGGS** originals, the two flagged corpora) before it enters a release cut (§1.6).

**Ethics:** religious texts across **multiple living traditions** (Hindu, Buddhist, Sikh, Tamil-ethical, Christian) are sensitive. Frame strictly as an attribution-faithfulness instrument; add a prominent disclaimer that gold answers are *textual-attribution* judgments, not endorsements of interpretation for any tradition. Recruit annotators with **relevant language and tradition literacy** (Sanskrit/Tamil/Pali/Gurmukhi/Hindi/English); for interpretive items (Tier A), prefer *defensible-set* gold over forcing a single "correct" theology, and surface ambiguity via the `ambiguity` field rather than hiding it. Treat each tradition's texts with equivalent care; do not privilege one tradition's framing. Document annotator demographics and languages at aggregate level; pay fairly; no PII.

---

## 8. v0 milestone (first shippable artifact)

**Goal:** prove the schema + annotation protocol + metric harness end-to-end on **one** corpus before scaling.

**Deliverables:**
1. ✅ **`corpus_index.jsonl` for the Gita** (Besant & Das 1905 EN + gita/gita Devanagari/IAST; **701 verses** incl. 13.35; 18.33 EN absent in Besant → flagged null) — frozen, version-hashed (`sha256 5ccfd87c…`). Built by `canoncite/corpus/build_gita.py`; provenance + spot-check in `VALIDATION.md`.
2. **60–100 fully double-annotated + adjudicated Gita items**, stratified across all five types incl. **≥10 unanswerable** and **≥20 items with near-miss distractors** (e.g., gold `2.47`, distractor `5.18`).
3. ✅ **Metric harness** (`canoncite/`) computing CER, CG, Attribution-P/R/F1 (exact + span), MAR (exist + support), NMR, Abstention Correctness — runnable on any system's `(answer, cited_ids)` output (7 tests pass).
4. **One agreement number reported** (Krippendorff's α with MASI on citation sets; Cohen's κ on categorical labels) from the double annotation — validates the protocol is teachable.
5. **A baseline run:** the current naive RAG (System A) scored by the harness on the 60–100 items → first real MAR/abstention numbers.
6. **Mini-datasheet + license check** passing (public-domain text only — Besant 1905 EN + ancient-PD Sanskrit).

**Definition of done:** the harness ingests model outputs and emits the full metric table; α/κ meet or transparently miss targets; the 60–100 items pass the ≥95%-IDs-exist gate. This artifact alone is demo/workshop-grade and de-risks the full v1 build — the Tier-A deep set (Bible, Constitution of India, Thirukkural) plus the Tier-B breadth set (Upanishads, Yoga Sutras, Ramayana, Mahabharata, Dhammapada, Guru Granth Sahib), ~1,300–1,500 items across 5 scripts (§1, §3).
