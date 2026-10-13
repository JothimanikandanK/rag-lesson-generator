# Self-Evaluating Lesson Content Generator

A Python project that generates a beginner-friendly lesson on **Introduction to RAG**, checks the draft against a hard pass/fail rubric, retries with evaluator feedback (up to two retries), and saves the final lesson, rejection log, run report, and persistent SQLite memory.

## Features

- **Separate generator and evaluator:** the evaluator independently checks the generated lesson.
- **Hard pass/fail checks:** a lesson is approved only when all required checks pass; there is no average score.
- **Bounded retry loop:** one initial attempt plus a maximum of two retries.
- **Deliberate failure demo:** `--demo-fail-first` creates a flawed first draft so you can demonstrate rejection and revision.
- **Persistent memory:** SQLite stores run and attempt history and recurring failure patterns can inform later prompts.
- **Grounding:** a small source pack guides lesson content. The rule-based evaluator is not a guarantee that every factual claim is correct.

## Requirements

- Python 3.10 or later
- No third-party packages are required for the offline demo.
- An API key is only needed if you want to use the OpenAI-compatible API mode.

## Setup and run (Windows / PowerShell)

1. Download or clone this repository.
2. Open a terminal in the project root—the folder containing `main.py`, `rag_agent/`, and `tests/`.
3. Check Python:

```powershell
python --version
```

4. Run the offline demo. It requires no API key:

```powershell
python main.py --topic "Introduction to RAG" --demo-fail-first
```

The first draft is deliberately flawed. The evaluator should reject it, send feedback to the generator, and the revised draft should pass. The command prints a run report to the terminal.

5. Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

The included test suite currently contains four offline tests covering a passing lesson, deliberate failure detection, retry behavior, and the retry cap.

## Run on macOS / Linux

From the project root, run the same commands:

```bash
python3 --version
python3 main.py --topic "Introduction to RAG" --demo-fail-first
python3 -m unittest discover -s tests -v
```

If your system uses `python` instead of `python3`, use `python` in the commands.

## Optional: use an OpenAI-compatible API

The generator supports an OpenAI-compatible chat-completions endpoint. Set your environment variables before running without `--demo-fail-first`.

**Windows PowerShell:**

```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_MODEL="gpt-4o-mini"
python main.py --topic "Introduction to RAG"
```

**macOS / Linux:**

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4o-mini"
python main.py --topic "Introduction to RAG"
```

Optional configuration:

- `OPENAI_BASE_URL` — API base URL; defaults to `https://api.openai.com/v1`.
- `OPENAI_MODEL` — model name; defaults to `gpt-4o-mini`.
- `--max-retries 0|1|2` — number of retries after the first attempt; maximum is two.
- `--output-dir outputs` — output folder.

Do not commit API keys or other credentials to GitHub. The offline demo is sufficient to demonstrate the workflow and does not call an external model.

## Outputs

The run creates these files in `outputs/` (or the folder passed through `--output-dir`):

- `lesson.md` — approved lesson, or a clearly marked **NOT APPROVED** lesson if all attempts fail.
- `rejection_log.json` — failed checks, reasons, and feedback supplied to the next attempt.
- `run_report.json` — final status, attempt count, rubric version, and check results.
- `memory.sqlite3` — persistent run and attempt history.

## Workflow

```text
Topic + source pack + memory hints
                |
                v
          Generator <--------- evaluator feedback
                |                       ^
                v                       |
        Hard-gate evaluator ------------+
           | PASS       | FAIL
           v            v
      Save lesson   Log rejection and retry
           \            /
             SQLite memory
```

The pipeline stops when the lesson passes or when the initial attempt plus the allowed retries have been used.

## Rubric

The evaluator uses nine hard-gate checks:

1. `definition` — defines RAG and expands the acronym.
2. `why_it_matters` — explains why RAG is useful.
3. `how_it_works` — explains the retrieval and generation process.
4. `concrete_example` — includes a clear example with a question, retrieved information, and answer.
5. `jargon_explained` — explains key technical terms in plain language.
6. `beginner_language` — checks beginner-friendly wording and sentence length.
7. `key_points` — covers benefits and limitations.
8. `coherent_structure` — checks lesson organization.
9. `grounding` — checks key source-pack coverage and guards against selected overclaims.

These are transparent rule-based checks, not a complete semantic or factual verification system.

## Project structure

- `main.py` — command-line entry point and bounded retry loop
- `rag_agent/generator.py` — API and deterministic demo generation
- `rag_agent/evaluator.py` — pass/fail rubric
- `rag_agent/memory.py` — SQLite persistence and memory hints
- `rag_agent/prompts.py` — generation and retry prompts
- `rag_agent/sources.py` — source pack used for grounding
- `tests/test_pipeline.py` — four offline tests
- `docs/DESIGN.md` — design decisions and trade-offs
- `docs/Assessment_Design_Document.pdf` — design document
- `docs/VIDEO_DEMO_SCRIPT.md` — short video narration outline

## Known limitations

The offline demo uses a deterministic simulator, not an LLM. The rule-based evaluator checks structure and selected content patterns but cannot catch every subtle factual error. The source pack is small and fixed. For production use, add stronger source-level attribution, independent factual review, broader regression tests, and human approval before publishing educational material.

