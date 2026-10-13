from __future__ import annotations
from .llm_client import api_available, chat, LLMError
from .prompts import SYSTEM_PROMPT, build_user_prompt


class LessonGenerator:
    """API mode when OPENAI_API_KEY is set; otherwise a deterministic OFFLINE SIMULATOR.
    The simulator is for tests/demo only. With demo_fail_first it writes a realistically flawed
    first draft (no labelled example, undefined jargon, an overclaim) and fixes ONLY the problems
    named in the evaluator feedback on the retry, so the feedback loop is genuinely exercised."""

    def __init__(self, demo_fail_first=False):
        self.demo_fail_first = demo_fail_first
        self.calls = 0
        self.flaws = {"concrete_example", "jargon_explained", "grounding"} if demo_fail_first else set()

    def generate(self, topic, source_pack, memory_hints="", retry_feedback=None, attempt_number=1):
        retry_feedback = retry_feedback or []
        if api_available():
            return chat([{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": build_user_prompt(topic, source_pack, memory_hints,
                                                                       retry_feedback, attempt_number)}])
        return self._simulate(retry_feedback)

    def _simulate(self, feedback):
        self.calls += 1
        for item in feedback:                       # act ONLY on what the evaluator reported
            self.flaws.discard(item.split(":", 1)[0].strip())
        f = self.flaws
        example = ("Imagine a student asks a question about the school. The system looks at the handbook and replies."
                   if "concrete_example" in f else
                   'A school handbook says: "The library closes at 4:00 p.m. on weekdays."\n\n'
                   '- **Question:** "When does the library close?"\n'
                   '- **Retrieved information:** The handbook line "The library closes at 4:00 p.m. on weekdays."\n'
                   '- **Answer:** "The library closes at 4:00 p.m. on weekdays."\n'
                   '- **Without RAG:** the model may only guess a closing time.\n'
                   '- **With RAG:** the model reads the handbook line first, then answers from it.')
        overclaim = " RAG always gives correct answers, so it removes hallucination completely." if "grounding" in f else \
                    " RAG does not guarantee a correct answer: the documents may be old, or the system may find the wrong section."
        step3 = ("3. **Store for search:** save the pieces in a vector database and build an index." if "jargon_explained" in f else
                 "3. **Prepare for search:** the system may create an embedding. An embedding is a list of numbers that shows the meaning of a text. Texts with similar meaning get similar numbers.")
        terms = ("- **Language model:** an AI program that reads and writes text.\n- **Chunk:** a small piece of a longer document.\n"
                 "- **Embedding:** a list of numbers used to compare text by meaning.\n"
                 "- **Vector search:** a search method that compares these number lists to find text with similar meaning.\n"
                 "- **Hallucination:** when an AI gives information that is false or not supported by its sources.\n"
                 "- **Fine-tuning:** training a model more on examples to change how it behaves.\n"
                 + ("" if "jargon_explained" in f else
                    "- **Vector database:** a store that keeps embeddings so that similar ones can be found quickly.\n"))
        return f"""## What is RAG?

RAG means **Retrieval-Augmented Generation**. Retrieval means finding information. Augmented means added to. Generation means writing the answer. So RAG is a way for an AI system to look up useful information before it writes an answer. Think of it like an open-book test. The system opens its notes first. Then it writes the answer.

## Why is it useful?

A **language model** is a computer program that reads and writes text. It learned from a large amount of text in the past. So it may not know your private documents or the latest news. When it does not know, it can guess. The guess may sound right but be wrong. RAG gives the model relevant documents at answer time, such as a school handbook or a product guide. This helps the answer match those documents. When the system shows its sources, people can also check the answer.{overclaim}

## How it works

Think of two stages. Stage one prepares the documents. Stage two answers a question.

1. **Collect documents:** gather useful files, such as a school handbook.
2. **Split into chunks:** divide long files into smaller pieces. A chunk is one small piece of text.
{step3}
4. **Find useful information:** when a person asks a question, the system searches for relevant chunks. It can use keyword search, meaning-based vector search, or both.
5. **Write the answer:** the language model gets the question and the chosen chunks. Then it writes an answer using that information.

## A simple example

{example}

## Important terms

{terms}
## Benefits and limits

Benefits: answers can be more relevant to your documents. The system can use updated documents. When sources are shown, it is easier to check the answer.

Limits: the system can miss the right document. The documents can be old or unreliable. The model can misunderstand what it reads. So important answers should always be checked.

RAG is not the same as fine-tuning. Fine-tuning changes a model by training it. RAG gives the model information at answer time. They solve different problems. They can also be used together.

## Quick recap

RAG first finds useful information and then gives it to a language model to help write an answer. The key idea is **search first, answer second**. RAG can improve answers, but it cannot promise that every answer is true.
"""
