# CANONCITE — Products Roadmap

CANONCITE (the "does the AI cite the *right* verse?" project) produces **five distinct
products** from one body of work. Two are near-done; three are real builds still ahead.
This file tracks all five so nothing gets lost.

The core research finding underneath all of them: *cross-lingual citation failure is a
**retrieval-ranking** problem, and a joint exact-ID selector (**System E2**) roughly halves
citation misattribution — more cheaply than the published SOTA.* Verified at scale (E2 <
D on misattribution across all 10 corpora; see `paper/canoncite.md`, Table 5.6).

---

## 1. The Dataset — the CANONCITE benchmark
**What it is:** 10 canonical texts (~188,557 citable verses), public-domain, with
trilingual questions (English + Hindi + native script) each tagged with the exact gold
citation. A citable, leaderboard-able artifact published on **HuggingFace**.

**Why it matters:** one-time artifact, but it's the anchor the paper and everything else
sits on; a released benchmark is what makes the work *cited* rather than just read.

**Status:** 🟡 **Built, not yet published.** `release/build_release.py` (public-domain
gate enforced), `DATASHEET.md`, HF README card, LICENSE all done; 622 seed items across
all 10 corpora. **Left:** finalize human-verified gold (reviewer pipeline), then the
actual HF push.

---

## 2. The Research Paper — the findings
**What it is:** the write-up of the result (ranking is the bottleneck; E2 halves
misattribution at lower cost). → arXiv, then a workshop, then ACL / NeurIPS Datasets &
Benchmarks.

**Why it matters:** the credibility signal (grad admissions / recruiters / advisor), and
the thing that makes the other four legible to the outside world.

**Status:** 🟡 **Draft complete, numbers landing.** `paper/canoncite.md` full draft; the
all-10 gate result is written as the money table (Table 5.6). **Left:** fold in the Aya
multi-reader robustness result, then submit. Likely wants an Indic-NLP advisor/co-author
for a top venue.

---

## 3. The Live Demo — people actually use it
**What it is:** a public demo/API — **ask any of the 10 texts a question → get an answer
with the correct verse cited, guaranteed no misattribution** (the C→E2 pipeline behind a
front-end).

**Note (be precise):** the app that is *live today* (Vercel web app) is the
**reviewer/annotation tool**, NOT this consumer product. The public "try it" demo is still
to build — but it's a small lift on top of the working engine.

**Why it matters:** the tangible thing you can show anyone in 10 seconds; converts the
research into something people *feel*.

**Status:** 🔴 **Engine done, public front-end to build.**

---

## 4. The Method as Open-Source Tooling — the reusable IP
**What it is:** the `canoncite` eval harness + the **E2 "exact-ID citation guardrail"**
packaged as a pip-installable library anyone can drop into their own RAG. **Not
scripture-specific** — works for any corpus with checkable IDs: **law, medicine,
scientific citations.** Ships with a **public leaderboard** for external submissions.

**Why it matters:** arguably the **highest-leverage** of the five. The dataset and paper
are one-time artifacts; the library is durable IP that compounds and turns the benchmark
into a *living* thing others build on.

**Status:** 🔴 **Internal code exists (`canoncite/`), packaging + leaderboard unbuilt.**

---

## 5. The Commercial Vertical — "citation-correct RAG" as a paid API
**What it is:** the same method aimed at a **high-stakes cited domain** where a wrong
citation is expensive — **law** (the Constitution of India is already in the corpus set)
or **medicine**. The *company* version: research doubles as the product's eval harness.

**Why it matters:** the business path; where the durable IP (#4) meets a market that pays
for correctness.

**Status:** 🔴 **Concept.** Flag freedom-to-operate (citation-verification patent
US12353469B1) before commercializing; academic publication is unaffected.

---

## Sequencing (suggested)
1. **Finish the research** (paper numbers + dataset gold) — unlocks #1 and #2.
2. **Publish** dataset (HF) + paper (arXiv). These two make the project real and citable.
3. **Build the demo (#3)** — cheap, high-visibility, reuses the engine.
4. **Package the library + leaderboard (#4)** — the compounding asset.
5. **Explore the vertical (#5)** — only once #4 exists and there's a design partner.
