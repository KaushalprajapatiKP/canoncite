# VALIDATION_EN -- English alignment for the Mahabharata corpus (CANONCITE)

Generated 2026-06-30. Companion to `VALIDATION.md`. Documents the attempt to add public-domain
English (`text_en`) to the BORI critical-edition Sanskrit index (73,816 shlokas).

**Output is a SEPARATE supplement** (`text_en_supplement.jsonl`); `corpus_index.jsonl` is NOT edited.
Supplement record shape:
`{"id","text_en","translation_source","granularity":"shloka|section","source_url","align_confidence"}`.

## Headline result (honest)

| Granularity | Shlokas aligned | % of 73,816 |
|---|---:|---:|
| **shloka** (per-verse, verified) | **699** | **0.95%** |
| section | 0 | 0.00% |
| **left null** (no honest alignment) | **73,117** | **99.05%** |

(700 Gita shlokas are in range; **1** -- `6.40.33` = Gita 18.33 -- is left unaligned because the
source Besant text for that verse is missing, so it is dropped rather than emitted as null.)

Per-shloka English was added **only for the Bhagavad Gita zone (parva 6, adhyayas 23-40)** -- the
single region where the BORI critical-edition numbering and a clean, verse-aligned public-domain
English translation cleanly correspond. The remaining **99%** is left null on purpose: with the
available PD sources it cannot be aligned per-shloka (or reliably per-section) **without fabricating
alignment**, which the build rules forbid.

## Sources

| Source | Status | Why |
|---|---|---|
| **Annie Besant**, *The Bhagavad-Gita*, 4th ed. 1905 (Wikisource; PUBLIC DOMAIN) | **USED** (Gita zone) | Clean, verse-aligned; matches BORI Gita verse-for-verse |
| **M.N. Dutt**, *Prose English Translation of the Mahabharata*, 1895-1905 (archive.org; PD) | Evaluated, not used | Only scanned/OCR page-images, not machine-fetchable per-verse; Calcutta-vulgate numbering != BORI |
| **K.M. Ganguli**, 1883-96 (sacred-texts.com /hin/maha/; PD) | Evaluated, not used per-shloka | Section-level prose on the vulgate; no verified section<->adhyaya concordance |

Provenance is carried in `text_en_supplement.jsonl` (`translation_source`, `source_url`) and cached
under `raw/english/` (`gita_besant_aligned.json` = all 700 aligned rows; `SOURCES_NOTES.md` = source
evaluation). Besant's per-discourse Wikisource URLs are the `source_url` of each record.

> Provenance honesty: the Gita English is **Besant 1905**, so `translation_source` is `"Besant_1905"`,
> not the suggested `"Dutt"`/`"Ganguli"`. Labelling Besant text as Dutt would fabricate provenance.
> Besant 1905 is public domain. (Dutt's own Gita is verse-by-verse PD too, but exists only as OCR
> scans; the in-repo Besant text is clean and already verified against our Sanskrit.)

## How the Gita zone was aligned and verified (nothing assumed)

1. **Numbering coincidence found.** Shloka counts for adhyayas 23-40 of Bhishma parva are
   47,72,43,42,29,47,30,28,34,42,55,20,34,27,20,24,28,78 = **700**, i.e. the standard Gita chapter
   counts. So adhyaya `A` = Gita chapter `A-22`, and (almost always) shloka `N` = Gita verse `N`.
2. **Chapter 13 off-by-one handled.** The `bhagavad_gita` corpus includes the disputed opening verse
   13.1 (`arjuna uvāca prakṛtiṃ puruṣaṃ caiva...`) -> 35 verses; BORI omits it -> 34 shlokas
   (6.35 starts `śrībhagavān uvāca idaṃ śarīraṃ kaunteya...`). Mapping for ch13 uses `gita_verse =
   shloka + 1`. All other chapters use `gita_verse = shloka`.
3. **Content-verified, not positional.** Every one of the 700 shlokas was matched to its Gita verse
   by a script-independent **consonant skeleton** (NFKD strip diacritics, drop vowels/aspiration,
   normalise nasals) with a similarity ratio. **Mean ratio 0.991.** Of 699 emitted: 684 >= 0.85 ->
   `high`; 15 < 0.85 -> `medium`. (Verse 6.40.33 dropped -- missing in the source English.)
4. **The 15 `medium` cases are still the correct verse** -- they are well-known half-line split
   points where BORI and the Besant/vulgate text break a shloka at a slightly different half-verse
   (e.g. 1.6, 1.27, 2.42, 18.36 where the Besant entry merges the following half-line), or (11.19) a
   corrupt transliteration *field* in the source whose English nonetheless matches. The English still
   covers the shloka's content; confidence is lowered only to flag the boundary nuance. None were
   dropped or mis-mapped.

## Per-parva coverage

Only parva 6 (Bhishma) receives English, and within it only adhyayas 23-40.

| Parva | Shlokas | EN aligned | Granularity |
|---:|---|---:|---|
| 6 bhishma | 5,406 | 699 (adh. 23-40 only) | shloka |
| all other 17 parvas | 68,410 | 0 | -- (null) |

Within parva 6: 699/5,406 = 12.9% of Bhishma parva; 0% of the other 16 adhyayas/4,706 shlokas of
that parva (war narrative, not the Gita).

## Edition-mismatch analysis (why the other 99% is not alignable)

The Sanskrit ids follow the **BORI / Poona critical edition**. Both PD English translations follow
the **Calcutta vulgate**, a different recension. Hard evidence -- **Ganguli section counts
(sacred-texts cached indices) vs BORI adhyaya counts** diverge in nearly every parva:

| Parva | BORI adhyayas | Ganguli sections | Δ |
|---:|---:|---:|---:|
| 1 adi | 225 | 236 | +11 |
| 2 sabha | 72 | 80 | +8 |
| 3 vana | 299 | 313 | +14 |
| 4 virata | 67 | 72 | +5 |
| 5 udyoga | 197 | 199 | +2 |
| 6 bhishma | 117 | 125 | +8 |
| 7 drona | 173 | 199 | +26 |
| 8 karna | 69 | 96 | +27 |
| 9 shalya | 64 | 65 | +1 |
| 10 sauptika | 18 | 18 | 0 |
| 11 stri | 27 | 26 | -1 |
| 12 shanti | 353 | 364 | +11 |
| 13 anushasana | 154 | 168 | +14 |
| 14 ashvamedhika | 96 | 92 | -4 |
| 15 ashramavasika | 47 | 39 | -8 |
| 16 mausala | 9 | 8 | -1 |

(Ganguli indices for parvas 17-18 were not cached; counts above are from the 16 cached index pages.)

Because section count != adhyaya count almost everywhere, **Ganguli section S does not equal BORI
adhyaya S**, the offset drifts cumulatively within a parva, and Ganguli prose is not numbered per
shloka at all. There is no verified concordance. Mapping any section to an adhyaya/shloka without
one would invent boundaries -> excluded. (The Gita zone escapes this only because the Gita is an
independently-transmitted text the critical edition keeps intact with the canonical 700-verse count.)

Dutt is verse-numbered but (a) only exists as OCR page-scans, not machine-fetchable per verse, and
(b) carries the same vulgate-vs-BORI numbering divergence. Evaluated, not used.

## 5-shloka spot-check (actual aligned English in the supplement)

| id | Gita ref | conf | text_en (Besant 1905) |
|---|---|---|---|
| 6.23.1 | BG 1.1 | high | "Dhritarâshtra said: On the holy plain, on the field of Kuru, gathered together, eager for battle, what did they, O Sanjaya, my people and the Pândavas?" |
| 6.24.47 | BG 2.47 | high | "Thy business is with the action only, never with its fruits; so let not the fruit of action be thy motive, nor be thou to inaction attached." |
| 6.31.1 | BG 9.1 | high | "The Blessed Lord said: To thee, the uncarping, verily shall I declare this profoundest Secret, wisdom with knowledge blended..." |
| 6.35.1 | BG 13.1(=13.2) | high | "The Blessed Lord said: This body, son of Kuntî, is called the Field; that which knoweth it is called the Knower of the Field..." (ch13 +1 offset) |
| 6.40.78 | BG 18.78 | high | "Wherever is Krishna, Yoga's Lord, wherever is Pârtha, the archer, assured are there prosperity, victory and happiness..." |

Cross-check: 6.23.1 here = `dharmakṣetre kurukṣetre...` (Gita 1.1); 6.40.78 = `yatra yogeśvaraḥ kṛṣṇo
yatra pārtho dhanurdharaḥ` (Gita 18.78, the final verse). Both Sanskrit and English line up.

## What could NOT be aligned (honest statement)

- **73,117 of 73,816 shlokas (99.05%)** have **no** `text_en` and are absent from the supplement
  (incl. `6.40.33`, dropped for missing source English).
- **All 17 non-Bhishma parvas** and the **4,706 non-Gita shlokas of Bhishma parva**: no per-shloka
  PD English. Dutt is the only verse-level PD option and it is neither cleanly machine-fetchable nor
  numbered to the BORI edition; Ganguli is section-level prose with no verified BORI concordance.
- **Section-level fallback was deliberately NOT produced** (0 records). Building it would require a
  validated Ganguli-section <-> BORI-adhyaya concordance, which does not exist (see mismatch table);
  emitting one would fabricate boundaries. It is left to a future version that builds AND validates
  such a concordance (or that OCR-aligns Dutt verse-by-verse against the vulgate, then bridges
  vulgate->BORI).
- Within the Gita zone, **15 verses are `medium` confidence** (half-line boundary differences), and
  the disputed Gita verse 13.1 has **no BORI counterpart** by design (correctly omitted, not faked).

## Reproducibility

Build is deterministic from two in-repo files (`bhagavad_gita/corpus_index.jsonl`,
`mahabharata/corpus_index.jsonl`) plus the cached Ganguli indices. No network text was fabricated;
the Gita English is the verified Besant 1905 text already cached in the repo and re-cached per-row
under `raw/english/gita_besant_aligned.json`.
