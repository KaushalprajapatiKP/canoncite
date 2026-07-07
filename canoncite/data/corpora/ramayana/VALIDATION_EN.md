# VALIDATION_EN -- English text supplement for Valmiki Ramayana (CANONCITE)

Companion to `VALIDATION.md`. Retrieved / built: **2026-06-30**.

This documents `text_en_supplement.jsonl`, a **separate** sidecar that adds per-shloka
English to the Sanskrit corpus **without modifying** the validated `corpus_index.jsonl`
(whose `text_en` stays `null`). Join the two by `id` (`kanda.sarga.shloka`).

- **supplement file:** `text_en_supplement.jsonl`
- **sha256:** `16d302e5df22d86aeceeee0c8dfcfda7bfef306b31e860614dacbc77799ff061`
- **rows:** 14,464 (one per aligned Baroda-CE id; ids not present here remain English-`null`)

## Supplement row schema

```json
{"id":"1.1.1","text_en":"Ascetic Valmiki enquired of Narada ...","translation_source":"IITK",
 "source_url":"https://raw.githubusercontent.com/AshuVj/Valmiki_Ramayan_Dataset/main/data/Valmiki_Ramayan_Shlokas.json",
 "align_confidence":"high","iitk_id":"1.1.1","align_ratio":1.0,
 "translation_provenance":"IIT-Kanpur GitaSupersite ... aligned to Baroda CE id by verse-content matching"}
```

`iitk_id` = the id of the matched verse **in the source (vulgate) numbering**; it usually
differs from `id` (see edition mismatch below). `align_ratio` = normalized-IAST similarity
of the two verses (1.0 = identical content).

## Source(s) used

| Field | Source | URL |
|---|---|---|
| `text_en` | **IIT-Kanpur "GitaSupersite" Valmiki Ramayana** running English translation (per-shloka), retrieved via the **MIT-licensed mirror** `AshuVj/Valmiki_Ramayan_Dataset` (`data/Valmiki_Ramayan_Shlokas.json`, 23,291 shlokas). The English used is that dataset's `explanation` field (clean prose translation); its `translation` field is a word-by-word gloss and was **not** used. | https://github.com/AshuVj/Valmiki_Ramayan_Dataset ; source portal https://www.valmiki.iitk.ac.in/ |

Raw sources cached under `raw/english/`:
- `AshuVj_Valmiki_Ramayan_Shlokas.json` (29.5 MB) -- the per-shloka IITK-derived data actually used.
- `dutt_vol1-2_bala_ayodhya.txt`, `dutt_vol3-5_aranya_kishkindha_sundara.txt`, `dutt_vol6_yuddha.txt`, `dutt_vol7_uttara.txt` -- M. N. Dutt 1891-94 OCR full text (archive.org), evaluated but **not** used for per-shloka alignment (see below).

### Honesty note on provenance / licence

The English is **IIT-Kanpur GitaSupersite** scholarly translation, mirrored under MIT by a third
party. The task brief explicitly lists `valmiki.iitk.ac.in` as an accepted per-shloka source, so
this satisfies the brief, but it is **not** a strictly public-domain text the way M. N. Dutt (1891)
or Griffith (1870) are. `translation_source` is therefore set to `"IITK"`, never `"Dutt_1891"`.
Nothing here is machine-translated or fabricated -- every `text_en` is a real fetched human
translation of that verse.

### Why M. N. Dutt (public-domain) was *not* used for per-shloka alignment

Dutt's 1891-94 prose (the canonical PD choice, downloaded and cached in full) renders each
**Section (= sarga) as one continuous prose passage with no per-shloka numbers or boundaries** --
the same alignability problem as Griffith, only in prose. Its opening Section I already fuses
Baroda 1.1.1-1.1.3 into one paragraph. Per-shloka boundaries are unrecoverable from Dutt without
fabricating them, so Dutt is unusable at shloka granularity. (It also follows the vulgate
recension, and the archive.org OCR of Vol. 7 Uttara is truncated to ~24 of ~100 sargas.) Dutt
remains cached for a future *sarga-level* English layer.

### Why not valmiki.iitk.ac.in directly / Griffith

- **Direct IITK fetch failed:** `www.valmiki.iitk.ac.in` currently CNAMEs to `gitasupersite.iitk.ac.in`
  and returns empty replies (HTTP 000) with a mismatched TLS cert (`ai.sugyapt.co.in`). The
  AshuVj mirror is a snapshot of the same IITK data and was used instead.
- **Griffith** (already covered in `VALIDATION.md`) is poetic canto-level verse, not shloka-alignable. Skipped.

## Coverage summary

- Total citable shlokas (Baroda CE): **18,761**
- English `text_en` aligned: **14,464 = 77.1%** (remaining 22.9% left `null` -- not fabricated)
- Confidence: **high 11,460** (exact verse-content identity) / **medium 3,004** (high-similarity, ratio 0.86-0.97; chiefly minor orthographic or verse-merge differences)

### Per-kanda alignment coverage

| # | Kanda | Aligned / Total | % |
|---:|---|---:|---:|
| 1 | Bala | 1,507 / 1,941 | 77.6% |
| 2 | Ayodhya | 2,622 / 3,160 | 83.0% |
| 3 | Aranya | 1,568 / 2,060 | 76.1% |
| 4 | Kishkindha | 1,518 / 1,987 | 76.4% |
| 5 | Sundara | 1,836 / 2,488 | 73.8% |
| 6 | Yuddha | 3,343 / 4,436 | 75.4% |
| 7 | Uttara | 2,070 / 2,689 | 77.0% |
| | **total** | **14,464 / 18,761** | **77.1%** |

## Edition-mismatch notes (critical)

Our corpus is the **Baroda Critical Edition** (18,761 shlokas, 606 sargas). The IITK/GitaSupersite
source follows the longer **Northern/vulgate (Gita Press) recension** (23,291 shlokas). They are
the *same poem* but with **different sarga and shloka numbering** -- the vulgate inserts extra
verses, so identical numbers rarely denote the same verse:

- Only **2.2%** of ids carry the *same* verse under the *same* `kanda.sarga.shloka` number.
- About **40%** of our verses appear verbatim somewhere in the source under a *different* number;
  another ~37% match with minor orthographic/sandhi variation.

Therefore alignment was done by **verse content, not by id number**. Method:
1. Normalize each verse's IAST to a sandhi-tolerant signature (strip diacritics/spaces/punct,
   drop visarga-`h`, unify nasals `m/n`, collapse doubled letters).
2. Per kanda, lock **anchors** = signatures that are unique on both sides and identical
   (rock-solid 1:1 verse matches), kept strictly monotonic.
3. **Gap-fill** the verses between consecutive anchors by best fuzzy signature similarity
   (`difflib` ratio), monotonic, threshold 0.86; >=0.97 -> `high`, else `medium`.

This makes drift self-correcting: alignment tracks the verse even as numbers diverge (e.g. our
`6.34.11` -> IITK `6.44.11`; our `7.50.16` -> IITK `7.51.27`). The unaligned 22.9% are verses
genuinely absent/heavily reworded in the other recension, or where the local order could not be
resolved safely -- these are left `null` rather than guessed.

**Caveat on `medium`:** the source occasionally merges 2+ shlokas into one entry, so a `medium`
row's English may cover a span slightly larger than the single Baroda shloka. All sampled medium
rows nonetheless point to the correct verse (see spot-check).

## 5-shloka spot-check (Sanskrit id + the actual English fetched)

Each shows the Baroda id, the source verse number it aligned to, and the verbatim `text_en`.

**1.1.1** (high, iitk_id 1.1.1)
- IAST: `tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam nāradaṃ paripapraccha vālmīkir munipuṃgavam`
- text_en: "Ascetic Valmiki enquired of Narada, preeminent among the sages ever engaged in the practice of religious austerities or study of the Vedas and best among the eloquent."

**3.1.1** (high, iitk_id 3.1.1)
- IAST: `praviśya tu mahāraṇyaṃ daṇḍakāraṇyam ātmavān dadarśa rāmo durdharṣas tāpasāśramamaṇḍalam`
- text_en: "The invincible and selfpossessed Rama entered the great forest of Dandaka and saw there a multitude of hermitages of the ascetics."

**5.1.1** (high, iitk_id 5.1.1)
- IAST: `tato rāvaṇanītāyāḥ sītāyāḥ śatrukarśanaḥ iyeṣa padam anveṣṭuṃ cāraṇācarite pathi`
- text_en: "Hanuman, crusher of enemies resolved to find the whereabouts of Sita, carried away by Ravana. He followed the path of the Charanas, celestial bards."

**6.34.11** (medium, ratio 0.957, iitk_id 6.44.11 -- note sarga renumbering)
- IAST: `vartamāne tathā ghore saṃgrāme lomaharṣaṇe rudhirodā mahāvegā nadyas tatra prasusruvuḥ`
- text_en: "In that way as the war was going on, and rivers of blood flowing with the terrific noise it made hair stand on end."

**7.1.1** (high, iitk_id 7.1.1)
- IAST: `prāptarājyasya rāmasya rākṣasānāṃ vadhe kṛte ājagmur ṛṣayaḥ sarve rāghavaṃ pratinanditum`
- text_en: "After Rama had attained his kingdom and the destruction of the Rakshasas was accomplished, all the sages came to congratulate Raghava."

## Reproduce

`raw/english/` holds the fetched sources. The alignment script
(`scratchpad/align2.py` at build time) reads `corpus_index.jsonl` + the cached AshuVj JSON and
writes `text_en_supplement.jsonl` deterministically; no network needed to reproduce from cache.
