"""
Gemini client wrapper used by DocuBot. (initially copied from module 4 tinker)
init() function is adapted from module 5 tinker.

Handles:
- Configuring the Gemini client from the GEMINI_API_KEY environment variable
- Naive "generation only" answers over the full docs corpus (Phase 0)
- RAG style answers that use only retrieved snippets (Phase 2)

Experiment with:
- Prompt wording
- Refusal conditions
- How strictly the model is instructed to use only the provided context
"""

import os
# from google import genai


# Directory where prompt templates live, relative to this file
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ folder."""
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class GeminiClient:
    """
    Simple wrapper around the Gemini model.

    Usage:
        client = GeminiClient()
        answer = client.naive_answer_over_full_docs(query, all_text)
        # or
        answer = client.answer_from_snippets(query, snippets)
    """

    def __init__(self, model_name: str = "gemini-flash-lite-latest", temperature: float = 0.2):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Create a .env file and set GEMINI_API_KEY=..."
            )

        # Import here so heuristic mode doesn't require the dependency at import time.
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = float(temperature)


    def answer_keywords(self):
        """
        Call the Gemini model to create keywords/phrases that will be used to
        retrieve documents. The output of this function will be the input of the
        RAG retrieval function for obtaining documents.
        """
        try:
            merged_prompt = _load_prompt("keyword_system.txt").strip()
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=merged_prompt,
            )
            return (response.text or "").strip()
        except Exception as e:
            return f"API error — could not generate content. ({type(e).__name__}: {e})"


    def answer_feedback(self, mode, snippets, game_state):
        """
        Generate an answer using the retrieved snippets.

        mode: whether the feedback is being given during or after the game is finished
        snippets: list of (filename, text) tuples selected by RAGuesser.retrieve
        game_state: the current game state (should be formatted beforehand through logic_utils.retrieve_formatted_stats())

        The prompt:
        - Shows each snippet with its filename
        - Instructs the model to generate feedback based on these snippets and the game's state
        - Requires an explicit "I do not know" refusal when needed
        """

        if not snippets:
            return "I do not know based on the docs I have."

        context_blocks = []
        for filename, text in snippets:
            block = f"File: {filename}\n{text}\n"
            context_blocks.append(block)
        context = "\n\n".join(context_blocks)
        system_prompt = _load_prompt("retrieval_system_midgame.txt") if mode == "midgame" else _load_prompt("retrieval_system_postgame.txt")
        user_prompt = _load_prompt("retrieval_user.txt")


        try:
            merged_prompt = f"{system_prompt}\n\n{user_prompt}".strip().format(STATE=game_state, SNIPPETS=context)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=merged_prompt,
            )
            return (response.text or "").strip()
        except Exception as e:
            return f"API error — could not generate content. ({type(e).__name__}: {e})"
