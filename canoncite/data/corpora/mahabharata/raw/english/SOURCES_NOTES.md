# English source evaluation -- Mahabharata CANONCITE (raw/english/)

Retrieved/evaluated: 2026-06-30. Purpose: source per-shloka public-domain English for the
BORI critical-edition Sanskrit index (`corpus_index.jsonl`, 73,816 shlokas).

## Sources evaluated

### 1. M.N. Dutt, *A Prose English Translation of the Mahabharata* (1895-1905) -- PUBLIC DOMAIN
The suggested "best per-verse" PD option. Dutt translates verse-by-verse, BUT:
- Only available as **scanned page-image / OCR volumes** on archive.org / HathiTrust, NOT as
  clean machine-readable per-verse text with reliable verse numbers. Per-shloka extraction at
  scale is not feasible by fetch, and OCR is noisy.
- Dutt follows the **Calcutta / vulgate** edition. Its adhyaya/verse numbering does NOT match the
  **BORI critical edition** numbering used for our Sanskrit ids (the critical edition removed
  ~28,824 apparatus/star lines as later interpolations and renumbered/merged adhyayas). So even a
  clean Dutt verse N of adhyaya M would not map to BORI `parva.adhyaya.shloka` outside zones whose
  numbering happens to coincide.
- Archive copies: https://archive.org/details/TheMahabharataMNDutt ,
  https://archive.org/details/in.ernet.dli.2015.134516 (Adi),
  https://archive.org/details/dli.ministry.04113 (Bhishma).
Conclusion: evaluated, NOT used (not machine-fetchable per-verse; edition mismatch).

### 2. K.M. Ganguli, *The Mahabharata* (1883-96), sacred-texts.com /hin/maha/ -- PUBLIC DOMAIN
Complete, but **SECTION-LEVEL prose** on the Calcutta vulgate. Sections do not correspond 1:1 to
BORI adhyayas (see edition-mismatch table in VALIDATION_EN.md: Ganguli section counts vs BORI
adhyaya counts diverge in nearly every parva, e.g. Karna 96 vs 69, Drona 199 vs 173, Adi 236 vs
225). No verified section<->adhyaya concordance exists. Used only as documented section-level
provenance in the base corpus (`source_urls.en`); NOT imported per-shloka here, to avoid
fabricating alignment boundaries. 18 parva index pages cached under `../ganguli/`.

### 3. Bhagavad Gita verse-aligned English -- USED for the Gita zone only
The Gita is a self-contained text whose 700-verse numbering the BORI critical edition preserves.
Our range **6.23-6.40** matches the standard 700-verse Gita chapter-for-chapter (47,72,43,42,29,
47,30,28,34,42,55,20,34,27,20,24,28,78 = 700). The repo's sibling `bhagavad_gita` corpus carries
clean, verse-aligned PD English (**Annie Besant, 4th ed., 1905**, from Wikisource). Every one of
the 700 verses was content-matched (scheme-independent consonant skeleton) to our Sanskrit before
mapping; mean similarity 0.991. This is the only zone where BORI ids and a clean PD verse-aligned
translation cleanly correspond.

`gita_besant_aligned.json` caches all 700 aligned rows (mbh id, gita id, skeleton-ratio, both IAST,
the English, source URL) -- the exact rows materialised into `../../text_en_supplement.jsonl`.

NOTE on provenance label: the supplement uses `translation_source:"Besant_1905"` (accurate origin),
which deviates from the suggested Dutt/Ganguli enum. Mis-labelling Besant text as "Dutt" would be
fabrication of provenance, which the build rules forbid above all. Besant 1905 is public domain.
