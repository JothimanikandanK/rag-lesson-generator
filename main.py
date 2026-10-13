from __future__ import annotations
import argparse, difflib, json
from pathlib import Path
from rag_agent.generator import LessonGenerator
from rag_agent.evaluator import evaluate_lesson, RUBRIC_VERSION
from rag_agent.llm_client import api_available, LLMError
from rag_agent.llm_judge import judge_lesson
from rag_agent.memory import MemoryStore
from rag_agent.sources import SOURCE_PACK


def describe_changes(prev, new, prev_eval, new_eval):
    """What changed between a rejected draft and its retry (for the rejection log)."""
    before, after = set(prev_eval["failed_checks"]), set(new_eval["failed_checks"])
    diff = list(difflib.unified_diff(prev.splitlines(), new.splitlines(), lineterm="", n=0))
    added = [l[1:].strip() for l in diff if l.startswith("+") and not l.startswith("+++") and l[1:].strip()]
    removed = [l[1:].strip() for l in diff if l.startswith("-") and not l.startswith("---") and l[1:].strip()]
    return {"fixed_checks": sorted(before - after), "still_failing": sorted(before & after),
            "newly_failing": sorted(after - before),
            "words_before": len(prev.split()), "words_after": len(new.split()),
            "lines_added": len(added), "lines_removed": len(removed),
            "sample_added": [a[:140] for a in added[:3]], "sample_removed": [r[:140] for r in removed[:3]]}


def run_pipeline(topic, max_retries=2, output_dir="outputs", demo_fail_first=False,
                 generator=None, judge="auto", memory_db=None):
    max_retries = max(0, min(2, max_retries))            # hard cap: loop always terminates
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    memory = MemoryStore(str(memory_db or out / "memory.sqlite3"))
    hints = memory.get_hints(topic)
    generator = generator or LessonGenerator(demo_fail_first=demo_fail_first)
    if judge == "auto":
        judge = judge_lesson if api_available() else None
    rejection_log, attempts, feedback = [], [], []
    prev_lesson, prev_eval, final_lesson, final_eval = None, None, "", None

    for attempt in range(max_retries + 1):
        try:
            lesson = generator.generate(topic=topic, source_pack=SOURCE_PACK, memory_hints=hints,
                                        retry_feedback=feedback, attempt_number=attempt + 1)
            result = evaluate_lesson(topic, lesson, SOURCE_PACK, judge=judge)
        except LLMError as exc:                           # API outage = failed attempt, not a crash
            lesson = prev_lesson or ""
            result = {"passed": False, "checks": {"generation_error": {"status": "FAIL", "reason": str(exc)}},
                      "failed_checks": ["generation_error"], "reasons": [f"generation_error: {exc}"],
                      "feedback": [f"generation_error: {exc}"]}
        if rejection_log and prev_eval is not None and lesson:
            rejection_log[-1]["changes_on_retry"] = describe_changes(prev_lesson or "", lesson, prev_eval, result)
        attempts.append({"attempt": attempt + 1, "passed": result["passed"], "checks": result["checks"],
                         "failed_checks": result["failed_checks"]})
        memory.save_attempt(topic, attempt + 1, lesson, result)
        final_lesson, final_eval = lesson, result
        if result["passed"]:
            break
        feedback = result["feedback"]
        rejection_log.append({"attempt": attempt + 1, "status": "REJECTED", "failed_checks": result["failed_checks"],
                              "reasons": result["reasons"], "feedback_sent_to_generator": feedback,
                              "changes_on_retry": None})
        prev_lesson, prev_eval = lesson, result

    passed = bool(final_eval and final_eval["passed"])
    status = "APPROVED" if passed else "NOT APPROVED"
    note = (f"passed all hard-gate checks on attempt {len(attempts)}." if passed else
            f"failed the rubric after {len(attempts)} attempt(s). Human review required. Do not publish.")
    (out / "lesson.md").write_text(f"# {topic}\n\n> Status: **{status}** — {note}\n\n{final_lesson.strip()}\n", encoding="utf-8")
    (out / "rejection_log.json").write_text(json.dumps(
        {"topic": topic, "rubric_version": RUBRIC_VERSION, "rejections": rejection_log}, indent=2, ensure_ascii=False), encoding="utf-8")
    report = {"topic": topic, "status": status, "passed": passed, "attempts_used": len(attempts),
              "max_retries": max_retries, "rubric_version": RUBRIC_VERSION, "llm_judge_used": judge is not None,
              "generator_mode": "api" if api_available() else "offline-simulator",
              "attempts": attempts, "memory_hints_used": hints,
              "design_note": "Deterministic checks are hard gates, not proof of factual correctness; API mode adds an independent LLM judge."}
    (out / "run_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    memory.save_run(topic, status, len(attempts), RUBRIC_VERSION)
    (out / "memory_snapshot.json").write_text(json.dumps(memory.export_snapshot(), indent=2, ensure_ascii=False), encoding="utf-8")
    memory.close()
    return report


def main():
    p = argparse.ArgumentParser(description="Self-evaluating beginner lesson generator")
    p.add_argument("--topic", default="Introduction to RAG")
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--output-dir", default="outputs")
    p.add_argument("--memory-db", default="memory/memory.sqlite3", help="persistent memory shared across runs")
    p.add_argument("--demo-fail-first", action="store_true", help="offline simulator writes a flawed first draft")
    p.add_argument("--no-judge", action="store_true", help="disable the LLM judge in API mode")
    p.add_argument("--feedback", help="human feedback to store in memory for future runs")
    a = p.parse_args()
    Path(a.memory_db).parent.mkdir(parents=True, exist_ok=True)
    if a.feedback:
        m = MemoryStore(a.memory_db); m.add_feedback(a.topic, a.feedback); m.close()
    report = run_pipeline(a.topic, a.max_retries, a.output_dir, a.demo_fail_first,
                          judge=None if a.no_judge else "auto", memory_db=a.memory_db)
    print(json.dumps({k: report[k] for k in ("topic", "status", "attempts_used", "generator_mode", "llm_judge_used")}, indent=2))
    print(f"\nFinal status: {report['status']}. See {a.output_dir}/ for lesson, rejection log, report, memory snapshot.")


if __name__ == "__main__":
    main()
