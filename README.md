# CANONCITE

**Does an AI cite the *right* verse — or just a confident, wrong one?**

CANONCITE is a benchmark and a method for **canonical-citation attribution**: measuring
and reducing the rate at which retrieval-augmented systems misattribute answers to the
*wrong* chapter/verse/article of a canonical text. It spans ten public-domain corpora,
five scripts, and three query languages (English / Hindi / native script) — and it isolates
a concrete failure mode (cross-lingual retrieval **ranking**, not reasoning) plus a method
that fixes the residual error other approaches can't.

> **Status: research in progress.** Core findings are empirically validated at scale (see
> below); the paper draft, dataset, and packaging are being finalized before submission.
> Not yet published to arXiv or HuggingFace.

---

## The headline result

Canonical texts cite **discrete, checkable IDs** (`BG 2.47`, `John 3:16`, `Art. 19(1)(a)`) —
so, unlike open-domain faithfulness (which needs NLI/LLM judges to *approximate* "is this
grounded?"), misattribution here is **automatically and exactly verifiable**: either the
cited ID is the right one, or it isn't.

Running the full system ladder (naive RAG → hybrid → reranking → a reproduced SOTA →
**our method**) across all ten corpora, cross-lingually:

| System | Cross-lingual Attribution F1 ↑ | Cross-lingual Misattribution Rate ↓ | Cost |
|---|---:|---:|---:|
| Naive RAG (BM25) | 0.173 | 0.470 | 1 LLM call/item |
| Hybrid (BM25 + dense) | 0.416 | 0.446 | 1 |
| Reranking (cross-encoder) | 0.404 | 0.482 | 1 |
| Reproduced SOTA (Self-RAG + CRAG) | **0.440** | 0.443 | ~10 |
| **Ours — E2 (joint discriminative exact-ID select)** | 0.423 | **0.387** | ~2 |

**Findings:**
1. The cross-lingual attribution collapse (English F1 ~0.70, cross-lingual ~0.17 under naive
   retrieval) is a **retrieval-ranking failure, not a reasoning failure** — the correct verse
   is usually *retrieved*, just ranked below the top-k the reader sees.
2. Once ranking is fixed, residual errors are dominated by **near-misses** (citing an
   adjacent, same-theme verse) — which a topical reranker and a binary verifier structurally
   cannot resolve.
3. Our method — showing the reader all reranked candidates *jointly* and forcing one exact
   choice or abstention — **passes its pre-committed gate**: lowest cross-lingual
   misattribution of any system, at ~1/5 the inference cost of the reproduced SOTA.
4. Every system has **CER = 1.000 / MAR-exist = 0.000** everywhere — no system ever cites a
   *non-existent* verse. All error is confident citation of a real-but-wrong one, which is why
   exact-ID discrimination (not existence-checking) is the effective intervention.

Full methodology, tables, and per-corpus breakdowns: [`paper/canoncite.md`](paper/canoncite.md).

---

## The dataset

**188,557 citable units across 10 public-domain corpora and 5 scripts**, each with a closed
canonical-ID space, a multilingual text triple (English + original script + transliteration
where applicable), and 622 seed benchmark items (trilingual: English + Hindi + native
language).

| Corpus | Tradition | Script | Units |
|---|---|---|---:|
| Bhagavad Gita | Hindu | Sanskrit (Devanagari) | 701 |
| Upanishads | Hindu | Sanskrit (Devanagari) | 462 |
| Yoga Sūtras | Hindu | Sanskrit (Devanagari) | 195 |
| Rāmāyaṇa | Hindu | Sanskrit (Devanagari) | 18,761 |
| Mahābhārata | Hindu | Sanskrit (Devanagari) | 73,816 |
| Dhammapada | Buddhist | Pali | 423 |
| Thirukkuṟaḷ | Tamil-ethical | Tamil | 1,330 |
| Guru Granth Sahib | Sikh | Gurmukhi | 60,555 |
| Constitution of India | Secular-legal | English / Hindi | 1,219 |
| Bible (WEB) | Christian | English | 31,095 |

Only public-domain editions are released (copyrighted translations — e.g. Sant Singh
Khalsa's Guru Granth Sahib, BBT's Gita — are used privately for annotation only and never
shipped). Full provenance, sha256 hashes, and per-corpus validation notes: manifest in
[`canoncite/CORPORA.md`](canoncite/CORPORA.md).

---

## Repo layout

```
canoncite/                 benchmark harness + systems (the core code)
├── metrics.py, eval.py, ids.py, items.py, corpus_io.py   — metric suite (CER, CG, Attribution P/R/F1, MAR, NMR, abstention)
├── corpus/                per-corpus builders (build_<corpus>.py)
├── data/corpora/<c>/      frozen corpus_index.jsonl + VALIDATION.md per corpus
├── data/items/<c>/        seed benchmark items (trilingual)
├── seed/                  LLM-assisted item seeding + translation tooling
├── systems/                five RAG system implementations (A naive, B hybrid, C rerank, D SOTA repro, E/E2 ours)
├── agreement/              reviewer agreement stats + gold adjudication
├── review/webapp/          human-review web app (Vercel + Supabase)
└── tests/                  20+ unit tests, stdlib-only for the metric core

paper/canoncite.md         the research paper draft (working format; see note below)
release/                   HuggingFace release builder (public-domain gate, datasheet, license)
results/gpu_qwen14b/        experiment outputs (per-system, per-corpus, per-language JSONL/MD)
PRODUCTS.md                 the 5-product roadmap this research feeds (dataset, paper, demo, OSS lib, commercial vertical)
product/live-app-plan.md    build plan for the public-facing demo
ENGINEERING_LOG.md          step-by-step build narrative of the systems (B/C/D/E/E2)
BENCHMARK_DESIGN.md, RESEARCH_PLAN.md, RELATED_WORK*.md   design + prior-art documents
```

**Note on the paper format.** `paper/canoncite.md` is the working draft in Markdown for fast
iteration. Submission to arXiv/ACL/NeurIPS requires converting it into their LaTeX template
(`acl.cls` / `neurips.sty`) — that conversion happens once the remaining empirical tables
(multi-reader robustness, inter-annotator agreement) are filled in.

---

## Reproducing results

```bash
# metric harness tests (stdlib only, no deps)
PYTHONPATH=. python -m pytest canoncite/tests -q

# run a system over a corpus (needs an OpenAI-compatible LLM endpoint — see canoncite/seed/.llm.env)
PYTHONPATH=. python -m canoncite.systems.sweep --system C --reader llm --k 5 \
    --checkpoint results/my_run.jsonl --out results/my_run.md
```

Dense retrieval (Systems B/C/D/E2) needs `sentence-transformers` + `faiss-cpu` and benefits
from a GPU; the metric harness itself has zero dependencies. See
[`canoncite/README.md`](canoncite/README.md) for the metric suite in detail and
[`ENGINEERING_LOG.md`](ENGINEERING_LOG.md) for how each system was built and validated.

---

## Roadmap — 5 products from this research

This benchmark and method feed five distinct outputs (full detail in
[`PRODUCTS.md`](PRODUCTS.md)):

| # | Product | Status |
|---|---|---|
| 1 | **Dataset** (HuggingFace release) | 🟡 Built, not published — needs final human-verified gold |
| 2 | **Research paper** | 🟡 Draft complete, empirical numbers landing |
| 3 | **Public demo** ("ask it, get the right verse cited") | 🔴 Engine done, front-end to build |
| 4 | **OSS method + library + leaderboard** (generalizes beyond scripture — law, medicine) | 🔴 Core code exists, packaging unbuilt |
| 5 | **Commercial vertical** (citation-correct RAG API for high-stakes domains) | 🔴 Concept |

---

## License

Code: MIT (see [`LICENSE`](LICENSE)). Released corpus text: public domain per source.
Annotations/questions: CC BY 4.0. See [`release/DATASHEET.md`](release/DATASHEET.md) for
full dataset licensing and exclusions.

## Ethics note

This benchmark spans multiple living traditions (Hindu, Buddhist, Sikh, Tamil-ethical,
Christian) plus a nation's constitution. It is scoped strictly as a **textual-attribution
faithfulness instrument** — gold answers are citation-locator judgments, not endorsements of
any doctrinal or theological position. Each tradition is treated with equivalent care; none
is privileged.
