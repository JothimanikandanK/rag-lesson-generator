"""Optional LLM judge (API mode only). A SECOND, independent call that grades the lesson
against the source pack. It adds checks to the deterministic gates; it never replaces them."""
from __future__ import annotations
import json, os, re
from .llm_client import chat, LLMError

JUDGE_CHECKS = {
    "llm_factual_accuracy": "Every technical claim is supported by the source pack. No outside facts, numbers or product claims.",
    "llm_beginner_clarity": "A class-12 learner from a non-English-medium school can follow the vocabulary. No unexplained term.",
    "llm_example_quality": "The example is correct, concrete, and the answer really comes from the retrieved text.",
    "llm_teaching_flow": "Ideas come in a logical order: what -> why -> how -> example -> limits.",
}

JUDGE_SYSTEM = ("You are a strict reviewer of beginner lessons. Judge ONLY with the rubric and the source pack. "
                "Each check is PASS or FAIL: no partial credit. For every FAIL, quote the exact lesson text that caused it "
                "and say how to fix it. Reply with JSON only.")


def judge_lesson(lesson: str, source_pack: str, chat_fn=chat) -> dict:
    rubric = "\n".join(f"- {k}: {v}" for k, v in JUDGE_CHECKS.items())
    user = (f"SOURCE PACK:\n{source_pack}\n\nRUBRIC:\n{rubric}\n\nLESSON:\n{lesson}\n\n"
            'Return JSON: {"llm_factual_accuracy": {"pass": true, "reason": "...", "evidence": "..."}, ...} for all 4 checks.')
    model = os.getenv("OPENAI_JUDGE_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        raw = chat_fn([{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
                      model=model, temperature=0.0)
        match = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(match.group(0))
        out = {}
        for name in JUDGE_CHECKS:
            item = data[name]
            out[name] = {"pass": bool(item["pass"]), "reason": str(item.get("reason", "")),
                         "evidence": str(item.get("evidence", ""))}
        return out
    except (LLMError, KeyError, TypeError, ValueError, AttributeError) as exc:
        # Fail closed: an unverifiable lesson is not shipped.
        return {"llm_judge_error": {"pass": False, "reason": f"LLM judge could not return a valid verdict: {exc}", "evidence": ""}}
