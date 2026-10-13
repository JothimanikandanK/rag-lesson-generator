# Video Demonstration Script (3-4 min)

**Before recording:** Python 3.10+, no API key needed. Delete `memory/` for a clean start.

**0:00-0:30 Problem.** "This system generates a beginner lesson, judges it with hard pass/fail checks, regenerates on failure, and decides alone whether it ships. Audience: a class-12 learner, non-English-medium, zero AI background."

**0:30-1:10 Architecture.** Show the README diagram. Generator, evaluator (deterministic gates + LLM judge in API mode), retry controller capped at 2 retries, SQLite memory.

**1:10-2:00 The loop.** Run `python main.py --demo-fail-first`. Open `outputs/rejection_log.json`: attempt 1 failed `concrete_example`, `jargon_explained`, `grounding`, each with a reason; `changes_on_retry` shows all three fixed. Say clearly this is the offline simulator.

**2:00-2:30 Result.** Open `outputs/lesson.md` (APPROVED, attempt 2) and `run_report.json` (every check PASS/FAIL).

**2:30-3:00 Memory.** Run again with `--feedback "Use one more everyday Indian example" --output-dir outputs/run2_with_memory`; show `memory_hints_used` and `memory_snapshot.json`.

**3:00-3:40 Trade-offs.** Rules are transparent but gameable; LLM judge is flexible but can be inconsistent; hence hybrid plus human approval. Rubric is never auto-edited. Run `python -m unittest discover -s tests -v` to show 16 passing tests.
