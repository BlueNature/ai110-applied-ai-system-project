import random
import streamlit as st
from dotenv import load_dotenv
from logic_utils import (
    check_guess, update_score, get_range_for_difficulty, parse_guess,
    retrieve_formatted_stats, generate_feedback, collect_retrieved_files,
)
from raguesser import RAGuesser
from llm_client import GeminiClient

#FIX: Refactored logic into logic_utils.py using agent mode

load_dotenv()

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")


@st.cache_resource
def get_raguesser():
    return RAGuesser()


@st.cache_resource
def get_gemini_client():
    try:
        return GeminiClient()
    except RuntimeError:
        return None

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 6,
    "Hard": 8,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

st.sidebar.metric("🏆 High Score", st.session_state.get("high_score", 0))

if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty

if difficulty != st.session_state.difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.score = 0
    st.session_state.midgame_feedback = None
    st.session_state.postgame_feedback = None
    st.session_state.retrieved_files = []
    st.session_state.file_viewer_idx = 0
    st.rerun()

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "high_score" not in st.session_state:
    st.session_state.high_score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "midgame_feedback" not in st.session_state:
    st.session_state.midgame_feedback = None

if "postgame_feedback" not in st.session_state:
    st.session_state.postgame_feedback = None

if "retrieved_files" not in st.session_state:
    st.session_state.retrieved_files = []

if "file_viewer_idx" not in st.session_state:
    st.session_state.file_viewer_idx = 0

st.subheader("Make a guess")

#FIX: Reserve the info box's spot here, but populate it after the guess is
#processed so "Attempts left" reflects the current attempt instead of lagging
#one behind (the submit handler below increments attempts after this point)
info_box = st.empty()

#FIX: Reserve the debug panel's spot here, but populate it after the guess is
#processed so it reflects the latest state (creating the expander now keeps its
#position/open state stable; contents are written into this container below)
debug_box = st.expander("Developer Debug Info")

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.status = "playing"
    st.session_state.history = []
    # also choose to reset score
    st.session_state.score = 0
    st.session_state.midgame_feedback = None
    st.session_state.postgame_feedback = None
    st.session_state.retrieved_files = []
    st.session_state.file_viewer_idx = 0
    st.success("New game started.")
    st.rerun()

#FIX: Defined once and called from both the game-over gate below and the
#bottom fallthrough after a guess just ended the game, so the postgame
#button renders in the SAME run the game ends in (that run's gate check
#already ran, with the old "playing" status, before status flipped below) —
#without needing an st.rerun() that would cut off the win/loss message.
def render_postgame_feedback():
    if st.button("🧠 Get Feedback", key="postgame_feedback_btn"):
        game_state = retrieve_formatted_stats(
            difficulty, st.session_state.attempts, attempt_limit,
            st.session_state.secret, st.session_state.history, st.session_state.status,
        )
        feedback_text, snippets = generate_feedback(
            "postgame", get_raguesser(), get_gemini_client(), game_state,
        )
        st.session_state.postgame_feedback = feedback_text
        st.session_state.retrieved_files = collect_retrieved_files(snippets, get_raguesser())
        st.session_state.file_viewer_idx = 0

    if st.session_state.postgame_feedback:
        st.info(st.session_state.postgame_feedback)

        files = st.session_state.retrieved_files
        if files:
            st.markdown("**Sources used for this feedback:**")
            prev_col, next_col = st.columns(2)
            with prev_col:
                if st.button("⬅ Previous document", key="prev_doc_btn"):
                    st.session_state.file_viewer_idx = (st.session_state.file_viewer_idx - 1) % len(files)
            with next_col:
                if st.button("➡ Next document", key="next_doc_btn"):
                    st.session_state.file_viewer_idx = (st.session_state.file_viewer_idx + 1) % len(files)
            idx = st.session_state.file_viewer_idx
            filename, full_text = files[idx]
            st.caption(f"Document {idx + 1} of {len(files)}: {filename}")
            st.text_area("Full document text", full_text, height=300, key=f"doc_view_{idx}", disabled=True)

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    #FIX: Populate the reserved info box before stopping so it isn't left blank
    #on a rerun that lands here (attempts is already final/correct at this point)
    info_box.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {attempt_limit - st.session_state.attempts}"
    )
    #FIX: Populate the reserved debug panel before stopping too, so it keeps
    #showing the final state instead of rendering empty on the game-over rerun
    with debug_box:
        st.write("Secret:", st.session_state.secret)
        st.write("Attempts:", st.session_state.attempts)
        st.write("Score:", st.session_state.score)
        st.write("Difficulty:", difficulty)
        st.write("History:", st.session_state.history)

    render_postgame_feedback()
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        #FIX: Improper guesses no longer burn an attempt; only count valid guesses
        # however, will no longer append invalid guesses to history
        # st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            if st.session_state.score > st.session_state.high_score:
                st.session_state.high_score = st.session_state.score
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

#FIX: Populate the reserved info box after the guess is handled, so "Attempts
#left" reflects the latest attempt count instead of lagging one behind
info_box.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

#FIX: Populate the reserved debug panel after the guess is handled, so History
#and the other fields show the current attempt instead of lagging one behind
with debug_box:
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

#FIX: A guess submitted just above may have just set status to "won"/"lost"
#within this same run (the game-over gate above already passed earlier in
#this script execution). Guard explicitly so the mid-game button never shows
#once the game is actually over; the else branch below renders the postgame
#section immediately in this same run instead.
if st.session_state.status == "playing":
    if st.button("🧠 Get Feedback", key="midgame_feedback_btn"):
        game_state = retrieve_formatted_stats(
            difficulty, st.session_state.attempts, attempt_limit,
            st.session_state.secret, st.session_state.history, "playing",
        )
        st.session_state.midgame_feedback, _ = generate_feedback(
            "midgame", get_raguesser(), get_gemini_client(), game_state,
        )

    if st.session_state.midgame_feedback:
        st.info(st.session_state.midgame_feedback)
else:
    #FIX: The guess just submitted above may have just ended the game. The
    #gate at the top of this run already checked status while it was still
    #"playing" and skipped itself, so render the postgame section here too,
    #in this same run, instead of waiting for an unrelated future rerun.
    render_postgame_feedback()

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
