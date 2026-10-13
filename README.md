
# Self-Evaluating Lesson Content Generator

Generates a beginner lesson on **Introduction to RAG**, judges it against hard pass/fail checks, regenerates with the evaluator's reasons (max 2 retries), and writes the passing lesson plus a rejection log that says **what failed, why, and what changed on the retry**. Memory persists across runs.

## Quick start (no API key, Python 3.10+, no packages)
```bash
python main.py --demo-fail-first          # offline simulator: flawed draft 1 -> rejected -> fixed draft 2 -> approved
python -m unittest discover -s tests -v   # 16 offline tests
```
`--demo-fail-first` uses a **deterministic offline simulator** (not an LLM). Draft 1 has three real flaws (no labelled example, undefined jargon, an overclaim). On retry the simulator fixes only what the evaluator reported, so the feedback loop is genuinely exercised.

## Real LLM mode
```bash
export OPENAI_API_KEY=...            # PowerShell: $env:OPENAI_API_KEY="..."
export OPENAI_MODEL=gpt-4o-mini      # generator model (optional)
export OPENAI_JUDGE_MODEL=...        # judge model (optional; use a different model if you can)
python main.py --topic "Introduction to RAG"
```
In API mode a **second, independent LLM call (judge, temperature 0)** adds 4 semantic checks (`llm_factual_accuracy`, `llm_beginner_clarity`, `llm_example_quality`, `llm_teaching_flow`) on top of the deterministic gates. If the judge's reply is invalid it **fails closed** (lesson not shipped). API outages count as failed attempts; the pipeline never crashes. `--no-judge` turns the judge off. `OPENAI_BASE_URL` supports any OpenAI-compatible endpoint.

## Architecture
```text
topic + source pack + memory hints
          |
          v
   Generator  <------ feedback ("check: reason") ------+
          |                                            |
          v                                            |
   Evaluator = deterministic gates + optional LLM judge
     PASS -> lesson.md (APPROVED)     FAIL -> rejection_log.json (+ what changed on retry)
          |                                            |
          +-------------> SQLite memory <--------------+  (failure patterns + human feedback)
```
Loop = 1 attempt + at most 2 retries (hard cap in code and tested). If nothing passes, `lesson.md` is marked **NOT APPROVED — do not publish**.

## Rubric v2.0.0 (every check PASS/FAIL, no scores)
| Check | What it verifies |
|---|---|
| definition | RAG expanded and defined in the first section |
| why_it_matters | the problem (model guesses / lacks private or new data) and how documents help |
| how_it_works | >= 4 numbered steps, order chunk -> search -> language model |
| concrete_example | labelled Question / Retrieved information / Answer, answer words come from the retrieved text |
| jargon_explained | every watched technical term that appears has a definition (not just 4 fixed terms) |
| beginner_language | avg sentence <= 18 words, max <= 32, 250-900 words, few long words, analogy present |
| key_points | >= 2 benefits, >= 2 limitations, keyword/vector search |
| coherent_structure | 7 headings in the required order |
| grounding | no overclaims, no numbers outside the source pack (example excluded), explicit "does not guarantee" |
| clean_output | no leaked meta text (evaluator, source pack, placeholders) |

## Memory / self-evolution
`memory/memory.sqlite3` keeps attempts, failure reasons, runs, and human feedback (`--feedback "..."`). The most frequent past failures (with their repair instructions) and recent human feedback are injected into the next generation prompt. `memory_snapshot.json` exports the learning; checks that fail >= 5 times are flagged for **human rubric review**. The rubric is never auto-edited, because a system must not lower its own bar to pass.

## Outputs (`outputs/`)
`lesson.md`, `rejection_log.json`, `run_report.json`, `memory_snapshot.json`; `outputs/run2_with_memory/` is a second run showing memory hints and human feedback being used.

## Files
`main.py` loop + CLI | `rag_agent/generator.py` | `evaluator.py` | `llm_judge.py` | `llm_client.py` | `memory.py` | `prompts.py` | `sources.py` | `tests/` | `docs/` (DESIGN.md, design PDF, VIDEO_DEMO_SCRIPT.md)

## Known limits (honest)
Deterministic checks catch structure, jargon, overclaims, and invented numbers, not every subtle factual error; that is what the LLM judge and human approval are for. Memory hints are topic-agnostic. The source pack is a small fixed set of notes (no vector DB needed for one topic).
=======

