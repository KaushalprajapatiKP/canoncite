# Related Work — Multilingual / Multi-Tradition Indian Framing (Prior-Art Vetting)

**Question vetted:** Is re-framing CANONCITE as a *multilingual, multi-tradition, multi-script Indian canonical-citation attribution* benchmark — spanning Bhagavad Gita / Upanishads / Yoga Sutras / Ramayana (Sanskrit), Dhammapada (Pali), Thirukkural (Tamil), Guru Granth Sahib (Gurmukhi), Constitution of India (Indian legal), and the Bible (English anchor) — **novel**, or already covered? Novelty axes claimed: **tradition × language/script × domain**, with fixed citation IDs as checkable ground truth and a misattribution/abstention focus.

**Investigation date:** 2026-06-30. All sources below were actually opened via WebSearch/WebFetch. URLs are real. Where I read only an abstract or a search snippet (not full text), I say so explicitly. Nothing here is fabricated.

> **Headline finding.** The *combination* (cross-lingual + multi-tradition + Indian-legal + Bible, with fixed-verse-ID attribution and abstention) is **unoccupied** — no single resource does it. BUT two adjacent classes now exist that constrain the novelty claim: (1) **Indic LLM-evaluation benchmarks that already include Hindu scripture/philosophy/law content** (ParamBench, MILU) — though as *MCQ understanding*, not citation attribution; and (2) **scripture-verse misattribution detection + correction**, already demonstrated for a *different* tradition (Islamic: IslamicEval 2025 / Qur'an QA). So the *idea* "detect/repair wrong scripture-verse citations" is no longer first-of-its-kind in religion broadly — the defensible delta is the **Indian-multilingual, multi-tradition, fixed-ID, abstention-aware instantiation**.

---

## 1. Closest existing Indic / scripture NLP datasets & benchmarks

### 1a. Indic-language LLM evaluation benchmarks (the crowding risk)
- **ParamBench** — "A Graduate-Level Benchmark for Evaluating LLM Understanding on Indic Subjects" (arXiv:2508.16185). https://arxiv.org/abs/2508.16185
  17K+ **Hindi** questions across 21 subjects (history, yoga, philosophy, literature, **law**, music, etc.) from a nationwide Indian-studies entrance exam. Diverse formats (MCQ, assertion–reason, sequence-ordering, list-matching). **Understanding/recall benchmark — NOT citation attribution; no verse-ID ground truth, no misattribution metric, no abstention, Hindi-only.** Best model (Gemma3-27B) ~56% — Hindu cultural/scripture content is hard. *This is the nearest "Indian scripture knowledge benchmark" and reviewers will cite it; our delta = attribution + multilinguality + abstention.*
- **MILU** — "Multi-task Indic Language Understanding Benchmark" (arXiv:2411.02538; AI4Bharat). https://arxiv.org/abs/2411.02538 · https://huggingface.co/datasets/ai4bharat/MILU
  ~80K MCQ across **11 Indic languages**, 8 domains / 41 subjects, incl. **Law & Governance** and **Arts & Humanities** with culturally-relevant Indian content. Again **MCQ understanding, no citation-attribution / fixed-ID / abstention** axis. Models are weakest exactly in Humanities + Law.
- **INDICQA Benchmark** (arXiv:2407.13522) — extractive (cloze/RC) QA across 11 Indic languages. https://arxiv.org/pdf/2407.13522 · **IndicQA** dataset https://huggingface.co/datasets/ai4bharat/IndicQA
- **IndicGLUE / IndicXTREME / IndicXNLI** (AI4Bharat NLU benchmarks) — general NLU, no scripture/attribution. Catalog: https://ai4bharat.github.io/indicnlp_catalog/ ; IndicXNLI arXiv:2204.08776.
- **BhashaSutra** survey of Indian NLP datasets (arXiv:2604.18423). https://arxiv.org/html/2604.18423v1
  Catalogs 200+ Indian datasets; on scripture it documents essentially **only one Gita study** (BERT sentiment/semantics of Gita translations, Chandra & Kulkarni 2022). It explicitly lists **no** Upanishad/Ramayana/Thirukkural/Guru-Granth/Dhammapada dataset and **no** citation-attribution or cross-tradition religious benchmark. Confirms the space is largely empty.

### 1b. Per-corpus scripture NLP (mostly informal / non-attribution)
- **Bhagavad Gita / Sanskrit:** public verse datasets exist (Kaggle, HF e.g. `JDhruv14/Bhagavad-Gita_Dataset`), plus Gita-vs-Yoga-Sutras classification (informal Medium write-up) and **ByT5-Sanskrit** for Sanskrit NLP tasks. RAG demos abound (GeetaGPT, Mistral7b-RAG-Gita). A research RAG paper over **Itihasa (Ramayana/Mahabharata) + Gita** ranks answers 1–5 on faithfulness over ~20 questions (ijariit V11I5-1176, https://ijariit.com/manuscripts/v11i5/V11I5-1176.pdf) — *no benchmark, no verse-ID attribution metric, tiny eval.* **No Gita/Upanishad/Ramayana citation-attribution benchmark found.**
- **Thirukkural (Tamil):** `aitamilnadu/thirukkural_instruct` (HF), a `thirukkural_QA` set via Cohere **Aya**, classification datasets (Aram/Porul/Inbam), Tamil NLP catalog (github.com/narVidhai/tamil-nlp-catalog). **Instruction/QA-style, no couplet-ID attribution or misattribution focus.**
- **Guru Granth Sahib (Gurmukhi):** **Sabudh** is building a contextual search engine over SGGS (https://sabudh.org/portfolio/building-a-rich-reservoir-of-gurmukhi/); **PunGPT2 / Quantum-RAG** for Punjabi generation+retrieval (arXiv:2508.01918); Punjabi transliteration corpora. **No SGGS QA/attribution benchmark with Ang/line ground truth found** — this corpus is the most under-resourced for our purpose.
- **Dhammapada (Pali/Buddhist):** **BuddhismEval** (HF `Nethmi14/BuddhismEval`) — bilingual **Sinhala/English** MCQ derived largely from the **Dhammapada**, with a **verse-by-verse parallel corpus** and factual/ethical/philosophical/applied categories. **SiPaKosa** (arXiv:2603.29221) — canonical Buddhist corpus in **Sinhala & Pali**. Closest existing Dhammapada NLP, but **MCQ/corpus, not verse-ID citation attribution, and Sinhala-centric (not Devanagari/Pali-script Indian framing).**

---

## 2. Multilingual / cross-lingual citation-attribution benchmarks (the key competitor class)

**Finding: no cross-lingual *citation/attribution* benchmark exists.** Multilingual benchmarks are about *understanding* (MMLU-ProX, XTREME, MILU) or *RAG robustness* (e.g., culturally-sensitive cross-lingual RAG, arXiv:2410.01171), not about scoring whether a model cited the *correct source ID* across languages. The entire attribution lineage from the original review (ALCE, AttributedQA, ExpertQA, HAGRID, CAQA, VeriCite, CiteFix, and the legal fixed-ID **Citation Grounding** / Ovcharov 2026) is **English- or single-language-centric**. **A multilingual / multi-script fixed-canonical-ID citation-attribution benchmark appears genuinely open — this is the strongest novelty axis the re-framing adds.**

Closest *religious* analogue (different tradition, monolingual-ish):
- **IslamicEval 2025** — first shared task on **capturing LLM hallucination in Islamic content** (ACL ArabicNLP 2025). https://aclanthology.org/2025.arabicnlp-sharedtasks.67/
  Subtask 1 = **hallucination detection + correction of quoted Qur'an Ayahs and Hadiths** (i.e., *is the cited/quoted verse right, and fix it*); Subtask 2 = grounded Qur'an/Hadith QA. **This is the closest existing thing to scripture-verse misattribution detection+repair** — but Arabic/Islamic, not Indian, not multi-tradition, not cross-script. It means our *concept* is anticipated in another religion; our delta is the multilingual Indian multi-tradition instantiation with explicit fixed-ID metrics.
- **IslamicMMLU** (arXiv:2603.23750), **IslamicLegalBench** (arXiv:2602.21226), and **FiqhQA** (abstention in Islamic-law QA — surfaced in search snippet, abstract not opened) show the Islamic-NLP stack already spans knowledge + legal + abstention. The Indic stack does **not** yet have the attribution/abstention equivalent.

---

## 3. Does multi-tradition Indian religious QA / attribution already exist?

**No multi-tradition (Hindu + Buddhist + Sikh + Christian) Indian religious QA or attribution benchmark was found.** Each tradition has isolated, mostly informal resources (above). ParamBench/MILU touch Hindu (and some Indian-cultural/legal) content but are single-purpose MCQ understanding sets, Hindu-leaning, with **no cross-tradition design and no attribution/abstention axis**. A generated "Durga cultural-heritage QA" set (PMC12874138) is single-deity, not attribution. **The cross-tradition + cross-script religious-attribution combination is unoccupied.**

---

## 4. Indian legal NLP relevant to the Constitution-of-India corpus

Indian legal NLP is mature but **not** organized around constitutional *citation attribution*:
- **IL-TUR** — Indian Legal Text Understanding & Reasoning benchmark (arXiv:2407.05399). https://arxiv.org/html/2407.05399v1 — multiple legal tasks; not constitution-citation attribution.
- **ILDC** (ACL 2021) — 34K Supreme Court judgments for court-judgment prediction + explanation; **InLegalBERT** (https://huggingface.co/law-ai/InLegalBERT).
- **NyayaAnumana / INLegalLlama** (arXiv:2412.08385) — largest Indian legal judgment-prediction dataset + LLM.
- **Constitution-of-India LLM case study** (arXiv:2404.06751) — RAG/LangChain QA over the Constitution; a demo, **no citation-attribution benchmark or article§clause-ID metric**.

**Takeaway:** Indian legal NLP focuses on judgment prediction / summarization, **not** on article-section-clause *citation attribution / misattribution*. So the **Constitution of India as a fixed-ID citation-attribution legal corpus is open** — a clean parallel to the original US-Constitution role, and arguably *more* defensible because the Constitution of India is longer, amendment-rich, and under-benchmarked for attribution.

**Bonus motivation (feasibility & framing):** cross-lingual faithfulness for low-resource Indian languages is a documented open problem — reported hallucination-*free* rates as low as **1–2% for Tamil** (Gemma / LLaMA-3.1) and a noted scarcity of faithfulness metrics outside English (CCL-XCoT, arXiv:2507.14239). This is strong *motivation* for a multilingual attribution/abstention benchmark — but also a red flag (see §6).

---

## 5. HONEST VERDICT — does the multilingual-Indian framing strengthen, weaken, or not change novelty?

**It STRENGTHENS novelty, on net — primarily via the language/script axis — and is defensibly novel, with caveats.**

- **Strengthens (real, new novelty surface):**
  1. **Cross-lingual / multi-script fixed-ID citation attribution does not exist anywhere** (§2). The entire attribution lineage is English/single-language. This is a clean, unoccupied axis and the single best reason to adopt the re-framing.
  2. **Multi-tradition Indian religious attribution does not exist** (§3); per-corpus resources are isolated and non-attribution.
  3. **Constitution-of-India citation attribution is open** (§4) and substitutes cleanly for US-Constitution while staying on-theme (Indian) — arguably stronger.
  4. The Indic scripture-NLP gap is real and acknowledged by the field's own survey (BhashaSutra, §1a).

- **What is partially scooped / does NOT change:**
  1. **The core concept "detect & repair wrong scripture-verse citations" is already done in another religion** — IslamicEval 2025 / Qur'an QA (§2). You cannot claim "first to do scripture-verse misattribution detection." (Mirrors the original review's finding that the fixed-ID idea was scooped in *legal* by Ovcharov 2026 — same pattern, different tradition.)
  2. **Indic LLM evaluation incl. Hindu scripture/law content already exists** (ParamBench, MILU, §1a). Reviewers will ask "how is this not another Indic benchmark?" Answer must lean on **attribution + fixed verse-ID + misattribution + abstention** (which ParamBench/MILU lack), *not* on "Indian scripture knowledge" (which they own).

- **Defensible? YES**, *if positioned narrowly* as: **the first multilingual, multi-tradition, multi-script benchmark for canonical-citation *attribution* (fixed verse/Ang/sutra/article-IDs) with misattribution and abstention** — explicitly distinguished from (a) Indic *understanding* MCQ sets and (b) monolingual Islamic verse-hallucination work. The cross-lingual attribution axis is the load-bearing novelty; tradition-count is supporting, not the claim.

---

## 6. Recommended positioning + feasibility red flags

**Positioning**
- Lead with the **cross-lingual fixed-ID attribution** gap (§2) — it is the cleanest first-mover claim and the original US-legal framing did not have it.
- Cite up front, as the bounding prior art you generalize beyond: **IslamicEval 2025** (scripture-verse misattribution, other tradition), **ParamBench / MILU** (Indic understanding, not attribution), and the legal fixed-ID **Citation Grounding** (Ovcharov 2026) from the original review. Frame CANONCITE as: *attribution where they do understanding; multilingual/multi-tradition where they are monolingual/single-tradition; abstention-aware where most are not.*
- Keep the **Bible (English)** as the high-resource clean-ID anchor and **Constitution of India** as the legal anchor — both reinforce the tradition×domain axes and are individually under-benchmarked for attribution.
- Do **not** claim "first religious citation-attribution benchmark" (Islamic work blocks it). Claim "first **multilingual, multi-script, multi-tradition Indian** canonical-citation attribution + abstention benchmark."

**Feasibility red flags (these are the bigger risk than novelty)**
- **Annotator scarcity / cost is the dominant risk.** Double-annotation with verse-ID ground truth across **8 traditions × multiple scripts (Devanagari, Tamil, Gurmukhi, Pali, English)** is far beyond a solo/small-team budget. ParamBench/MILU had AI4Bharat-scale institutional backing. **Recommend scoping v1 to 3–4 corpora with deep annotation** (e.g., Gita + Bible + Constitution-of-India + Thirukkural or Dhammapada-Pali), and stage the rest as extensions — same "moderate size, strong agreement" advice as the original plan.
- **Text/OCR availability & ID conventions are uneven.** Bible/Gita/Constitution have clean public-domain text + canonical IDs. **Guru Granth Sahib (Ang/line)** and **Pali Dhammapada** are the most under-resourced (Gurmukhi tooling is early-stage — Sabudh/PunGPT2; reliable line-level IDs and clean text are the bottleneck). Verify a clean, license-safe, ID-addressable edition exists **before** committing each corpus.
- **Heterogeneous citation-ID semantics** (chapter.verse vs Ang.line vs Kural-number vs article§clause vs sutra-pada) complicate a "unified exact-ID metric" — solvable, but needs a per-corpus ID grammar in the schema.
- **Low-resource model performance is poor** (Tamil hallucination-free ~1–2%) — good for *motivation*, but means results may be dominated by base-model failure rather than attribution behavior; design must separate "can't read the language" from "misattributes."
- **Copyright:** same as original — public-domain editions only (e.g., classical Tamil Thirukkural, public SGGS text, public Pali Dhammapada, public-domain Bible/Gita translations).

---

### Summary (8–12 lines)

1. No single resource does multilingual + multi-tradition + Indian-legal + Bible **canonical-ID citation attribution** — the *combination* is unoccupied.
2. **Cross-lingual / multi-script fixed-ID citation attribution does not exist anywhere** (ALCE/CAQA/VeriCite/Citation-Grounding are all English/single-language) — the strongest new novelty axis.
3. But **Indic LLM-evaluation benchmarks already cover Hindu scripture/philosophy/law** — ParamBench (17K Hindi) and MILU (80K, 11 langs) — as *MCQ understanding*, not attribution.
4. And **scripture-verse misattribution detection+correction already exists for another tradition** — **IslamicEval 2025** (Qur'an Ayah/Hadith) — so "first religious verse-attribution" is blocked.
5. Per-corpus Indic scripture NLP is sparse/informal (Gita RAG demos, Thirukkural-instruct, BuddhismEval/Dhammapada, Sabudh-SGGS) — none with verse-ID attribution or misattribution metrics.
6. **Constitution-of-India attribution is open** (Indian legal NLP = judgment prediction/summarization, not constitutional citation), a clean substitute for the US-Constitution role.
7. Biggest risk is **feasibility, not novelty**: annotator scarcity for Gurmukhi/Pali/Tamil/Sanskrit, uneven OCR/text + ID availability (SGGS and Pali worst), heterogeneous ID semantics, and base-model failure swamping attribution signal in low-resource languages.
8. Position as **attribution + abstention** (what Indic benchmarks lack) and **multilingual/multi-tradition** (what Islamic/legal attribution work lacks); scope v1 to 3–4 deeply-annotated corpora and stage the rest.

**VERDICT: STRENGTHENS novelty (adds a genuinely open cross-lingual/multi-script attribution axis) — defensible? YES, if narrowed to "first multilingual, multi-tradition, multi-script Indian canonical-citation *attribution + abstention* benchmark" and explicitly contrasted with ParamBench/MILU (understanding) and IslamicEval 2025 (single-tradition verse-hallucination); feasibility, not novelty, is the real threat.**
