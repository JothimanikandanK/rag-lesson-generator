"""Hard pass/fail rubric. Deterministic checks (always on) + optional LLM judge (API mode).
Every check is PASS or FAIL. One FAIL rejects the lesson."""
from __future__ import annotations
import re

RUBRIC_VERSION = "2.0.0"

ORDERED_HEADINGS = [("what is rag",), ("why",), ("how it works",), ("example",),
                    ("important terms", "key terms"), ("benefits and limits", "limits"), ("quick recap", "recap")]

# Terms a beginner may not know. If one appears, the lesson must define it somewhere.
JARGON = ["language model", "embedding", "chunk", "vector search", "vector database", "hallucination",
          "fine-tuning", "index", "indexing", "token", "llm", "api", "semantic", "corpus", "retriever", "prompt"]
REQUIRED_DEFINITIONS = ["embedding", "chunk", "vector search", "hallucination"]
DEF_CUE = re.compile(r"\b(is a|is an|is the|is one|is when|means|called|refers to)\b", re.I)

OVERCLAIMS = [r"always\s+(\w+\s+){0,2}(correct|true|accurate|right)", r"100\s?%", r"never (wrong|hallucinat\w*|makes? mistakes?)",
              r"(eliminates?|removes?) (all )?hallucination", r"completely removes?", r"no mistakes",
              r"(?<!not )(?<!cannot )(?<!n't )guarantee[sd]? (that |a |every |the )?(correct|true|accurate|answer)",
              r"perfect answers?"]
LIMIT_STATEMENT = re.compile(r"does not guarantee|cannot promise|can still be wrong|not always (correct|right)", re.I)
LEAKS = ["intentionally", "evaluator", "rejected", "as an ai language model", "source pack", "todo", "{example}", "attempt "]
STOP = set("the a an and or of to in on at is are was it this that with for as by from be can will then".split())


def _check(ok, reason, **extra):
    return {"status": "PASS" if ok else "FAIL", "reason": "Satisfied" if ok else reason, **extra}


def parse_sections(text):
    secs, cur, buf = [], None, []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            if cur is not None:
                secs.append((cur, "\n".join(buf)))
            cur, buf = line.lstrip("# ").strip().lower(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        secs.append((cur, "\n".join(buf)))
    return secs


def _sec(secs, *keys):
    for head, body in secs:
        if any(k in head for k in keys):
            return body
    return ""


def _prose(text):
    t = re.sub(r"^\s*#+.*$", "", text, flags=re.M)
    t = re.sub(r"^\s*(\d+\.|[-*])\s+", "", t, flags=re.M)
    t = t.replace("**", "").replace("p.m.", "pm").replace("a.m.", "am")
    return t


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", _prose(text)) if len(s.split()) >= 2]


def _words(s):
    return re.findall(r"[a-z0-9:]+", s.lower())


def _defined(term, text):
    rx = rf"{re.escape(term)}(?:s|es)?"
    if re.search(rf"\*\*{rx}\s*:\s*\*\*|\*\*{rx}\*\*\s*:", text, re.I):
        return True
    return any(re.search(rf"\b{rx}\b", s, re.I) and DEF_CUE.search(s) for s in _sentences(text))


def readability(text):
    sents = _sentences(text)
    lens = [len(s.split()) for s in sents] or [0]
    words = re.findall(r"[A-Za-z']+", _prose(text))
    long_words = [w for w in words if len(w) >= 13]
    return {"words": len(words), "avg_sentence_words": round(sum(lens) / len(lens), 1),
            "max_sentence_words": max(lens), "long_word_ratio": round(len(long_words) / max(1, len(words)), 3)}


def deterministic_checks(lesson, source_pack):
    text = lesson.strip()
    lower = text.lower()
    secs = parse_sections(text)
    heads = [h for h, _ in secs]
    c = {}

    first = secs[0][1].lower() if secs else ""
    c["definition"] = _check(
        "retrieval-augmented generation" in first and "rag" in first and bool(re.search(r"means|stands for|is a", first)),
        "In the first section, expand RAG as Retrieval-Augmented Generation and define it in one plain sentence.")

    why = _sec(secs, "why").lower()
    problem = any(t in why for t in ["wrong", "not know", "guess", "outdated", "private", "old"])
    value = any(t in why for t in ["relevant", "documents", "latest", "updated", "sources"])
    c["why_it_matters"] = _check(problem and value,
        "In the 'why' section, state the problem (model can guess or be wrong / lacks private or new data) and how documents help.")

    how = _sec(secs, "how it works")
    how_l = how.lower()
    steps = re.findall(r"^\s*\d+\.\s", how, flags=re.M)
    pos = [how_l.find(t) for t in ("chunk", "search", "language model")]
    c["how_it_works"] = _check(len(steps) >= 4 and all(p >= 0 for p in pos) and pos == sorted(pos),
        "Give at least 4 numbered steps in order: split into chunks, search for relevant chunks, then give them to the language model.")

    ex = _sec(secs, "example")
    ex_n = ex.replace("*", "")
    ex_l = ex_n.lower()
    labelled = all(k in ex_l for k in ("question:", "retrieved information:", "answer:"))
    ok_support = False
    if labelled:
        ans = re.search(r"answer:\s*(.+)", ex_n, re.I).group(1)
        retrieved = re.search(r"retrieved information:\s*(.+)", ex_n, re.I).group(1)
        evidence = ex_n.split("Question:")[0] + " " + retrieved   # quoted source + retrieved line only
        shared = {w for w in _words(ans) if w not in STOP and len(w) > 3} & set(_words(evidence))
        ok_support = len(shared) >= 3
    c["concrete_example"] = _check(labelled and ok_support,
        "Add a worked example with 'Question:', 'Retrieved information:' and 'Answer:'. The answer must use words from the retrieved text.")

    undefined = [t for t in JARGON if re.search(rf"\b{re.escape(t)}(?:s|es)?\b", lower) and not _defined(t, text)]
    missing_req = [t for t in REQUIRED_DEFINITIONS if not _defined(t, text)]
    bad = sorted(set(undefined + missing_req))
    c["jargon_explained"] = _check(not bad, f"Define in plain words before relying on them: {', '.join(bad)}.", unexplained=bad)

    r = readability(text)
    analogy = bool(re.search(r"think of it like|imagine|like an open-book", lower))
    c["beginner_language"] = _check(
        250 <= r["words"] <= 900 and r["avg_sentence_words"] <= 18 and r["max_sentence_words"] <= 32
        and r["long_word_ratio"] <= 0.02 and analogy,
        f"Use shorter sentences (avg <= 18, max <= 32 words), 250-900 words, an everyday analogy. Measured: {r}", metrics=r)

    lim = _sec(secs, "limits").lower()
    ben_hits = sum(t in lim for t in ["relevant", "updated", "up-to-date", "sources", "check"])
    lim_hits = sum(t in lim for t in ["miss", "outdated", "old", "wrong", "unreliable", "misunderstand"])
    c["key_points"] = _check(ben_hits >= 2 and lim_hits >= 2 and ("keyword" in lower or "vector" in lower),
        "Cover at least two benefits, two limitations, and the kinds of search (keyword / vector).")

    idx = []
    for keys in ORDERED_HEADINGS:
        idx.append(next((i for i, h in enumerate(heads) if any(k in h for k in keys)), -1))
    c["coherent_structure"] = _check(all(i >= 0 for i in idx) and idx == sorted(idx),
        "Use these headings in order: What is RAG, Why, How it works, Example, Important terms, Benefits and limits, Quick recap.")

    overclaims = [m.group(0) for p in OVERCLAIMS for m in [re.search(p, lower)] if m]
    body_no_example = re.sub(r"\d+(?:[.,:]\d+)*", lambda m: m.group(0),
                             "\n".join(b for h, b in secs if "example" not in h))
    body_no_example = re.sub(r"^\s*\d+\.\s", "", body_no_example, flags=re.M)
    invented = [n for n in re.findall(r"\d+(?:[.,:]\d+)*%?", body_no_example) if n not in source_pack]
    c["grounding"] = _check(not overclaims and not invented and bool(LIMIT_STATEMENT.search(text)),
        f"Remove overclaims {overclaims}, invented numbers {invented}; and state clearly that RAG does not guarantee a correct answer.",
        overclaims=overclaims, invented_numbers=invented)

    leaks = [t for t in LEAKS if t in lower]
    c["clean_output"] = _check(not leaks, f"Remove text that is not part of the lesson: {leaks}.")
    return c


def evaluate_lesson(topic, lesson, source_pack, judge=None):
    checks = deterministic_checks(lesson, source_pack)
    if judge is not None:
        for name, v in judge(lesson, source_pack).items():
            checks[name] = _check(v["pass"], f"{v['reason']} Evidence: {v.get('evidence', '')}".strip())
    failed = [n for n, v in checks.items() if v["status"] == "FAIL"]
    reasons = [f"{n}: {checks[n]['reason']}" for n in failed]
    return {"passed": not failed, "checks": checks, "failed_checks": failed,
            "reasons": reasons, "feedback": reasons}
