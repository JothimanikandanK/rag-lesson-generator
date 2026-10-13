SOURCE_PACK = """
Grounding notes for a beginner explanation of Retrieval-Augmented Generation (RAG):
- RAG stands for Retrieval-Augmented Generation.
- A RAG system first retrieves relevant information from a collection of documents or other knowledge sources, then gives that information to a language model to help it generate an answer.
- The retrieval step may use keyword search, vector similarity search, or a combination. Vector search compares numerical representations called embeddings.
- An embedding is a list of numbers that represents aspects of the meaning of text, allowing similar meanings to be compared.
- Documents are often split into smaller chunks before indexing. This helps retrieve focused pieces of information.
- RAG can make answers more relevant to supplied or up-to-date information and can make answers easier to check when the system shows its sources.
- RAG does not guarantee correctness. Retrieval can miss relevant material, sources can be wrong or outdated, and a model can still misunderstand the retrieved text.
- Fine-tuning changes model behavior by training on examples; RAG supplies relevant information at answer time. They solve different problems and may be combined.
- Basic flow: collect documents -> split into chunks -> index/search them -> user asks a question -> retrieve relevant chunks -> provide chunks and question to the language model -> generate an answer.
- Simple example: a school uploads its handbook. A learner asks, "When does the library close?" The system retrieves the handbook section about library hours and the language model writes an answer based on that section.
- Use plain language for beginners; explain terms such as model, embedding, vector database, chunk, and hallucination when they appear.
"""
