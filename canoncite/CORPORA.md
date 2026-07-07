# CANONCITE — Corpora Manifest

Released corpus data layer (public-domain text only). Generated from the frozen `corpus_index.jsonl` files.

| Corpus | Tradition | Lang/script | Units | EN% | Orig% | Sample id |
|---|---|---|---:|---:|---:|---|
| **bhagavad_gita** | Hindu | Sanskrit (Devanagari) | 701 | 99% | 100% | `1.1` |
| **bible** | Christian | English | 31,095 | 100% | 0% | `Genesis 1:1` |
| **constitution_india** | Secular-legal | English (legal) | 1,219 | 100% | 0% | `Preamble` |
| **dhammapada** | Buddhist | Pali | 423 | 100% | 100% | `1.1` |
| **guru_granth_sahib** | Sikh | Gurmukhi | 60,555 | 0% | 100% | `ang.1.1` |
| **mahabharata** | Hindu | Sanskrit (Devanagari) | 73,816 | 0% | 100% | `1.1.0` |
| **ramayana** | Hindu | Sanskrit (Devanagari) | 18,761 | 0% | 100% | `1.1.1` |
| **thirukkural** | Tamil/ethical | Tamil | 1,330 | 100% | 100% | `1` |
| **upanishads** | Hindu | Sanskrit (Devanagari) | 462 | 90% | 78% | `isha.1` |
| **yoga_sutras** | Hindu | Sanskrit (Devanagari) | 195 | 99% | 100% | `1.1` |

**Total: 188,557 citable units across 10 corpora, 5 scripts.** All IDs unique within each corpus.

### Notes
- **English kept private (copyright)**: Guru Granth Sahib (Sant Singh Khalsa) and Ramayana (IIT-K) — released as original-script/Sanskrit only; English available privately for annotation/robustness. Same policy as the BBT Gita translation.
- **Sanskrit-only release**: Ramayana, Mahabharata (no per-shloka public-domain English aligns to the critical edition; Mahabharata ships 699 Gita-zone English verses from Besant, PD).
- **English-only**: Bible, Constitution of India (no separate original layer).
- Per-corpus provenance, coverage, flagged gaps, and sha256 hashes are in each corpus's `VALIDATION.md`.
