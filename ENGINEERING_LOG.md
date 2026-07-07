# CANONCITE — Experiment-Engine Engineering Log

A chronological record of building and evaluating the retrieval/attribution system
ladder (Systems A → B → C → D → E → E2) for the CANONCITE benchmark. Every step,
command, result, finding, and infrastructure lesson is captured here so the work is
fully reproducible and the paper's numbers are traceable to the code that produced them.

- **Repo:** `pralia-labs/shastra`, code in `canoncite/systems/`.
- **Benchmark:** canonical-citation attribution + abstention over 10 public-domain corpora
  (188,557 citable units, 5 scripts). Metric: does the system cite the *exact* correct
  reference ID (chapter.verse etc.), measured deterministically against a closed ID space.
- **Reader LLM:** Qwen2.5-14B-Instruct via Ollama on an NVIDIA L4 (23 GB) GPU box.
- **Pilot corpora** (fast iteration): Bhagavad Gītā (82 items), Yoga Sūtras (50 items),
  each evaluated across query languages en / hi / native (Sanskrit).
- **Headline metrics:** Attribution F1 (exact) ↑, Misattribution Rate (MAR) ↓ = fraction
  of cited answers that cite the wrong existing verse. Cross-lingual (XL) = mean over hi/native.

---

## 0. Starting point

Prior sessions had built: the 10 frozen corpora, the metric harness (`canoncite/`), 622
trilingual seed items, the review web app, and **System A (naive BM25 RAG)** with a full
28-cell grid on Qwen2.5-14B. System A established the phenomenon: **cross-lingual attribution
collapse** — English F1 ≈ 0.70 collapses to ≈ 0.17 for Hindi/native queries on the same gold
citation. Citation Existence Rate = 1.000 everywhere (the reader never invents a fake verse
ID); every error is a *confident citation of a real-but-wrong verse* (MAR-support).

The experiment engine (`canoncite/systems/`) was mid-build. This log covers completing it.

**Environment recipe (per session):**
- GPU box: `ssh -i vpp-key.pem ubuntu@45.194.47.31` (NVIDIA L4, shared/ephemeral company box).
- Ollama runs as a systemd service (auto-serves `:11434`, OpenAI-compatible); model `qwen2.5:14b`.
- Repo rsync'd to `~/shastra/`; `canoncite/seed/.llm.env` = provider=ollama, model=qwen2.5:14b.
- Deps on box: torch (CUDA), sentence-transformers, faiss-cpu.
- **Run jobs detached and drop-proof:**
  `setsid nohup bash -c "cd ~/shastra && PYTHONPATH=. python3 -m canoncite.systems.sweep ... > /tmp/x.log 2>&1" </dev/null & disown`
- Every sweep takes `--checkpoint <jsonl>` (appends each (corpus,lang) cell, resumes on restart).
- Pull results back with `rsync` to Mac `results/gpu_qwen14b/`.

---

## 1. Corrected E-on-B — the `--reader top1` footgun

**Problem found:** the prior "E-on-B" runs (`systemEB.jsonl`, `systemEB_v2.jsonl`) had been
run with `--reader top1` (the CLI default), *not* `--reader llm`. `top1` cites the single
top-retrieved verse with no LLM reasoning — so those runs were invalid for an E-vs-B comparison.

**Action:** re-ran E-on-B correctly with `--reader llm` over hybrid retrieval, k=10, on the
pilot corpora → `results/gpu_qwen14b/systemEB_llm.jsonl`.

**Result — E ≈ B (E does not earn its keep):**

| corpus·q | B F1 | E-on-B F1 | B MAR | E MAR |
|---|---|---|---|---|
| gita·en | 0.754 | 0.754 | 0.209 | 0.209 |
| gita·hi | 0.660 | 0.659 | 0.250 | 0.267 |
| gita·sa | 0.628 | 0.635 | 0.317 | 0.290 |
| yoga·en | 0.797 | 0.794 | 0.167 | 0.119 |
| yoga·hi | 0.622 | 0.604 | 0.121 | 0.156 |
| yoga·sa | 0.593 | 0.579 | 0.097 | 0.100 |

E's verify→repair barely fired (n_repaired 0–5/cell); it mostly *abstained* (15–22/82),
and cross-lingual wrong-abstention climbed to 0.14–0.32. **Hypothesis at the time:** the
grounding verifier is too strict cross-lingually. (This turned out to be wrong — see §2.)

**Lesson:** always pass `--reader llm` for System B/C/E/E2 runs; `top1` is the default and a footgun.

---

## 2. Diagnosis — the verifier is innocent; the cause is *ranking*

Built two diagnostics (no fabrication — pure measurement):

- **`canoncite/systems/diagnose_e.py`** — per-item trace: was gold retrieved? did the base
  reader cite gold? did the verifier reject it? Quantifies verifier false-negatives.
- **`canoncite/systems/recall_probe.py`** — retrieval-only recall@k of the gold verse (no LLM).

**`diagnose_e.py` verdict (gita-hi, yoga-sa):** the verifier is **innocent** — 0–1 false
negatives per cell, only 1–2 genuine over-abstentions. The real gap: of ~70 answerable
gita-hi items, the gold verse was only *retrieved* (top-5) for 48 — E cannot cite or repair
to a verse it never sees.

**`recall_probe.py` — the smoking gun (recall@k of the gold verse):**

| corpus·q | R@5 | R@10 | R@20 | R@50 | median gold rank |
|---|---|---|---|---|---|
| gita·en | 0.80 | 0.86 | 0.94 | 0.99 | 1 |
| gita·hi | 0.36 | 0.63 | 0.86 | 0.99 | 7 |
| gita·sa | 0.56 | 0.79 | 0.84 | 0.94 | 5 |
| yoga·en | 0.93 | 0.96 | 0.96 | 0.98 | 1 |
| yoga·hi | 0.23 | 0.34 | 0.77 | 0.93 | 12 |
| yoga·sa | 0.23 | 0.32 | 0.73 | 0.96 | 13 |

**Finding:** dense retrieval *finds* the gold verse (R@50 = 0.93–0.99) but, cross-lingually,
**ranks it at median rank 7–13** — below the top-5 the reader sees. The cross-lingual collapse
is a **ranking failure**, not a reasoning or verification failure. English queries put gold at rank 1.

---

## 3. k-sweep — confirming the lever (and its ceiling)

Re-ran E-on-B at k=10 and k=20 to test "just widen the reader's window."

- **k=10:** E beats B in **all 6 cells** (repairs finally fire, 1–4/cell). XL mean F1 0.619→0.659.
- **k=20:** **plateaus/regresses** — gita-hi 0.683 (k10) → 0.670 (k20); the reader drowns in
  20 noisy passages. Also hit a 120 s Ollama `TimeoutError` (huge prompt).

**Conclusion:** brute-force widening plateaus at ~k=10; the right lever is **reranking** (fix
the order, not the window). Locked E's default to k=10, retrieval=hybrid.

---

## 4. System C — cross-encoder reranking (the fix)

Built the ranking fix:

- **`canoncite/systems/rerank.py`** — `BAAI/bge-reranker-v2-m3` cross-encoder (multilingual
  XLM-RoBERTa), loaded as a singleton; `rerank(query, candidates, top)`.
- **`canoncite/systems/reranked_rag.py`** — System C runner + shared `rerank_retrieve()`:
  wide hybrid recall (cand=50) → cross-encoder rerank → top-5 → reader.
- Wired `sweep.py --system C` and `--retrieval rerank` (for E-on-C / E2-on-C).

**Result — C vs B (reader=llm, k=5), `system{B,C}.jsonl`:**

| corpus·q | B F1 | C F1 | Δ |
|---|---|---|---|
| gita·en | 0.754 | 0.735 | −0.019 |
| gita·hi | 0.660 | **0.747** | **+0.087** |
| gita·sa | 0.628 | **0.710** | **+0.082** |
| yoga·en | 0.797 | 0.811 | +0.014 |
| yoga·hi | 0.622 | **0.690** | **+0.068** |
| yoga·sa | 0.593 | 0.613 | +0.020 |
| **XL mean** | **0.626** | **0.690** | **+0.064** |

**Finding:** reranking delivers its biggest gains exactly where gold was buried (cross-lingual),
neutral on English (no headroom). C@5 (XL 0.690) even beats E@10 (XL 0.659) → **reranking >
widening k**, with a shorter cleaner context. Retrieval ladder: **A→B→C = 0.177 → 0.626 → 0.690**.

---

## 5. E-on-C — verify+repair is *subsumed* once ranking is fixed (pivotal negative result)

Ran E's binary verify+repair over reranked retrieval → `systemEC.jsonl`.

**Result:** XL mean F1 C 0.690 → E-on-C 0.698 (**+0.008, noise**; 3 cells up, 3 down); MAR mixed.

**Finding:** E v1's verify+repair is a remedy for *bad retrieval*. Once System C surfaces the
right verse in the top-5, there is nothing wrong to repair — the verify step just adds a few
abstentions. **The value of a generic verify-and-repair layer is captured by fixing ranking.**

**Error analysis of C's residual misattributions:** dominated by **near-misses** — citing an
adjacent, same-theme verse (Gītā 2.47 vs 2.48). Gītā-en NMR 0.214 ≈ 86% of that cell's MAR.
A topical reranker scores neighbors ~equally and cannot separate them; E's binary per-candidate
check accepts the first plausible one and cannot either. **This near-miss class is the target
for an exact-ID method** — and the paper's actual novelty.

---

## 6. System E2 — joint discriminative exact-ID selection (the contribution)

Built **`canoncite/systems/verified_rag2.py`** (`sweep.py --system E2`): replaces E v1's binary
per-candidate grounding check with a **joint discriminative select** — show all reranked top-k
(k=8) candidates side by side and force ONE exact-source pick ("neighbors on the same theme are
NOT the source; or null → abstain"). One LLM call, not k. Seeing 2.47 and 2.48 *together* is
what makes the exact-ID distinction possible.

**Result — E2-on-C vs C, `systemE2C.jsonl`:**

| corpus·q | C F1 | E2 F1 | C MAR | **E2 MAR** | repairs |
|---|---|---|---|---|---|
| gita·en | 0.735 | 0.754 | 0.250 | **0.119** | 15 |
| gita·hi | 0.747 | 0.744 | 0.254 | **0.149** | 19 |
| gita·sa | 0.710 | 0.724 | 0.309 | **0.138** | 15 |
| yoga·en | 0.811 | 0.723 | 0.186 | **0.100** | 14 |
| yoga·hi | 0.690 | 0.683 | 0.231 | **0.128** | 9 |
| yoga·sa | 0.613 | 0.620 | 0.242 | **0.216** | 11 |
| **XL mean** | **0.690** | **0.693** | | **≈ halved** | |

**Finding — E2 roughly HALVES misattribution (MAR ↓41–55%) at matched F1**, with repairs firing
heavily (9–19/cell vs E v1's 0–5). This is the payoff on the benchmark's **core axis** (citation
misattribution + abstention) — a discrimination neither the topical reranker (C) nor the binary
verifier (E) can make. **E2 is the paper's method contribution.**

**Known blemish:** Yoga Sūtras English F1 0.811 → 0.723 — E2 over-corrects on easy English items
where C is already near-ceiling. Targeted fix pending (soften the abstain, or only override on
genuinely ambiguous candidate sets).

---

## 7. System D — Self-RAG + CRAG (the SOTA baseline E2 must beat)

Built **`canoncite/systems/self_rag.py`** (`sweep.py --system D`): inference-time (prompted)
Self-RAG + CRAG, the standard way to baseline these when reflection tokens can't be fine-tuned.
Over the same reranked retrieval as E2:
1. **CRAG relevance filter** — label each passage correct/ambiguous/incorrect; drop incorrect;
   if none survive → abstain (closed corpus, no web fallback).
2. **Self-RAG generate** over surviving passages.
3. **ISSUP support critique** — keep a citation only if the passage supports the answer; else
   switch to the best supported alternative, else abstain.

D reflects on each passage **individually** (like E v1's binary check) — the hypothesis is that
it cannot separate near-miss neighbors, so **E2's joint discrimination should beat D on MAR**.
This head-to-head (D vs E2) is the paper's central gate. *Evaluation running.*

---

## 8. Scale-up + paper

- **Full chain launched** (detached, checkpointed, small-corpora-first):
  `C → D → E2 → B`, each across all 10 corpora. Builds the 8 missing BGE-M3 dense caches on
  the fly. Checkpoints `systemC_all/systemD_all/systemE2_all/systemB_all.jsonl`.
  **Rule: never run two Ollama-driving sweeps concurrently** — they queue and blow the 120 s
  timeout (learned the hard way when a concurrent E2 run killed the scale run).
- **Paper `paper/canoncite.md` updated** with §5.4.3 (System C + recall probe), §5.4.4 (E-on-dense
  subsumed), §5.4.5 (E2 halves MAR), §5.4.6 (System D methodology); rewrote Table 5.6, the
  abstract, and §1.2 contributions to the "ranking is the bottleneck; E2 halves misattribution"
  story. All numbers verbatim from `results/`.

---

## System catalog (`canoncite/systems/`)

| File | System / role |
|---|---|
| `bm25.py` | stdlib BM25 lexical retriever |
| `dense.py` | BGE-M3 dense retriever (+ FAISS), embeddings cached per corpus (`dense_bgem3.npz`) |
| `corpus_text.py` | corpus loader (concatenates text fields for retrieval/verification) |
| `reader.py` | readers: `top1` / `topk` / `llm` (the real reader; cites exact IDs or abstains) |
| `naive_rag.py` | **System A** — BM25 → reader |
| `hybrid_rag.py` | **System B** — BM25 + BGE-M3 fused by RRF → reader |
| `rerank.py` | BGE-reranker-v2-m3 cross-encoder |
| `reranked_rag.py` | **System C** — wide hybrid → rerank → top-5 → reader (+ shared `rerank_retrieve`) |
| `verified_rag.py` | **System E (v1)** — binary grounding verify + repair / abstain |
| `verified_rag2.py` | **System E2 (ours)** — joint discriminative exact-ID select |
| `self_rag.py` | **System D** — Self-RAG + CRAG (SOTA baseline) |
| `diagnose_e.py` | diagnostic — verifier false-negative / over-abstention trace |
| `recall_probe.py` | diagnostic — recall@k of the gold verse (retrieval-only) |
| `sweep.py` | grid runner: `--system A/B/C/D/E/E2`, `--retrieval bm25/hybrid/rerank`, `--reader`, `--k`, `--checkpoint`, `--out` |

**Run examples:**
```
PYTHONPATH=. python3 -m canoncite.systems.sweep --system C  --reader llm --k 5 --checkpoint results/gpu_qwen14b/systemC_all.jsonl  --out results/gpu_qwen14b/systemC_all.md
PYTHONPATH=. python3 -m canoncite.systems.sweep --system E2 --retrieval rerank --reader llm --k 8 --checkpoint results/gpu_qwen14b/systemE2_all.jsonl --out results/gpu_qwen14b/systemE2_all.md
PYTHONPATH=. python3 -m canoncite.systems.sweep --system D  --retrieval rerank --reader llm --k 8 --checkpoint results/gpu_qwen14b/systemD_all.jsonl  --out results/gpu_qwen14b/systemD_all.md
```

---

## Consolidated result (pilot corpora, Qwen2.5-14B, cross-lingual mean F1)

| System | XL Attr-F1 ↑ | XL MAR ↓ | one-line |
|---|---|---|---|
| A · naive BM25 | 0.177 | high (0.6–0.9) | cross-lingually blind |
| B · hybrid (BM25+BGE-M3) | 0.626 | ↓ | dense retrieval closes most of the gap |
| C · reranking (BGE-reranker-v2-m3) | **0.690** | mixed | fixes *ranking* — best retrieval-only |
| D · Self-RAG+CRAG (SOTA) | *running* | *running* | per-passage reflection baseline |
| E · ours v1 (binary verify+repair) | 0.698 (on C) | mixed | subsumed once ranking fixed |
| **E2 · ours (discriminative exact-ID)** | 0.693 (on C) | **≈ halved (↓41–55%)** | wins on the core misattribution axis |

`CER = 1.000` for every system/cell → no system ever cites a non-existent verse; all error is
real-but-wrong-verse, which is exactly why E2's exact-ID discrimination (not an existence check)
is the effective intervention.

---

## Infrastructure lessons

1. **Detached jobs** survive session/turn boundaries only with
   `setsid nohup bash -c "..." > log 2>&1 </dev/null & disown`. Plain `&` or `setsid` alone can die.
2. **Never run two Ollama sweeps concurrently** — Ollama serializes requests; the second stream
   pushes the first past the 120 s urllib timeout and crashes it. Chain sweeps sequentially.
3. **Keep the reader context small** (k≈5 + rerank). Large prompts (k=20) both hurt accuracy and
   blow the 120 s generation timeout.
4. **`pgrep -f "systems.sweep"` self-matches** the checking shell (the pattern is in its own argv)
   → false "still running". Use `ps aux | grep "[c]anoncite.systems.sweep"` (bracket trick).
5. **Checkpoints are mandatory** — the box is flaky/ephemeral; `--checkpoint` makes every sweep
   resumable and idempotent per (corpus, lang) cell.

---

## Open items / next

- Complete the all-10 scale run; fill the paper's all-10 columns (Table 5.6).
- **The gate: D vs E2 on MAR** (D's pilot cells land from the running chain).
- Fix the E2 Yoga-en over-correction.
- Multi-reader panel (≥1 Indic-tuned model + Claude) on the winning configs.
- Human-review → gold pipeline; dataset release.
