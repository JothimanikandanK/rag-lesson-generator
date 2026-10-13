# Design Notes

## Goal
Not "one clever prompt": a loop that decides on its own whether content is good enough to ship, explains every rejection, and learns across runs.

## Components and why
- **Generator** (API or offline simulator). The simulator exists so the loop is testable and demoable for free; it is labelled as a simulator everywhere. It writes a flawed first draft on request and fixes only what feedback names, so tests prove feedback is actually used.
- **Evaluator = deterministic gates + optional LLM judge.** Deterministic checks are cheap, repeatable, and unit-tested; they cover structure, readability numbers, jargon definitions, overclaims, invented numbers. The LLM judge (separate call, temperature 0, optionally a different model) covers what rules cannot: factual accuracy against the source pack, clarity, example quality, flow. It must quote evidence for each fail and fails closed on bad output.
- **Hard pass/fail**: any single FAIL rejects. No averages that hide a missing example or a wrong claim.
- **Retry controller**: 1 + max 2 retries, clamped in code; API errors count as failed attempts; exhausted budget => NOT APPROVED. Each rejection records `changes_on_retry` (checks fixed / still failing / newly broken, word delta, diff samples).
- **Memory (SQLite)**: failure reasons + human feedback -> next prompt. Guidance adapts; acceptance criteria do not. Repeated failures (>= 5) raise a flag for a human to review the rubric.

## Trade-offs
- Rules vs LLM judge: rules are transparent but gameable by keywords; judges are flexible but inconsistent and can share the generator's blind spots. Hybrid + human approval is the production path.
- Two retries: bounds cost and guarantees termination; a stubborn failure goes to a human instead of looping.
- No automatic rubric edits: avoids the system weakening its own bar.
- No vector DB: one topic, a small source pack is enough; per-claim source spans are the next step.

## Fixes made in v2 (from review of v1)
v1 problems: tests could not be discovered (import path); evaluator had an operator-precedence bug in `grounding` and was keyword-only; jargon check covered only 4 hard-coded terms; readability was never measured; the demo failure was a hard-coded sentence and the retry ignored feedback; rejection log lacked "what changed"; API errors crashed the run; retry-cap test could not fail; memory stored no reasons or human feedback.

## Next steps
Per-claim source-span attribution, a second judge model, learner testing as a quality signal, a manual publish approval step.
