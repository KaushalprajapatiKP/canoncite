"""Trilingual pass: add Hindi + native-language translations to every seed item.

Engine: **AI4Bharat IndicTrans2** (`ai4bharat/indictrans2-en-indic-1B`) — SOTA
open-source EN->Indic MT, covering Hindi / Tamil / Punjabi / Sanskrit. Run this on
a GPU box. Pali (Dhammapada's native language) is NOT in IndicTrans2 and is handled
separately by `translate_pali.py` (Claude) — so this script has NO API dependency.

For each item it translates `question` + `gold_answer` from English into the
corpus's IndicTrans2 target langs and writes them under `translations`. Gold
citations are language-independent and never change. The pass is idempotent: a
language already present on an item is skipped (safe to re-run).

Run on the GPU box:
    pip install -r canoncite/requirements.txt
    PYTHONPATH=. python canoncite/seed/translate.py --all --device cuda
    # then: re-validate, git add canoncite/data/items, commit, push
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from canoncite.corpus_io import load_id_space
from canoncite.items import CORPUS_NATIVE, Item, validate_item

# our lang code -> IndicTrans2 FLORES code (Pali intentionally absent)
FLORES = {"hi": "hin_Deva", "sa": "san_Deva", "ta": "tam_Taml", "pa": "pan_Guru"}
MODEL = "ai4bharat/indictrans2-en-indic-1B"


def indic_target_langs(corpus: str) -> list[str]:
    """IndicTrans2-supported target langs for a corpus: Hindi + native (if distinct
    and IndicTrans2-supported). Dhammapada's native (Pali) is excluded here."""
    native = CORPUS_NATIVE[corpus]
    langs = ["hi"]
    if native != "hi" and native in FLORES:
        langs.append(native)
    return langs


class IndicTrans2:
    """Lazy IndicTrans2 wrapper (loads the model once, on first use)."""

    def __init__(self, device: str = "cpu"):
        self.device = device
        self._tok = self._model = self._ip = None

    def _load(self):
        if self._model is not None:
            return
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        try:
            from IndicTransToolkit.processor import IndicProcessor
        except ImportError:
            from IndicTransToolkit import IndicProcessor
        self._tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(MODEL, trust_remote_code=True).to(self.device)
        self._ip = IndicProcessor(inference=True)

    def translate(self, sentences: list[str], tgt: str) -> list[str]:
        """EN -> tgt (FLORES code). Empty strings pass through unchanged."""
        self._load()
        import torch
        idx = [i for i, s in enumerate(sentences) if s and s.strip()]
        out = list(sentences)
        for start in range(0, len(idx), 16):
            ids = idx[start:start + 16]
            chunk = [sentences[i] for i in ids]
            batch = self._ip.preprocess_batch(chunk, src_lang="eng_Latn", tgt_lang=tgt)
            enc = self._tok(batch, truncation=True, padding="longest", return_tensors="pt",
                            max_length=256).to(self.device)
            with torch.no_grad():
                gen = self._model.generate(**enc, max_length=256, num_beams=5, num_return_sequences=1)
            dec = self._tok.batch_decode(gen, skip_special_tokens=True)
            for i, r in zip(ids, self._ip.postprocess_batch(dec, lang=tgt)):
                out[i] = r
        return out


def run_corpus(corpus: str, engine: IndicTrans2) -> dict:
    path = f"canoncite/data/items/{corpus}/seed_candidates.jsonl"
    U = load_id_space(f"canoncite/data/corpora/{corpus}/corpus_index.jsonl")
    items = [Item.from_dict(json.loads(l)) for l in open(path, encoding="utf-8") if l.strip()]

    for lang in indic_target_langs(corpus):
        todo = [i for i in items if lang not in i.translations]  # idempotent
        if not todo:
            continue
        q_t = engine.translate([i.question for i in todo], FLORES[lang])
        a_t = engine.translate([i.gold_answer for i in todo], FLORES[lang])
        for it, q, a in zip(todo, q_t, a_t):
            it.translations[lang] = {"question": q, "gold_answer": a}
            it.provenance.setdefault("trans_engine", {})[lang] = "indictrans2"
            it.provenance["trans_verified"] = False

    errs = sum(1 for i in items if any(l == "error" for l, _ in validate_item(i, U)))
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    return {"corpus": corpus, "items": len(items),
            "langs": indic_target_langs(corpus), "validation_errors": errs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    corpora = list(CORPUS_NATIVE) if args.all else [args.corpus]
    engine = IndicTrans2(args.device)
    for c in corpora:
        print(run_corpus(c, engine), file=sys.stderr)


if __name__ == "__main__":
    main()
