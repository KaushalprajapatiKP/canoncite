"""Render the ACL submission (canoncite.tex) as readable Markdown.

The .tex is the artefact we submit; this produces a version that can be read in
any editor or on GitHub without a TeX toolchain (this machine has none). It is a
faithful rendering, not a second source of truth -- regenerate it after editing
the .tex rather than editing the .md by hand:

    python paper/acl/tex2md.py

Handles only the constructs the submission actually uses; anything unrecognised
is passed through so it shows up as obviously-wrong rather than silently dropped.
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "canoncite.tex")
MD = os.path.join(HERE, "canoncite.md")

# LaTeX accent/diacritic forms used for transliterated Sanskrit, Tamil, Pali.
ACCENTS = {
    r"\={\i}": "ī", r"\={a}": "ā", r"\={u}": "ū", r"\={\i}}": "ī",
    r"\d{n}": "ṇ", r"\d{s}": "ṣ", r"\d{r}": "ṛ", r"\d{t}": "ṭ", r"\d{d}": "ḍ",
    r"\d{m}": "ṃ", r"\d{h}": "ḥ", r"\d{l}": "ḷ",
    r"\'{e}": "é", r"\~{n}": "ñ",
}

SYMBOLS = {
    r"\alpha": "α", r"\kappa": "κ", r"\sigma": "σ", r"\pm": "±",
    r"\times": "×", r"\uparrow": "↑", r"\downarrow": "↓", r"\sim": "~",
    r"\cdot": "·", r"\ldots": "…", r"\dagger": "†", r"\approx": "≈", r"\neq": "≠",
    r"\subseteq": "⊆", r"\not\subseteq": "⊄", r"\to": "→", r"\rightarrow": "→",
    r"\!": "", r"\,": " ", r"\ ": " ", r"\%": "%", r"\&": "&", r"\$": "$",
    r"\_": "_", r"\#": "#",
}


def _inline(s: str) -> str:
    """Inline markup: emphasis, citations, math, escapes."""
    for k, v in ACCENTS.items():
        s = s.replace(k, v)
    # numeric group separators first: \textbf{188{,}557} would otherwise not match
    s = s.replace("{,}", ",").replace("{.}", ".")
    # emphasis, applied innermost-first and repeated so nested commands resolve
    # (e.g. \textbf{118 items to \texttt{verified}})
    for _ in range(6):
        before = s
        s = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", s)
        s = re.sub(r"\\mathbf\{([^{}]*)\}", r"**\1**", s)
        s = re.sub(r"\\emph\{([^{}]*)\}", r"*\1*", s)
        s = re.sub(r"\\textit\{([^{}]*)\}", r"*\1*", s)
        s = re.sub(r"\\textsc\{([^{}]*)\}", r"\1", s)
        s = re.sub(r"\\texttt\{([^{}]*)\}", r"`\1`", s)
        if s == before:
            break
    # citations -> (Author, key) style; the .bib carries the full entry
    s = re.sub(r"\\citet\{([^}]*)\}", lambda m: _cite(m.group(1), True), s)
    s = re.sub(r"\\cite\{([^}]*)\}", lambda m: _cite(m.group(1), False), s)
    # cross-references
    s = re.sub(r"\\S\\ref\{sec:([^}]*)\}",
               lambda m: "\u00a7" + SECTIONS.get(m.group(1), m.group(1)), s)
    s = re.sub(r"Table~\\ref\{tab:([^}]*)\}",
               lambda m: "Table " + str(TABLE_NUM.get(m.group(1), "?")), s)
    s = re.sub(r"\\ref\{[^}]*\}", "", s)
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    # math: strip $...$ and translate the symbols inside
    def _math(m):
        inner = m.group(1)
        for k, v in SYMBOLS.items():
            inner = inner.replace(k, v)
        return re.sub(r"[{}\\]", "", inner)
    s = re.sub(r"\$([^$]*)\$", _math, s)
    for k, v in SYMBOLS.items():
        s = s.replace(k, v)
    s = s.replace("{,}", ",").replace("{.}", ".")
    s = s.replace("---", "—").replace("--", "–")
    s = s.replace("``", "“").replace("''", "”")
    s = re.sub(r"\\\\\s*$", "", s)
    return re.sub(r"[ \t]+", " ", s).strip()


_CITEKEYS: dict[str, str] = {}


def _cite(keys: str, textual: bool) -> str:
    out = []
    for k in [k.strip() for k in keys.split(",")]:
        out.append(_CITEKEYS.get(k, k))
    joined = "; ".join(out)
    return f"{joined}" if textual else f"({joined})"


def _load_bib():
    """Map bib keys to 'Author Year' for readable inline citations."""
    path = os.path.join(HERE, "canoncite.bib")
    if not os.path.exists(path):
        return
    for entry in re.split(r"@\w+\{", open(path, encoding="utf-8").read())[1:]:
        key = entry.split(",", 1)[0].strip()
        am = re.search(r"author\s*=\s*\{(.+?)\}\s*,\s*\n", entry, re.S)
        ym = re.search(r"year\s*=\s*\{(\d{4})\}", entry)
        who = "?"
        if am:
            first = am.group(1).split(" and ")[0].strip().strip("{}")
            who = first.split(",")[0].strip() if "," in first else first.split()[-1]
        _CITEKEYS[key] = f"{who} {ym.group(1)}" if ym else who


def _strip_wrapper(line: str, cmd: str, nargs: int) -> str:
    r"""Remove \cmd{..}{..}{X} keeping X. Brace-counted, so the kept argument may
    itself contain commands (e.g. \multicolumn{2}{c}{\textbf{English}})."""
    out, i, tag = [], 0, "\\" + cmd + "{"
    while True:
        j = line.find(tag, i)
        if j == -1:
            out.append(line[i:])
            return "".join(out)
        out.append(line[i:j])
        k = j + len(tag) - 1
        kept = ""
        for arg in range(nargs):
            depth, start = 0, k
            while k < len(line):
                if line[k] == "{":
                    depth += 1
                elif line[k] == "}":
                    depth -= 1
                    if depth == 0:
                        k += 1
                        break
                k += 1
            kept = line[start + 1:k - 1]
        out.append(kept)
        i = k


def _table(block: str) -> str:
    """tabular -> markdown table; caption becomes an italic line beneath."""
    cap = ""
    ci = block.find("\\caption{")
    if ci >= 0:
        k = ci + len("\\caption{"); depth = 1; start = k
        while k < len(block) and depth:
            if block[k] == "{": depth += 1
            elif block[k] == "}": depth -= 1
            k += 1
        cap = _inline(" ".join(block[start:k-1].split()))
    body = re.search(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", block, re.S)
    if body:
        inner = body.group(1)
        # drop the column specification, which may itself contain braces (@{}lcc@{})
        depth, cut = 0, 0
        for idx, ch in enumerate(inner):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    cut = idx + 1
                    break
        inner = inner[cut:]
        body = re.match(r"(?s)(.*)", inner)
    if not body:
        return f"*{cap}*\n" if cap else ""
    rows = []
    for raw in body.group(1).split(r"\\"):
        line = raw.strip()
        for rule in ("\\toprule", "\\midrule", "\\bottomrule"):
            line = line.replace(rule, "")
        line = re.sub(r"\\cmidrule\([^)]*\)\{[^}]*\}", "", line)
        line = _strip_wrapper(line, "multicolumn", 3)
        line = _strip_wrapper(line, "multirow", 3)
        line = line.strip()
        if not line:
            continue
        rows.append([_inline(c) for c in line.split("&")])
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |",
           "|" + "---|" * width]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    if cap:
        out += ["", f"*{cap}*"]
    return "\n".join(out)


SECTIONS: dict[str, str] = {}
TABLE_NUM: dict[str, int] = {}


def _load_sections(src: str):
    """label -> section title, so cross-references read as names not slugs."""
    cur = None
    for line in src.splitlines():
        m = re.match(r"\\section\*?\{(.+?)\}", line.strip())
        if m:
            cur = m.group(1)
        m = re.search(r"\\label\{sec:([^}]*)\}", line)
        if m and cur:
            SECTIONS[m.group(1)] = cur


def convert() -> str:
    _load_bib()
    src = open(TEX, encoding="utf-8").read()
    _load_sections(src)
    for i, lab in enumerate(re.findall(r'\\label\{tab:([^}]*)\}', src), 1):
        TABLE_NUM[lab] = i
    src = src.split(r"\begin{document}", 1)[1].split(r"\end{document}")[0]
    src = re.sub(r"(?m)^\s*%.*$", "", src)          # comment lines
    src = re.sub(r"(?<!\\)%.*$", "", src, flags=re.M)  # trailing comments

    title = "CANONCITE: A Multilingual, Multi-Tradition Benchmark for Canonical-Citation Attribution and Abstention"
    out = [f"# {title}", "",
           "> Rendered from `canoncite.tex` by `tex2md.py`. The `.tex` is the "
           "submission artefact; regenerate this file rather than editing it.", ""]

    # pull tables out first so their internals are not treated as prose
    tables: dict[str, str] = {}
    def _stash(m):
        key = f"@@TABLE{len(tables)}@@"
        tables[key] = _table(m.group(0))
        return "\n" + key + "\n"
    src = re.sub(r"\\begin\{table\}.*?\\end\{table\}", _stash, src, flags=re.S)

    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S)
    if abstract:
        out += ["## Abstract", "", _inline(" ".join(abstract.group(1).split())), ""]
        src = src[abstract.end():]

    # a \paragraph may begin mid-block; make it start its own chunk
    src = re.sub(r"(?<!\n)(?<!\n\n)\s*(\\paragraph\{)", r"\n\n\1", src)
    for raw in re.split(r"\n\s*\n", src):
        chunk = raw.strip()
        if not chunk or chunk in (r"\maketitle",):
            continue
        if chunk.startswith("@@TABLE"):
            out += ["", tables.get(chunk.strip(), ""), ""]
            continue
        m = re.match(r"\\section\*?\{(.+?)\}(.*)", chunk, re.S)
        if m:
            out += ["", f"## {_inline(m.group(1))}", ""]
            rest = m.group(2).strip()
            if rest:
                out.append(_inline(" ".join(rest.split())))
            continue
        m = re.match(r"\\paragraph\{(.+?)\}(.*)", chunk, re.S)
        if m:
            out += ["", f"**{_inline(m.group(1))}**  ", ""]
            rest = m.group(2).strip()
            if rest:
                out.append(_inline(" ".join(rest.split())))
            continue
        if r"\begin{itemize}" in chunk:
            for item in re.split(r"\\item", chunk)[1:]:
                item = item.replace(r"\end{itemize}", "").replace(r"\begin{itemize}", "")
                item = re.sub(r"\[[^\]]*\]", "", item, count=1)
                out.append(f"- {_inline(' '.join(item.split()))}")
            out.append("")
            continue
        if chunk.startswith(r"\bibliography"):
            continue
        if chunk.strip() == r"\appendix":
            out += ["", "---", "", "# Appendix", ""]
            continue
        out.append(_inline(" ".join(chunk.split())))

    # references, from the bib
    out += ["", "## References", ""]
    for key, label in sorted(_CITEKEYS.items(), key=lambda kv: kv[1]):
        out.append(f"- **{label}** (`{key}`)")
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text + "\n"


if __name__ == "__main__":
    md = convert()
    with open(MD, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"wrote {os.path.relpath(MD)}  ({len(md.split())} words)")
