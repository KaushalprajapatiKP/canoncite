# Related Work & Prior-Art Investigation

**Thesis under review:** *Measuring and Reducing Citation Misattribution in Retrieval-Augmented QA over Canonical Texts.*
Claimed novelty: (a) attribution to a **fixed canonical ID space** (chapter.verse, surah:ayah, article§clause) enabling **exact, NLI-free** attribution scoring; (b) a **cross-domain multi-corpus benchmark** (Gita + Bible + US Constitution); (c) **interpretive/ambiguous** questions; (d) a **misattribution-repair** method.

**Investigation date:** 2026-06-29. All sources below were actually opened/searched via live web search. URLs are real. Where I did not open the full text, I say so.

> **Headline finding:** The single most threatening overlap is **"Citation Grounding" (Ovcharov, 2026, arXiv:2606.00898)** — a legal-domain paper that already does fixed-ID attribution against a citation graph, defines a precision/relevance/temporality metric suite, AND ships a repair method (CG-DPO) with cross-(legal-)domain evaluation. It scoops the *concept* of C2 and C3, but only in a single legal jurisdiction (Ukrainian law), not cross-corpus or religious. Read this paper before writing anything.

---

## 1. Closest prior work (most relevant, real citations + links)

1. **ALCE — "Enabling Large Language Models to Generate Text with Citations"** — Gao, Yen, Yu, Chen (EMNLP 2023). https://arxiv.org/abs/2305.14627 · code https://github.com/princeton-nlp/ALCE
   The canonical citation-quality benchmark (ASQA, QAMPARI, ELI5). Citation quality = **NLI entailment against retrieved web passages** (citation recall + precision). *Overlap:* defines the citation-precision/recall paradigm we'd reuse. *Delta preserved:* it is approximate/NLI-based against free-text passages, NOT exact matching to a fixed ID space. This is exactly the contrast our C2 wants to draw.

2. **"Citation Grounding: Detecting and Reducing LLM Citation Hallucinations via Legal Citation Graphs"** — Volodymyr Ovcharov (arXiv:2606.00898, 2026). https://arxiv.org/abs/2606.00898
   **The most direct competitor.** Builds a fixed citation graph (21,736 statute nodes from 100.8M Ukrainian court decisions); defines **Citation Grounding (CG)** = fraction of generated citations verifiable against the ground-truth graph, decomposed into **Citation Precision (does the provision exist)**, **Citation Relevance**, **Citation Temporality**; and introduces **CG-DPO** (preference fine-tuning on corrupted-citation pairs) as a repair method, evaluated across 7 legal sub-domains. *Overlap:* near-identical to our C2 metric idea (exact existence checking against a fixed ID space) AND to C3 (repair). *Delta we retain:* single legal jurisdiction; not cross-corpus; not religious; uses DPO fine-tuning rather than an inference-time verifier agent; no interpretive/abstention taxonomy.

3. **AttributedQA — "Attributed Question Answering: Evaluation and Modeling for Attributed Large Language Models"** — Bohnet, Tran, Verga, et al. (Google, arXiv:2212.08037, 2022). https://arxiv.org/abs/2212.08037
   Formalizes attribution via **AIS (Attributable to Identified Sources)** and proposes the reproducible eval framework most attribution papers build on. *Overlap:* foundational framing of "attribution." *Delta:* attribution is to retrieved passages, judged by human/NLI; no fixed canonical ID matching.

4. **ExpertQA — "Expert-Curated Questions and Attributed Answers"** — Malaviya, Lee, Chen, et al. (NAACL 2024). https://arxiv.org/abs/2309.07852 · https://aclanthology.org/2024.naacl-long.167/
   2,177 expert questions across 32 fields with claim-level factuality + attribution judgments. *Overlap:* cross-field attribution benchmark with interpretive/expert questions. *Delta:* attribution to web/passage evidence, no fixed-ID space, not canonical-text focused.

5. **HAGRID — "A Human-LLM Collaborative Dataset for Generative Information-Seeking with Attribution"** — Kamalloo et al. (arXiv:2307.16883, 2023). https://arxiv.org/abs/2307.16883 · https://huggingface.co/datasets/miracl/hagrid
   Attributed generation dataset built on MIRACL; in-context citation style. *Overlap:* attributable-generation benchmark. *Delta:* passage-level quotes, not fixed canonical IDs.

6. **CAQA — "Can LLMs Evaluate Complex Attribution in QA? Automatic Benchmarking using Knowledge Graphs"** — Hu et al. (ACL 2025; arXiv:2401.14640). https://arxiv.org/abs/2401.14640 · https://aclanthology.org/2025.acl-long.837/
   Uses **knowledge graphs** to auto-generate fine-grained attribution categories (supportive / partially-supportive / contradictory / irrelevant). *Overlap:* structured-source-driven, automatic attribution scoring — conceptually adjacent to "fixed ID enables automatic scoring." *Delta:* KG triples not canonical-text IDs; evaluates *evaluators*, not a RAG repair method.

7. **Self-RAG — "Learning to Retrieve, Generate, and Critique through Self-Reflection"** — Asai, Wu, Wang, Sil, Hajishirzi (ICLR 2024; arXiv:2310.11511). https://arxiv.org/abs/2310.11511
   On-demand retrieval + reflection tokens; improves citation accuracy in long-form generation. *Role:* a required baseline (plan System D). Not a fixed-ID attribution method.

8. **CRAG — "Corrective Retrieval Augmented Generation"** — Yan, Gu, et al. (arXiv:2401.15884, 2024). https://arxiv.org/abs/2401.15884 · https://openreview.net/forum?id=JnWJbrnaUE
   Lightweight retrieval evaluator triggers corrective retrieval actions. *Role:* required baseline (System D). Corrects retrieval, not citation IDs.

9. **RARR — "Researching and Revising What Language Models Say, Using Language Models"** — Gao, Dai, et al. (ACL 2023; arXiv:2210.08726). https://arxiv.org/abs/2210.08726 · https://github.com/anthonywchen/RARR
   Post-hoc attribution + revision of unsupported content. *Overlap:* the generate→verify→repair loop that our C3 echoes. *Delta:* attributes to web evidence, no fixed ID space.

10. **CiteFix — "Enhancing RAG Accuracy Through Post-Processing Citation Correction"** — Maheshwari, Tenneti, Nakkiran (arXiv:2504.15629, 2025). https://arxiv.org/abs/2504.15629
    Post-processing that re-attributes/corrects citations via keyword+semantic+BERTScore+lightweight-LLM matching. *Overlap:* this is a **citation-repair method**, very close in spirit to C3. *Delta:* corrects to **retrieved passages**, not canonical IDs; no benchmark contribution.

11. **VeriCite — "Towards Reliable Citations in RAG via Rigorous Verification"** — Qian, Fan, Guo, et al. (SIGIR-AP 2025; arXiv:2510.11394). https://arxiv.org/abs/2510.11394 · https://dl.acm.org/doi/10.1145/3767695.3769505
    Three-stage generate→NLI-verify→refine pipeline on ASQA/ELI5/HotpotQA/MuSiQue. *Overlap:* verify-then-repair citations (C3). *Delta:* NLI against passages, not fixed-ID exact match.

12. **"A Comparative Analysis of Faithfulness Metrics and Humans in Citation Evaluation"** — Li et al. (arXiv:2408.12398, 2024) and companion **"Towards Fine-Grained Citation Evaluation"** (arXiv:2406.15264). https://arxiv.org/abs/2408.12398 · https://arxiv.org/abs/2406.15264
    Show NLI/LLM faithfulness metrics struggle to separate full/partial/no support. *Why it matters:* this is the empirical motivation for our pitch — exact ID matching sidesteps the partial-support ambiguity these metrics fail on. Good support for C2's framing.

---

## 2. Direct competitors to our specific novelty

**(a) Fixed-ID / canonical attribution scoring (our C2 core idea):**
- **Citation Grounding (2606.00898, legal)** — *already does it* via a statute citation graph: "does the cited provision exist" = existence check against a fixed node set. This is the same insight as our Citation Existence Rate. **Our claim "fixed IDs enable exact NLI-free attribution" is no longer conceptually novel — it is demonstrated in legal.** What remains: doing it in religious/canonical-scripture corpora and cross-domain.
- **CAQA (2401.14640)** uses KG structure to make attribution automatically checkable — adjacent idea, different structure.
- No paper found does **verse/surah/article§clause** canonical-ID attribution scoring for scripture. That specific instantiation appears open.

**(b) Cross-domain / multi-corpus citation benchmark (our C1 core idea):**
- ExpertQA (32 fields) and **CiteVQA** (multi-domain document attribution, arXiv:2605.12882) and **MCiteBench** (multimodal citations, arXiv:2503.02589) cover multiple domains, but all are passage/document-grounded, none mix **religious + secular-legal canonical texts with canonical-ID ground truth**. No direct competitor found for the specific Gita+Bible+Constitution cross-corpus canonical-ID benchmark. **This combination looks genuinely unoccupied.**

**(c) Misattribution-repair method (our C3 core idea):**
- **Heavily contested.** CiteFix (post-process correction), VeriCite (verify+refine), RARR (post-hoc revise), CG-DPO (legal repair via DPO), Self-RAG/CRAG (corrective generation), plus **CiteGuard** (arXiv:2510.17853, retrieval-augmented citation validation), **FACTUM** (mechanistic citation-hallucination detection, arXiv:2601.05866), **CiteCheck** (citation faithfulness detection, arXiv:2502.10881), **SemanticCite** (arXiv:2511.16198), and **"Enhancing Factual Accuracy and Citation Generation via Multi-Stage Self-Verification"** (arXiv:2509.05741). The generate→verify→repair loop is now a crowded space. Our only defensible delta is that verification is an **exact lookup against a fixed ID space** (cheaper, deterministic, no NLI noise) rather than NLI-against-passages.

---

## 3. Existing benchmarks/datasets we'd compete with or build on

| Resource | Domain | Attribution unit | Link | Relation |
|---|---|---|---|---|
| ALCE (ASQA/QAMPARI/ELI5) | open-domain | retrieved passage (NLI) | https://github.com/princeton-nlp/ALCE | metric paradigm to extend |
| AttributedQA | open-domain | identified source (AIS) | https://arxiv.org/abs/2212.08037 | framing |
| ExpertQA | 32 expert fields | web/passage | https://arxiv.org/abs/2309.07852 | cross-field comparison point |
| HAGRID | info-seeking (MIRACL) | quote/passage | https://huggingface.co/datasets/miracl/hagrid | attributed-gen baseline |
| CAQA | KG-derived | KG triple / category | https://arxiv.org/abs/2401.14640 | structured-attribution analogue |
| Qur'an QA 2022 (QRCD/AyaTEC) | Quran | passage span (verse-ID-adjacent) | https://github.com/llm-lab-org/QuranicBenchmarking | religious QA; **no misattribution metric**; could supply Quran items |
| Optimized Quran Passage Retrieval | Quran | verse/passage | https://arxiv.org/abs/2412.11431 | Quran extension corpus |
| BibleQA (Finding Answers from the Word of God) | Bible | answer verse | https://arxiv.org/abs/1810.12118 | Bible-verse QA precursor; trivia-style, no attribution-faithfulness focus |
| Legal citation prediction (Australian law) | legal | case/statute citation | https://arxiv.org/abs/2412.06272 | legal-citation-accuracy precedent |
| "Large Legal Fictions" (Dahl et al.) | legal | case citation | https://academic.oup.com/jla/article/16/1/64/7699227 | measures legal citation hallucination rates |
| Citation Grounding (legal graph) | legal | statute node (fixed ID) | https://arxiv.org/abs/2606.00898 | **closest competitor** (see §2) |

**Build-on opportunities:** existing Quran (QRCD) and Bible (BibleQA) QA sets give us a head start on those corpora, but none carry **canonical-ID attribution ground truth + interpretive/unanswerable taxonomy**, which is the part we'd add. Survey grounding: **"A Survey of Large Language Models Attribution"** (arXiv:2311.03731) and **"Attribution, Citation, and Quotation: A Survey of Evidence-based Text Generation"** (arXiv:2508.15396) confirm no scripture/cross-canonical fixed-ID benchmark exists.

---

## 4. Relevant patents

1. **US12353469B1 — "Verification and citation for language model outputs"** — Amazon Technologies Inc. Filed 2024-06-28, granted 2025-07-08. https://patents.google.com/patent/US12353469B1/en
   Claims a citation module that identifies values/strings in LLM output, validates them against **ground-truth databases / retrieved source documents**, and auto-corrects mismatches; includes temporal-aware embeddings and NL→SQL. **Blocking assessment: moderate.** It targets verification of *quantitative values / strings against a knowledge base via regex/SQL*, on **retrieved passages**, not attribution to a **fixed canonical citation-ID space** with verse/section semantics. Our method (exact ID-set matching + repair over canonical corpora) is distinguishable, but a productized "RAG + automatic citation verification + correction" feature would want a freedom-to-operate review against this claim set. Academic publication is unaffected.
2. **US patent app — "Methods and systems for generation of text using LLM with indications of unsubstantiated information"** (USPTO doc 12468878). https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12468878
   Covers prompting an LLM to flag unsubstantiated spans. Tangential; low blocking risk for a fixed-ID attribution metric/method. (Surfaced in search; only abstract-level reviewed.)
3. **US patent (USPTO doc 12306859) — "protecting and removing private information used in LLMs."** https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12306859
   Not relevant to citation attribution; listed for completeness only.

> Caveat: Google Patents' search UI did not render full result lists to the fetcher, so this patent sweep is **non-exhaustive**. A proper FTO search (especially OpenAI/Anthropic/Google/Microsoft assignees on "citation verification" and "grounded generation") is recommended before any product claims. No academic-novelty blocker found.

---

## 5. Honest novelty verdict

**C1 — Cross-corpus canonical-ID benchmark (Gita + Bible + Constitution, w/ interpretive + unanswerable items): NOVEL (with caveats).**
No existing benchmark mixes religious and secular-legal canonical texts with canonical-ID attribution ground truth and an interpretive/abstention taxonomy. Component pieces exist independently (Quran QA, BibleQA, legal citation sets), so reviewers will say "assembled from known parts" — the defensible novelty is the *cross-domain canonical-ID design + interpretive/trap items*, not the corpora themselves. Strongest, most clearly-publishable contribution. Lead with it.

**C2 — Exact, NLI-free attribution metrics over a fixed ID space: PARTIAL (conceptually scooped).**
The core claim "discrete IDs let you score attribution exactly instead of via NLI" is **already demonstrated** by the legal Citation Grounding paper (CG/CP/CR/CT) and is adjacent to CAQA's KG-structured scoring. Your CER/CG/MAR are close cousins of their CP/CG. You cannot claim the *idea* as new. You *can* claim the first instantiation for scripture/canonical-text QA and the first **cross-domain** comparison of misattribution rates under one exact metric. Reframe C2 as "a unified cross-corpus exact-attribution metric suite," cite Ovcharov 2026 prominently, and drop any "first to propose NLI-free exact attribution" language.

**C3 — Misattribution-repair method: PARTIAL, leaning SCOOPED.**
Generate→verify→repair for citations is crowded (CiteFix, VeriCite, RARR, CG-DPO, CiteGuard, FACTUM, CiteCheck, multi-stage self-verification, Self-RAG/CRAG). An inference-time verifier-agent that exact-matches cited IDs against the corpus and regenerates is incremental over CiteFix. To survive review it must (i) beat a real SOTA baseline (Self-RAG/CRAG/VeriCite), not just naive RAG, and (ii) show the fixed-ID exact-check yields a measurable advantage (determinism, cost, or MAR reduction) over NLI-based repair. Otherwise C3 collapses into the benchmark contribution.

**Overall:** The thesis is publishable as a **datasets-and-benchmarks** paper (C1+C2 reframed), but the method (C3) and the metric *idea* (C2) are no longer first-movers. The "fixed-ID enables exact attribution" framing is the one place where you've been beaten to the core insight (in legal), so position against it explicitly rather than claiming it.

---

## 6. Recommended thesis refinements

1. **Re-anchor on cross-domain generality, not the metric idea.** Make the headline "first benchmark showing misattribution and its repair *transfer across religious and secular-legal canonical corpora under one exact metric*." Cite Ovcharov 2026 as the legal-only predecessor you generalize.
2. **Cite and contrast Citation Grounding (2606.00898) up front.** Treat CG/CP/CR/CT as related metrics; show your CER/CG/MAR are the cross-corpus generalization. Do NOT claim to have invented NLI-free exact attribution scoring.
3. **Differentiate C3 sharply or demote it.** Either (a) prove the exact-ID verifier beats VeriCite/Self-RAG/CRAG on MAR at lower cost (no NLI model needed), or (b) present C3 as a strong baseline and let C1+C2 carry the paper. Add CiteFix and VeriCite as method baselines, not just Self-RAG/CRAG.
4. **Lean hard on interpretive + unanswerable items.** This is the least-covered axis among competitors (most are factoid/lookup). Abstention-on-unanswerable and ambiguity-graded items are a genuine differentiator — expand the trap/near-miss citation items (gold 2.47 vs distractor 5.18) since "near-miss misattribution" is exactly what fixed-ID scoring measures uniquely well.
5. **Keep the corpus mix but justify it as a design, not a convenience.** Frame Gita+Bible+Constitution as spanning {interpretive-religious, narrative-religious, prescriptive-legal} to argue generality to any citation-critical domain.
6. **Run an FTO check on US12353469B1** before any product/demo claims; publication is fine.
7. **Public-domain only** in the released set (already noted in the plan) — drop BBT/Prabhupada from the released benchmark.

---

### One-line summary

A crowded attribution/citation-verification field plus a legal paper (Ovcharov 2026) that already does fixed-ID scoring + repair means the *metric idea* and the *repair method* are no longer first-movers, but the cross-domain religious-plus-legal canonical-ID benchmark with interpretive/unanswerable items remains open and is the contribution to lead with.

**Verdict — C1 (benchmark): NOVEL · C2 (metrics): PARTIAL · C3 (method): PARTIAL.**
