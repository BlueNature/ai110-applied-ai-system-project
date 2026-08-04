import random
import streamlit as st
from logic_utils import check_guess, update_score, get_range_for_difficulty, parse_guess

#FIX: Refactored logic into logic_utils.py using agent mode

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

#FIX: Changed attempt limits for normal and hard
attempt_limit_map = {
    "Easy": 6,
    "Normal": 6,
    "Hard": 8,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# Stretch Goal 2: Add high score metric in the sidebar
st.sidebar.metric("🏆 High Score", st.session_state.get("high_score", 0))

#FIX: Changing difficulty no longer leaves the old secret/score/attempts in
#play; selecting a new difficulty now resets state and starts a fresh game
#with a secret drawn from the new difficulty's range
if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty

if difficulty != st.session_state.difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.score = 0
    st.rerun()

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

#FIX: Fixed off-by-one error for initialization attempt number
if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

# Stretch Goal 2: High score persists across games/difficulty changes within the session
if "high_score" not in st.session_state:
    st.session_state.high_score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("Make a guess")

#FIX: Changed hardcoded range to use actual difficulty range (low/high variables)
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
    #FIX: Guess range no longer stays at [1, 100] regardless of difficulty
    st.session_state.secret = random.randint(low, high)
    #FIX: Reset status so New Game is playable after a win/loss; clear stale history
    st.session_state.status = "playing"
    st.session_state.history = []
    # also choose to reset score
    st.session_state.score = 0
    st.success("New game started.")
    st.rerun()

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

        #FIX: Removed even-attempt str(secret) conversion that made guesses
        #unwinnable and produced wrong hints (int vs str comparison) every other turn
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
            # Stretch Goal 2: Record best winning score this session
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

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
