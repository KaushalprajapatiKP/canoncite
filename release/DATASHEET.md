# Datasheet for CANONCITE (v0)

A "Datasheet for Datasets" (Gebru et al., 2021) for the public release of the
**CANONCITE** benchmark — a trilingual, multi-tradition benchmark for
**canonical-citation attribution** over public-domain scripture and legal
corpora. This datasheet documents the public release only: **public-domain text
plus CC BY 4.0 annotations**; copyright-restricted translations are excluded
(see Composition → Exclusions).

---

## Motivation

**For what purpose was the dataset created?**
CANONCITE evaluates whether retrieval-augmented and generative systems **cite
the right canonical unit** when answering questions grounded in a fixed,
citable corpus. The central object is the *citation* (e.g. Bhagavad Gita `2.47`,
`Genesis 1:1`, Dhammapada `1.1`), not free-text answer quality. It measures
attribution faithfulness: Citation Existence Rate (does the cited id exist?),
Citation Groundedness (was it retrieved?), Attribution P/R/F1 (exact and
span-tolerant), Misattribution Rate, Near-miss Misattribution Rate, and
abstention behavior on unanswerable questions.

**Explicitly NOT a purpose:** CANONCITE makes *textual-attribution* judgments.
It is **not** an authority on the doctrine, theology, or correct interpretation
of any tradition, and gold answers are not endorsements of any interpretive
position.

**Who created it and for whom?** Built by the Shastra / Scripture-RAG research
effort as an open benchmark for the NLP/IR community.

---

## Composition

**What do instances represent?** Two coupled layers:

1. **Corpus layer** (`corpora/<corpus>/corpus_index.jsonl`): the citable text
   units — one JSON record per unit — carrying a canonical `id`, original-script
   text and/or public-domain English, transliteration, token count, and full
   per-field provenance (`translation_source`, `original_source`,
   `source_urls`, `retrieved`).
2. **Item layer** (`items/<corpus>/seed_candidates.jsonl`): benchmark questions.
   Each item carries `question`, `question_type`
   (factual / retrieval / conceptual / interpretive / unanswerable), `ambiguity`,
   `gold_citations` (⊆ the corpus id space), `near_miss_distractors`,
   `gold_answer`, `must_abstain`/`abstain_reason` for unanswerables,
   `answer_support`, and a trilingual `translations` block.

**How many instances?**

| Corpus | Tradition | Native lang / script | Units | EN coverage | Items |
|---|---|---|---:|---:|---:|
| bhagavad_gita | Hindu | Sanskrit / Devanagari | 701 | 99.9% | 82 |
| bible | Christian | English / Latin | 31,095 | 100% | 80 |
| constitution_india | Secular-legal | English / Latin | 1,219 | 100% | 70 |
| dhammapada | Buddhist | Pali / Latin | 423 | 100% | 60 |
| guru_granth_sahib | Sikh | Punjabi / Gurmukhi | 60,555 | 0% (excluded) | 60 |
| mahabharata | Hindu | Sanskrit / Devanagari | 73,816 | 0% (excluded) | 40 |
| ramayana | Hindu | Sanskrit / Devanagari | 18,761 | 0% (excluded) | 60 |
| thirukkural | Tamil-ethical | Tamil / Tamil | 1,330 | 100% | 70 |
| upanishads | Hindu | Sanskrit / Devanagari | 462 | 90% | 50 |
| yoga_sutras | Hindu | Sanskrit / Devanagari | 195 | 99.5% | 50 |
| **Total** | 5 traditions | 5 scripts | **188,557** | — | **622** |

**Is this a sample or the whole?** The corpus layer is the *complete* frozen
canonical text for each source edition. The item layer is a curated sample of
questions per corpus (v0 seed set).

**What data does each instance contain?** See Composition above. Corpus text is
verbatim from public-domain editions; questions/answers are original
annotations.

**Are there labels?** Yes — `gold_citations` are the ground-truth attributions.
Item integrity is machine-enforced: every gold/near-miss id must exist in the
corpus id space `U`, unanswerable items must carry an empty gold set, etc.
(`canoncite/items.py::validate_item`).

**Exclusions (what is deliberately NOT here).** Copyright-restricted English
translations are removed from the public release and kept private:
- **Guru Granth Sahib** — Dr. Sant Singh Khalsa English (copyrighted, US term to
  ~2096). Released as **Gurmukhi original only**.
- **Ramayana** — IIT-Kanpur English (copyrighted); Griffith's public-domain
  English could not be aligned to the shloka grid. Released as **Sanskrit only**.
- **Mahabharata** — Ganguli's public-domain English exists but does not align to
  the critical-edition shloka grid, so it is excluded from the released text
  layer. Released as **Sanskrit only**.

This mirrors the policy applied to the BBT/Prabhupada Gita translation (not
used anywhere). The build script (`build_release.py`) enforces the exclusions:
it aborts if any `*.with_english.private.jsonl`, `text_en_supplement.jsonl`,
`VALIDATION_EN.md`, or `raw/` cache is present, if any record's
`translation_source` is off the public-domain allowlist, or if an
excluded-English corpus ships any English text.

**Confidential / offensive data?** No PII. The texts are religious and legal
canon of multiple *living* traditions and must be treated as sensitive (see
Ethics under Uses).

---

## Collection process

**How was the data acquired?** The corpus text was fetched from documented
public-domain digitizations (GRETIL, SuttaCentral, Wikisource, Project
Gutenberg, sacred-texts.com, GurbaniNow/BaniDB, gita open dataset,
Government-of-India constitution text). Every record records its
`source_urls`, `translation_source`/`original_source`, and `retrieved` date;
per-corpus `VALIDATION.md` files carry the sha256 of the frozen index and the
alignment/coverage notes.

**How were the items produced?** A two-stage pipeline, *not* scraping:
1. **LLM-seeded.** Candidate questions were drafted by an LLM conditioned on the
   corpus units (`provenance.seed = "claude_drafted"`).
2. **Human-verified.** Candidates are reviewed/adjudicated by annotators with
   relevant language and tradition literacy; verification status is tracked
   (`provenance.verified`, `adjudicated`). **The v0 release ships the
   pre-review seed candidates (`seed_candidates.jsonl`); post-review
   `gold.jsonl` will replace them in a later cut.**

**Translations.** The trilingual layer (English base + Hindi + the corpus's
native language) was produced by machine translation — **IndicTrans2** and
**Claude** (`provenance.trans_engine`, e.g. `{"hi": "indictrans2", "sa":
"indictrans2"}`) — with human verification tracked via `trans_verified`. Gold
*citations* are language-independent; only the surface `question`/`gold_answer`
strings are translated.

---

## Preprocessing / cleaning / labeling

- **Canonical id assignment.** Each unit gets a stable, edition-anchored id
  (e.g. Gita `chapter.verse`, Bible `Book chap:verse`, GGS `ang.line`,
  Mahabharata `parva.adhyaya.shloka`). Ids are unique within each corpus.
- **Script normalization.** Devanagari originals for some Sanskrit corpora are
  produced by deterministic, lossless IAST→Devanagari transliteration of the
  fetched GRETIL text (same text, second script — not re-sourced).
- **Tuk-level segmentation** for the Guru Granth Sahib (the citable line is the
  danda-terminated *tuk*, sequentially numbered — see its `VALIDATION.md`).
- **Alignment honesty.** Where a public-domain English translation could not be
  aligned to the canonical grid, `text_en` is left `null` rather than
  fabricating verse boundaries (Ramayana, Mahabharata).
- **Frozen indexes.** The released `corpus_index.jsonl` files are frozen; the
  raw fetch caches (`raw/`) are retained privately but **excluded** from the
  release.

---

## Uses

**What is it for?** Evaluating **citation-attribution faithfulness** of
RAG/LLM systems over canonical corpora: given a question and a retrieval set,
did the system cite ids that (a) exist, (b) were retrieved, and (c) actually
support the answer — and did it abstain when it should?

**What should it NOT be used for?**
- **Not doctrinal or theological authority.** Gold answers are textual-locator
  judgments, not rulings on the correct interpretation of scripture for any
  tradition. Do not use CANONCITE to adjudicate religious questions.
- Not a translation-quality benchmark (the multilingual layer is
  machine-translated and only partially human-verified).
- Not a claim that one tradition's framing is privileged over another's.

**Known biases and limitations.**
- **Translation choice.** English gold text is anchored to specific
  public-domain editions (Besant, Müller SBE, Pope 1886, Vivekananda/Woods, WEB).
  These carry the diction, theology, and era of their translators; a different
  edition could phrase — and thus locate — an answer differently.
- **Machine-translation artifacts.** Hindi/native translations come from
  IndicTrans2 + Claude and may contain errors where not yet human-verified.
- **Annotator worldview on interpretive items.** For `interpretive` (and some
  `conceptual`) questions, "the" supporting citation can be genuinely
  contested. These items reflect annotator judgment; the `ambiguity` field
  surfaces contestedness rather than hiding it, and interpretive gold is treated
  as a *defensible set* rather than a single forced-correct answer.
- **Coverage asymmetry.** Three corpora ship original-script only (English
  excluded for copyright/alignment reasons), so cross-lingual English↔native
  evaluation is not uniform across corpora.
- **Copyrighted-translation exclusion.** Because the widely-used copyrighted
  English translations (Sant Singh Khalsa GGS, IIT-K Ramayana, BBT Gita) are
  deliberately excluded, results on those corpora reflect original-script
  retrieval only and are not comparable to systems using those translations.

---

## Distribution

**How is it distributed?** As a self-contained bundle (`canoncite-v0/`) suitable
for HuggingFace Datasets and arXiv: per-corpus `corpus_index.jsonl` +
`seed_candidates.jsonl` + `VALIDATION.md`, and a top-level `manifest.json` with
per-corpus counts, per-file sha256, sources, and licenses.

**License.** Annotations/questions (the item layer) under **CC BY 4.0**. Corpus
text is **public-domain per source**; see `LICENSE`/`NOTICE` for the exact
editions. Copyrighted English translations are excluded.

---

## Maintenance

**Who maintains it?** The Shastra / Scripture-RAG maintainers
(contact: the repository owner).

**Will it be updated?** Yes. The immediate planned change is replacing the v0
`seed_candidates.jsonl` with human-adjudicated `gold.jsonl` after
double-annotation and inter-annotator-agreement reporting. Corpus indexes are
frozen and versioned by sha256 (see each `VALIDATION.md` and `manifest.json`);
any change ships as a new version.

**Erratum / contribution.** Corrections (mis-id, mis-alignment, translation
fixes) are welcome via the repository. Provenance and per-file hashes make
verification reproducible.
