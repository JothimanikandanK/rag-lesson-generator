# Introduction to RAG

> Status: **APPROVED** — passed all hard-gate checks on attempt 2.

## What is RAG?

RAG means **Retrieval-Augmented Generation**. Retrieval means finding information. Augmented means added to. Generation means writing the answer. So RAG is a way for an AI system to look up useful information before it writes an answer. Think of it like an open-book test. The system opens its notes first. Then it writes the answer.

## Why is it useful?

A **language model** is a computer program that reads and writes text. It learned from a large amount of text in the past. So it may not know your private documents or the latest news. When it does not know, it can guess. The guess may sound right but be wrong. RAG gives the model relevant documents at answer time, such as a school handbook or a product guide. This helps the answer match those documents. When the system shows its sources, people can also check the answer. RAG does not guarantee a correct answer: the documents may be old, or the system may find the wrong section.

## How it works

Think of two stages. Stage one prepares the documents. Stage two answers a question.

1. **Collect documents:** gather useful files, such as a school handbook.
2. **Split into chunks:** divide long files into smaller pieces. A chunk is one small piece of text.
3. **Prepare for search:** the system may create an embedding. An embedding is a list of numbers that shows the meaning of a text. Texts with similar meaning get similar numbers.
4. **Find useful information:** when a person asks a question, the system searches for relevant chunks. It can use keyword search, meaning-based vector search, or both.
5. **Write the answer:** the language model gets the question and the chosen chunks. Then it writes an answer using that information.

## A simple example

A school handbook says: "The library closes at 4:00 p.m. on weekdays."

- **Question:** "When does the library close?"
- **Retrieved information:** The handbook line "The library closes at 4:00 p.m. on weekdays."
- **Answer:** "The library closes at 4:00 p.m. on weekdays."
- **Without RAG:** the model may only guess a closing time.
- **With RAG:** the model reads the handbook line first, then answers from it.

## Important terms

- **Language model:** an AI program that reads and writes text.
- **Chunk:** a small piece of a longer document.
- **Embedding:** a list of numbers used to compare text by meaning.
- **Vector search:** a search method that compares these number lists to find text with similar meaning.
- **Hallucination:** when an AI gives information that is false or not supported by its sources.
- **Fine-tuning:** training a model more on examples to change how it behaves.
- **Vector database:** a store that keeps embeddings so that similar ones can be found quickly.

## Benefits and limits

Benefits: answers can be more relevant to your documents. The system can use updated documents. When sources are shown, it is easier to check the answer.

Limits: the system can miss the right document. The documents can be old or unreliable. The model can misunderstand what it reads. So important answers should always be checked.

RAG is not the same as fine-tuning. Fine-tuning changes a model by training it. RAG gives the model information at answer time. They solve different problems. They can also be used together.

## Quick recap

RAG first finds useful information and then gives it to a language model to help write an answer. The key idea is **search first, answer second**. RAG can improve answers, but it cannot promise that every answer is true.
