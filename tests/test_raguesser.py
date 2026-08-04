import pytest
import os
import tempfile
import shutil
from raguesser import RAGuesser, split_into_sections, STOPWORDS


# =====================================================================
# Fixtures: Set up temporary docs folders for testing
# =====================================================================

@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory with test documents."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def docs_with_binary_search(temp_docs_dir):
    """Create test docs about binary search and linear search."""
    doc1 = """Binary search is an efficient algorithm.

It divides the search space in half with each guess.

You can find any number in a sorted list using binary search."""

    doc2 = """Linear search checks each element one by one.

It is less efficient than binary search.

Linear search works on unsorted lists too."""

    with open(os.path.join(temp_docs_dir, "binary.md"), "w") as f:
        f.write(doc1)
    with open(os.path.join(temp_docs_dir, "linear.md"), "w") as f:
        f.write(doc2)

    return temp_docs_dir


@pytest.fixture
def docs_with_multiple_files(temp_docs_dir):
    """Create test docs with multiple files and sections."""
    files = {
        "auth.md": "Authentication is important.\n\nPassword hashing keeps users safe.\n\nUse strong passwords.",
        "database.md": "Database design is critical.\n\nIndexes speed up queries.\n\nNormalization prevents data redundancy.",
        "api.md": "APIs allow communication.\n\nREST APIs use HTTP methods.\n\nAuthentication protects API endpoints.",
    }

    for filename, content in files.items():
        with open(os.path.join(temp_docs_dir, filename), "w") as f:
            f.write(content)

    return temp_docs_dir


@pytest.fixture
def raguesser_with_docs(docs_with_binary_search):
    """Create a RAGuesser instance with test documents."""
    return RAGuesser(docs_folder=docs_with_binary_search)


# =====================================================================
# Tests: split_into_sections helper
# =====================================================================

def test_split_single_paragraph():
    text = "This is a single paragraph."
    sections = split_into_sections(text)
    assert sections == ["This is a single paragraph."]


def test_split_multiple_paragraphs():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    sections = split_into_sections(text)
    assert len(sections) == 3
    assert sections[0] == "First paragraph."
    assert sections[1] == "Second paragraph."
    assert sections[2] == "Third paragraph."


def test_split_ignores_extra_whitespace():
    text = "\n\nFirst.\n\n\n\nSecond.\n\n"
    sections = split_into_sections(text)
    assert len(sections) == 2
    assert sections[0] == "First."
    assert sections[1] == "Second."


def test_split_handles_windows_line_endings():
    text = "First.\r\n\r\nSecond."
    sections = split_into_sections(text)
    assert len(sections) == 2
    assert sections[0] == "First."
    assert sections[1] == "Second."


def test_split_strips_leading_trailing_whitespace():
    text = "   First.   \n\n   Second.   "
    sections = split_into_sections(text)
    assert sections[0] == "First."
    assert sections[1] == "Second."


def test_split_empty_string_returns_empty_list():
    text = ""
    sections = split_into_sections(text)
    assert sections == []


def test_split_only_whitespace_returns_empty_list():
    text = "\n\n\n"
    sections = split_into_sections(text)
    assert sections == []


# =====================================================================
# Tests: Document Loading
# =====================================================================

def test_load_documents_from_folder(docs_with_binary_search):
    rg = RAGuesser(docs_folder=docs_with_binary_search)
    assert len(rg.documents) == 2
    filenames = {doc[0] for doc in rg.documents}
    assert "binary.md" in filenames
    assert "linear.md" in filenames


def test_load_documents_ignores_non_text_files(temp_docs_dir):
    # Create a markdown file
    with open(os.path.join(temp_docs_dir, "doc.md"), "w") as f:
        f.write("Content here")

    # Create a non-text file that should be ignored
    with open(os.path.join(temp_docs_dir, "image.png"), "wb") as f:
        f.write(b"PNG\x00")

    rg = RAGuesser(docs_folder=temp_docs_dir)
    # Should only load the markdown file
    assert len(rg.documents) == 1
    assert rg.documents[0][0] == "doc.md"


def test_load_documents_preserves_content(docs_with_binary_search):
    rg = RAGuesser(docs_folder=docs_with_binary_search)

    for filename, text in rg.documents:
        if filename == "binary.md":
            assert "Binary search" in text
            assert "efficient" in text


def test_load_documents_empty_folder(temp_docs_dir):
    rg = RAGuesser(docs_folder=temp_docs_dir)
    assert rg.documents == []


# =====================================================================
# Tests: Section Building
# =====================================================================

def test_build_sections_splits_documents(raguesser_with_docs):
    # binary.md has 3 paragraphs, linear.md has 3 paragraphs = 6 sections
    assert len(raguesser_with_docs.sections) >= 6


def test_build_sections_preserves_filename(raguesser_with_docs):
    filenames = {section[0] for section in raguesser_with_docs.sections}
    assert "binary.md" in filenames
    assert "linear.md" in filenames


def test_build_sections_each_section_has_content(raguesser_with_docs):
    for filename, text in raguesser_with_docs.sections:
        assert isinstance(filename, str)
        assert isinstance(text, str)
        assert len(text) > 0


# =====================================================================
# Tests: Index Building
# =====================================================================

def test_build_index_creates_inverted_index(raguesser_with_docs):
    index = raguesser_with_docs.index
    assert isinstance(index, dict)
    assert len(index) > 0


def test_build_index_maps_tokens_to_files(raguesser_with_docs):
    index = raguesser_with_docs.index

    # "binary" should map to binary.md
    if "binary" in index:
        assert "binary.md" in index["binary"]

    # "linear" should map to linear.md
    if "linear" in index:
        assert "linear.md" in index["linear"]


def test_build_index_lowercases_tokens(raguesser_with_docs):
    index = raguesser_with_docs.index
    # All tokens should be lowercase
    for token in index.keys():
        assert token == token.lower()


def test_build_index_excludes_stopwords(raguesser_with_docs):
    index = raguesser_with_docs.index
    for stopword in ["the", "a", "is", "it"]:
        assert stopword not in index


def test_build_index_removes_punctuation(raguesser_with_docs):
    index = raguesser_with_docs.index
    # Tokens should not have trailing punctuation
    for token in index.keys():
        assert not token.endswith(".")
        assert not token.endswith(",")
        assert not token.endswith("!")
        assert not token.endswith("?")


def test_build_index_from_simple_sections():
    sections = [
        ("file1.md", "hello world"),
        ("file2.md", "hello python"),
        ("file1.md", "world peace"),
    ]
    rg = RAGuesser.__new__(RAGuesser)
    index = rg.build_index(sections)

    assert "hello" in index
    assert "file1.md" in index["hello"]
    assert "file2.md" in index["hello"]
    assert "world" in index
    assert index["world"] == ["file1.md"]
    assert "peace" in index


# =====================================================================
# Tests: Document Scoring
# =====================================================================

def test_score_exact_match():
    rg = RAGuesser.__new__(RAGuesser)
    score = rg.score_document("binary search", "binary search algorithm")
    assert score > 0


def test_score_partial_match():
    rg = RAGuesser.__new__(RAGuesser)
    score1 = rg.score_document("binary search", "binary search algorithm")
    score2 = rg.score_document("binary", "binary search algorithm")
    assert score1 >= score2


def test_score_no_match():
    rg = RAGuesser.__new__(RAGuesser)
    score = rg.score_document("xyz abc", "binary search algorithm")
    assert score == 0


def test_score_ignores_stopwords():
    rg = RAGuesser.__new__(RAGuesser)
    # "is the" are stopwords, only "binary" should score
    score = rg.score_document("binary is the", "binary search algorithm")
    assert score > 0


def test_score_case_insensitive():
    rg = RAGuesser.__new__(RAGuesser)
    score1 = rg.score_document("Binary Search", "binary search algorithm")
    score2 = rg.score_document("binary search", "BINARY SEARCH ALGORITHM")
    assert score1 == score2


def test_score_counts_token_frequency():
    rg = RAGuesser.__new__(RAGuesser)
    # Query with "search" twice; text has "search" once
    score = rg.score_document("search search", "search algorithm")
    # Should count the minimum frequency: min(2, 1) = 1
    assert score == 1


def test_score_multiple_tokens():
    rg = RAGuesser.__new__(RAGuesser)
    score = rg.score_document("binary search", "binary and search algorithm")
    assert score == 2


def test_score_empty_query():
    rg = RAGuesser.__new__(RAGuesser)
    score = rg.score_document("", "binary search algorithm")
    assert score == 0


# =====================================================================
# Tests: Retrieval
# =====================================================================

def test_retrieve_returns_list(raguesser_with_docs):
    results = raguesser_with_docs.retrieve("binary search")
    assert isinstance(results, list)


def test_retrieve_returns_filename_text_tuples(raguesser_with_docs):
    results = raguesser_with_docs.retrieve("binary search")
    for item in results:
        assert isinstance(item, tuple)
        assert len(item) == 2
        filename, text = item
        assert isinstance(filename, str)
        assert isinstance(text, str)


def test_retrieve_relevant_results(raguesser_with_docs):
    results = raguesser_with_docs.retrieve("binary search")
    # Should find binary.md sections
    filenames = [r[0] for r in results]
    assert "binary.md" in filenames


def test_retrieve_top_k_limits_files(docs_with_multiple_files):
    rg = RAGuesser(docs_folder=docs_with_multiple_files)
    results = rg.retrieve("password authentication database", top_k=2)

    distinct_files = len(set(r[0] for r in results))
    assert distinct_files <= 2


def test_retrieve_respects_section_cap_per_file(docs_with_multiple_files):
    rg = RAGuesser(docs_folder=docs_with_multiple_files)
    results = rg.retrieve("database", top_k=10)

    # Count sections per file
    file_counts = {}
    for filename, _ in results:
        file_counts[filename] = file_counts.get(filename, 0) + 1

    # Each file should contribute at most SECTION_CAP_PER_FILE sections
    from raguesser import SECTION_CAP_PER_FILE
    for count in file_counts.values():
        assert count <= SECTION_CAP_PER_FILE


def test_retrieve_empty_results_for_gibberish():
    # Create a raguesser with test docs
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "doc.md"), "w") as f:
        f.write("Binary search is efficient.")

    rg = RAGuesser(docs_folder=temp_dir)
    results = rg.retrieve("xyzabc qwerty poiuyt")

    shutil.rmtree(temp_dir)
    # Should return empty or very minimal results (stopped by MIN_RELEVANCE_RATIO)
    assert len(results) == 0


def test_retrieve_no_stopword_only_query():
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "doc.md"), "w") as f:
        f.write("Some content here.")

    rg = RAGuesser(docs_folder=temp_dir)
    results = rg.retrieve("the is a")

    shutil.rmtree(temp_dir)
    # Query is all stopwords, should return empty
    assert len(results) == 0


def test_retrieve_scores_ranked(docs_with_multiple_files):
    rg = RAGuesser(docs_folder=docs_with_multiple_files)
    results = rg.retrieve("password database index", top_k=10)

    # Results should be present and organized by relevance
    assert len(results) > 0


def test_retrieve_default_top_k():
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "doc.md"), "w") as f:
        f.write("Binary search. Linear search. Hash search. Tree search.")

    rg = RAGuesser(docs_folder=temp_dir)
    results = rg.retrieve("search")

    shutil.rmtree(temp_dir)
    # Default top_k is 5
    assert len(results) >= 1


# =====================================================================
# Tests: Retrieval-Only Answering
# =====================================================================

def test_answer_retrieval_only_returns_string(raguesser_with_docs):
    answer = raguesser_with_docs.answer_retrieval_only("binary search")
    assert isinstance(answer, str)


def test_answer_retrieval_only_with_results(raguesser_with_docs):
    answer = raguesser_with_docs.answer_retrieval_only("binary search")
    # Should contain content or the "I do not know" message
    assert len(answer) > 0


def test_answer_retrieval_only_includes_filenames(raguesser_with_docs):
    answer = raguesser_with_docs.answer_retrieval_only("binary search")
    # If we have results, filenames should be included in brackets
    if "I do not know" not in answer:
        assert "[" in answer and "]" in answer


def test_answer_retrieval_only_unknown_query(raguesser_with_docs):
    answer = raguesser_with_docs.answer_retrieval_only("xyzabc gibberish")
    assert "I do not know" in answer


def test_answer_retrieval_only_custom_top_k(raguesser_with_docs):
    answer1 = raguesser_with_docs.answer_retrieval_only("binary", top_k=1)
    answer2 = raguesser_with_docs.answer_retrieval_only("binary", top_k=10)
    # Both should return strings (exact content may vary)
    assert isinstance(answer1, str)
    assert isinstance(answer2, str)


# =====================================================================
# Tests: RAG Answering (with mock LLM client)
# =====================================================================

class MockLLMClient:
    """Mock LLM client for testing RAG mode."""
    def answer_from_snippets(self, query, snippets):
        # Return a formatted answer based on snippets
        if not snippets:
            return "No snippets provided."
        return f"Based on {len(snippets)} snippets: OK"


def test_answer_rag_requires_llm_client():
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, "doc.md"), "w") as f:
        f.write("Test content.")

    rg = RAGuesser(docs_folder=temp_dir)

    with pytest.raises(RuntimeError, match="LLM client"):
        rg.answer_rag("test query")

    shutil.rmtree(temp_dir)


def test_answer_rag_with_client(docs_with_binary_search):
    client = MockLLMClient()
    rg = RAGuesser(docs_folder=docs_with_binary_search, llm_client=client)

    answer = rg.answer_rag("binary search")
    assert isinstance(answer, str)


def test_answer_rag_calls_client_with_snippets(docs_with_binary_search):
    client = MockLLMClient()
    rg = RAGuesser(docs_folder=docs_with_binary_search, llm_client=client)

    answer = rg.answer_rag("binary search", top_k=2)
    # Mock should return a message about snippets
    assert "snippet" in answer.lower() or "I do not know" in answer


def test_answer_rag_unknown_query(docs_with_binary_search):
    client = MockLLMClient()
    rg = RAGuesser(docs_folder=docs_with_binary_search, llm_client=client)

    answer = rg.answer_rag("xyzabc gibberish")
    assert "I do not know" in answer


# =====================================================================
# Tests: Full Corpus Text
# =====================================================================

def test_full_corpus_text_concatenates_all_docs(docs_with_binary_search):
    rg = RAGuesser(docs_folder=docs_with_binary_search)
    corpus = rg.full_corpus_text()

    assert isinstance(corpus, str)
    assert "binary" in corpus.lower()
    assert "linear" in corpus.lower()


def test_full_corpus_text_empty_for_no_docs(temp_docs_dir):
    rg = RAGuesser(docs_folder=temp_docs_dir)
    corpus = rg.full_corpus_text()

    assert corpus == ""


def test_full_corpus_text_joined_with_paragraphs(docs_with_binary_search):
    rg = RAGuesser(docs_folder=docs_with_binary_search)
    corpus = rg.full_corpus_text()

    # Documents should be joined with "\n\n"
    assert "\n\n" in corpus


# =====================================================================
# Tests: RAGuesser Initialization
# =====================================================================

def test_raguesser_init_loads_and_indexes(docs_with_binary_search):
    rg = RAGuesser(docs_folder=docs_with_binary_search)

    assert rg.docs_folder == docs_with_binary_search
    assert len(rg.documents) > 0
    assert len(rg.sections) > 0
    assert isinstance(rg.index, dict)
    assert rg.llm_client is None


def test_raguesser_init_with_llm_client(docs_with_binary_search):
    client = MockLLMClient()
    rg = RAGuesser(docs_folder=docs_with_binary_search, llm_client=client)

    assert rg.llm_client is client


def test_raguesser_init_nonexistent_folder():
    # Should handle gracefully (empty docs)
    rg = RAGuesser(docs_folder="/nonexistent/path/to/docs")
    assert rg.documents == []
    assert rg.sections == []
    assert rg.index == {}


# =====================================================================
# Tests: Integration / End-to-End
# =====================================================================

def test_end_to_end_query_workflow(docs_with_multiple_files):
    """Test the full workflow: load docs, index, retrieve, answer."""
    rg = RAGuesser(docs_folder=docs_with_multiple_files)

    # Query about authentication
    results = rg.retrieve("authentication password", top_k=3)

    # Should find relevant sections
    assert len(results) > 0

    # Get retrieval-only answer
    answer = rg.answer_retrieval_only("authentication password")
    assert isinstance(answer, str)
    assert len(answer) > 0


def test_end_to_end_with_multiple_queries(docs_with_multiple_files):
    """Test that the same RAGuesser instance handles multiple queries."""
    rg = RAGuesser(docs_folder=docs_with_multiple_files)

    answer1 = rg.answer_retrieval_only("database")
    answer2 = rg.answer_retrieval_only("authentication")
    answer3 = rg.answer_retrieval_only("xyz gibberish")

    # All should return valid answers
    assert isinstance(answer1, str)
    assert isinstance(answer2, str)
    assert "I do not know" in answer3


def test_different_docs_get_different_results():
    """Test that different documents produce different retrieval results."""
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    with open(os.path.join(temp_dir1, "doc.md"), "w") as f:
        f.write("Binary search is fast.")

    with open(os.path.join(temp_dir2, "doc.md"), "w") as f:
        f.write("Linear search is slow.")

    rg1 = RAGuesser(docs_folder=temp_dir1)
    rg2 = RAGuesser(docs_folder=temp_dir2)

    results1 = rg1.retrieve("binary fast")
    results2 = rg2.retrieve("binary fast")

    # rg1 should have results, rg2 should not
    assert len(results1) > 0
    assert len(results2) == 0

    shutil.rmtree(temp_dir1)
    shutil.rmtree(temp_dir2)
