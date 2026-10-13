import json, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # run from project root, any way

from main import run_pipeline
from rag_agent.evaluator import evaluate_lesson
from rag_agent.generator import LessonGenerator
from rag_agent.llm_client import LLMError
from rag_agent.llm_judge import judge_lesson
from rag_agent.memory import MemoryStore
from rag_agent.sources import SOURCE_PACK

os.environ.pop("OPENAI_API_KEY", None)   # tests are always offline
T = "Introduction to RAG"


def good():
    return LessonGenerator().generate(T, SOURCE_PACK)


def ev(text, judge=None):
    return evaluate_lesson(T, text, SOURCE_PACK, judge=judge)


class AlwaysBad:
    def generate(self, **kw):
        return "## What is RAG?\n\nRAG is good."


class Broken:
    def generate(self, **kw):
        raise LLMError("network down")


class EvaluatorTests(unittest.TestCase):
    def test_complete_lesson_passes(self):
        r = ev(good()); self.assertTrue(r["passed"], r["reasons"])

    def test_missing_example_fails(self):
        t = good().replace("**Retrieved information:**", "**Found:**")
        self.assertIn("concrete_example", ev(t)["failed_checks"])

    def test_answer_not_supported_by_retrieved_text_fails(self):
        t = good().replace('**Answer:** "The library closes at 4:00 p.m. on weekdays."', "**Answer:** Pizza is delicious everywhere nowadays.")
        self.assertIn("concrete_example", ev(t)["failed_checks"])

    def test_undefined_jargon_fails(self):
        t = good().replace("- **Vector database:** a store that keeps embeddings so that similar ones can be found quickly.\n", "")
        t = t.replace("or both.", "or both. The chunks are kept in a vector database.")
        r = ev(t); self.assertIn("jargon_explained", r["failed_checks"])

    def test_overclaim_fails_but_negated_guarantee_passes(self):
        self.assertIn("grounding", ev(good() + "\nRAG always gives correct answers.")["failed_checks"])
        self.assertNotIn("grounding", ev(good())["failed_checks"])   # contains 'does not guarantee'

    def test_invented_statistic_fails(self):
        t = good().replace("Think of it like an open-book test.", "Think of it like an open-book test. RAG improves accuracy by 37%.")
        self.assertIn("grounding", ev(t)["failed_checks"])

    def test_long_sentences_fail_readability(self):
        long = " and ".join(["this extraordinarily convoluted sentence keeps going and going without any sensible stopping point"] * 3)
        t = good().replace("The system opens its notes first.", long + ".")
        self.assertIn("beginner_language", ev(t)["failed_checks"])

    def test_wrong_heading_order_fails(self):
        t = good().replace("## Quick recap", "## Zzz").replace("## What is RAG?", "## Quick recap")
        self.assertIn("coherent_structure", ev(t)["failed_checks"])

    def test_leaked_meta_text_fails(self):
        self.assertIn("clean_output", ev(good() + "\nThe evaluator rejected this.")["failed_checks"])

    def test_llm_judge_failure_rejects(self):
        fake = lambda l, s: {"llm_factual_accuracy": {"pass": False, "reason": "bad claim", "evidence": "x"}}
        r = ev(good(), judge=fake)
        self.assertFalse(r["passed"]); self.assertIn("llm_factual_accuracy", r["failed_checks"])

    def test_judge_fails_closed_on_garbage(self):
        out = judge_lesson("x", "y", chat_fn=lambda *a, **k: "not json")
        self.assertFalse(out["llm_judge_error"]["pass"])


class PipelineTests(unittest.TestCase):
    def test_demo_rejects_then_passes_and_logs_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            rep = run_pipeline(T, 2, tmp, demo_fail_first=True)
            self.assertTrue(rep["passed"]); self.assertEqual(rep["attempts_used"], 2)
            log = json.loads((Path(tmp) / "rejection_log.json").read_text())["rejections"]
            self.assertEqual(len(log), 1)
            self.assertEqual(sorted(log[0]["failed_checks"]), ["concrete_example", "grounding", "jargon_explained"])
            self.assertEqual(sorted(log[0]["changes_on_retry"]["fixed_checks"]), sorted(log[0]["failed_checks"]))

    def test_retry_cap_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            rep = run_pipeline(T, 99, tmp, generator=AlwaysBad())
            self.assertEqual(rep["attempts_used"], 3); self.assertEqual(rep["status"], "NOT APPROVED")
            self.assertIn("NOT APPROVED", (Path(tmp) / "lesson.md").read_text())

    def test_zero_retries_means_one_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_pipeline(T, 0, tmp, generator=AlwaysBad())["attempts_used"], 1)

    def test_api_outage_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            rep = run_pipeline(T, 2, tmp, generator=Broken())
            self.assertEqual(rep["status"], "NOT APPROVED"); self.assertEqual(rep["attempts_used"], 3)

    def test_memory_persists_and_feeds_next_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "m.sqlite3"
            run_pipeline(T, 2, tmp, demo_fail_first=True, memory_db=db)
            m = MemoryStore(str(db)); m.add_feedback(T, "Use more Indian examples"); m.close()
            rep2 = run_pipeline(T, 2, tmp, demo_fail_first=True, memory_db=db)
            self.assertIn("concrete_example", rep2["memory_hints_used"])
            self.assertIn("Indian examples", rep2["memory_hints_used"])


if __name__ == "__main__":
    unittest.main()
