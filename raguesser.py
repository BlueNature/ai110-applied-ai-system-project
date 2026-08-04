"""
(initially copied from module 4 tinker)
Core RAGuesser class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob
from collections import Counter

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on",
    "for", "with", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "at", "by",
    "from", "into", "about", "than", "then", "so", "such", "not", "no",
    "do", "does", "did", "can", "will", "would", "should", "could",
    "you", "your", "we", "our", "i", "what", "which", "who", "how",
}

# Max number of sections a single file may contribute to one retrieve() call,
# so a multi-section answer isn't truncated to just its single best section.
SECTION_CAP_PER_FILE = 4

# Guardrail: minimum fraction of a query's content words that must appear
# in a section for it to be trusted. Below this, a match is likely
# incidental keyword overlap rather than real relevance. Calibrated
# against SAMPLE_QUERIES: filters out trick/out-of-scope queries while
# keeping every legitimately-answerable one.
MIN_RELEVANCE_RATIO = 0.1

def split_into_sections(text):
    """
    Splits raw document text into chunks on paragraph breaks (blank lines).
    """
    text = text.replace("\r\n", "\n")
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip()]

class RAGuesser:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Split each document into paragraph sections so retrieval can
        # return individual sections instead of whole files
        self.sections = self.build_sections(self.documents)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.sections)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Section Splitting
    # -----------------------------------------------------------

    def build_sections(self, documents):
        """
        Splits every loaded document into paragraph sections.
        Returns a list of (filename, section_text) tuples — one entry
        per section, still tagged with the plain source filename.
        """
        sections = []
        for filename, text in documents:
            for section_text in split_into_sections(text):
                sections.append((filename, section_text))
        return sections

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, sections):
        """
        TODO (Phase 1):
        Build a tiny inverted index mapping lowercase words to the section
        chunks they appear in (grouped by source filename).

        Example structure:
        {
            "token": ["AUTH.md", "API_REFERENCE.md"],
            "database": ["DATABASE.md"]
        }

        Keep this simple: split on whitespace, lowercase tokens,
        ignore punctuation if needed.
        """
        index = {}
        for filename, text in sections:
            # Tokenize: split text into words and lowercase them
            tokens = text.lower().split()
            for token in tokens:
                # Clean up punctuation
                token = token.strip('.,!?;:()')
                if token and token not in STOPWORDS:
                    if token not in index:
                        index[token] = []
                    # Add filename if not already present
                    if filename not in index[token]:
                        index[token].append(filename)
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        TODO (Phase 1):
        Return a simple relevance score for how well the text matches the query.

        Suggested baseline:
        - Convert query into lowercase words
        - Count how many appear in the text
        - Return the count as the score
        """

        query_tokens = (t.strip('.,!?;:()') for t in query.lower().split())
        text_tokens = (t.strip('.,!?;:()') for t in text.lower().split())
        query_counter = Counter(t for t in query_tokens if t and t not in STOPWORDS)
        text_counter = Counter(t for t in text_tokens if t and t not in STOPWORDS)

        # Sum of minimum counts for each token
        score = sum((query_counter & text_counter).values())
        return score

    def retrieve(self, query, top_k=5):
        """
        TODO (Phase 1):
        Use the index and scoring function to select relevant section snippets,
        walking ranked sections until top_k distinct source files are covered.
        Each file may contribute up to SECTION_CAP_PER_FILE of its highest
        scoring sections, so a multi-section answer isn't truncated down to
        a single section.

        Return a list of (filename, text) sorted by score descending.
        """
        raw_tokens = (t.strip('.,!?;:()') for t in query.lower().split())
        query_tokens = [t for t in raw_tokens if t and t not in STOPWORDS]

        candidates = (s for s in self.sections if any(s[0] in self.index.get(t, []) for t in query_tokens))
        scored = ((filename, text, self.score_document(query, text)) for filename, text in candidates)

        # Guardrail: drop sections whose overlap with the query is too weak
        # to trust, so retrieve() returns [] (triggering "I do not know")
        # instead of noisy, barely-related snippets.
        confident = [
            (filename, text, score) for filename, text, score in scored
            if query_tokens and score / len(query_tokens) >= MIN_RELEVANCE_RATIO
        ]

        ranked = sorted(confident, key=lambda s: s[2], reverse=True)

        results = []
        section_counts = {}
        distinct_files = set()
        for filename, text, score in ranked:
            if filename not in distinct_files:
                if len(distinct_files) >= top_k:
                    break
                distinct_files.add(filename)
            if section_counts.get(filename, 0) >= SECTION_CAP_PER_FILE:
                continue
            section_counts[filename] = section_counts.get(filename, 0) + 1
            results.append((filename, text))
        return results

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        formatted = []
        for filename, text in snippets:
            formatted.append(f"[{filename}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
