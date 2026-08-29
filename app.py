import streamlit as st
import os
import json
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="centered"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 44px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .info-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 20px;
    }

    .result-card {
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin: 20px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🧠 AI Quiz Generator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Learn • Practice • Improve</div>',
    unsafe_allow_html=True
)


# =========================================================
# CHECK API KEY
# =========================================================

if not API_KEY:

    st.error("❌ Gemini API key not found.")

    st.info(
        "Add GEMINI_API_KEY=your_key_here to your .env file."
    )

    st.stop()


# =========================================================
# GEMINI CLIENT
# =========================================================

try:

    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(
            timeout=30000
        )
    )

except Exception as e:

    st.error(f"❌ Gemini connection failed: {e}")

    st.stop()


# =========================================================
# SESSION STATE
# =========================================================

if "questions" not in st.session_state:
    st.session_state.questions = []

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "score" not in st.session_state:
    st.session_state.score = 0

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "quiz_duration" not in st.session_state:
    st.session_state.quiz_duration = 300


# =========================================================
# GENERATE QUIZ FUNCTION
# =========================================================

def generate_quiz(topic, difficulty, number_of_questions):

    prompt = f"""
You are an expert quiz creator.

Create a multiple-choice quiz about:

Topic: {topic}

Difficulty: {difficulty}

Number of questions: {number_of_questions}

Return ONLY valid JSON.

Use exactly this structure:

[
    {{
        "question": "Question text",
        "options": [
            "Option A",
            "Option B",
            "Option C",
            "Option D"
        ],
        "answer": "Correct option",
        "explanation": "Short explanation"
    }}
]

Rules:

1. Create exactly {number_of_questions} questions.
2. Every question must have exactly 4 options.
3. The answer must exactly match one option.
4. Questions must be relevant to {topic}.
5. Match the {difficulty} difficulty.
6. Give a short explanation.
7. Do not use Markdown.
8. Do not add text outside the JSON.
9. Return JSON only.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                ),
                max_output_tokens=4000
            )
        )

        text = response.text.strip()

        # Remove markdown code fences
        text = re.sub(
            r"```json",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"```",
            "",
            text
        )

        text = text.strip()

        # Extract JSON array
        start = text.find("[")
        end = text.rfind("]")

        if start == -1 or end == -1:

            raise ValueError(
                "Gemini did not return valid JSON."
            )

        text = text[start:end + 1]

        questions = json.loads(text)

        if not isinstance(questions, list):

            raise ValueError(
                "Invalid quiz format."
            )

        if len(questions) != number_of_questions:

            raise ValueError(
                f"Expected {number_of_questions} questions "
                f"but received {len(questions)}."
            )

        # Validate every question
        for question in questions:

            if "question" not in question:
                raise ValueError(
                    "Question text is missing."
                )

            if "options" not in question:
                raise ValueError(
                    "Options are missing."
                )

            if "answer" not in question:
                raise ValueError(
                    "Answer is missing."
                )

            if "explanation" not in question:

                question["explanation"] = (
                    "This is the correct answer."
                )

            if len(question["options"]) != 4:

                raise ValueError(
                    "Each question must have 4 options."
                )

            if question["answer"] not in question["options"]:

                raise ValueError(
                    "Answer does not match an option."
                )

        return questions, None

    except Exception as e:

        return None, str(e)


# =========================================================
# QUIZ GENERATION SETTINGS
# =========================================================

if not st.session_state.questions:

    st.subheader("⚙️ Create Your Quiz")

    topic = st.text_input(
        "📚 Topic",
        placeholder="Example: Python Programming"
    )

    difficulty = st.selectbox(
        "🎯 Difficulty",
        [
            "Easy",
            "Medium",
            "Hard"
        ]
    )

    number_of_questions = st.slider(
        "🔢 Number of Questions",
        min_value=3,
        max_value=10,
        value=5
    )

    st.markdown("### ⏱️ Quiz Time")

    time_per_question = st.selectbox(
        "Time per question",
        [
            30,
            60,
            90,
            120
        ],
        index=1,
        format_func=lambda x: f"{x} seconds"
    )

    if st.button(
        "🚀 Generate Quiz",
        type="primary",
        use_container_width=True
    ):

        if not topic.strip():

            st.warning(
                "⚠️ Please enter a topic first."
            )

        else:

            with st.spinner(
                "🧠 Gemini is creating your quiz..."
            ):

                questions, error = generate_quiz(
                    topic.strip(),
                    difficulty,
                    number_of_questions
                )

            if questions:

                st.session_state.questions = questions

                st.session_state.quiz_duration = (
                    number_of_questions * time_per_question
                )

                st.session_state.start_time = time.time()

                st.session_state.quiz_started = True

                st.session_state.submitted = False

                st.session_state.score = 0

                st.rerun()

            else:

                st.error(
                    "❌ Could not generate the quiz."
                )

                st.code(
                    error if error else "Unknown error."
                )


# =========================================================
# ACTIVE QUIZ
# =========================================================

if (
    st.session_state.questions
    and not st.session_state.submitted
):

    total_questions = len(
        st.session_state.questions
    )

    # -----------------------------------------------------
    # TIMER
    # -----------------------------------------------------

    elapsed_time = (
        time.time()
        - st.session_state.start_time
    )

    remaining_time = max(
        0,
        st.session_state.quiz_duration
        - int(elapsed_time)
    )

    minutes = remaining_time // 60
    seconds = remaining_time % 60

    # -----------------------------------------------------
    # TIMER DISPLAY
    # -----------------------------------------------------

    if remaining_time > 60:

        st.info(
            f"⏱️ Time remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )

    elif remaining_time > 0:

        st.warning(
            f"⚠️ Time remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )

    else:

        st.error(
            "⏰ Time's up! Submit your quiz."
        )


    # -----------------------------------------------------
    # PROGRESS
    # -----------------------------------------------------

    answered_questions = 0

    for i in range(total_questions):

        if st.session_state.get(
            f"answer_{i}"
        ) is not None:

            answered_questions += 1

    progress = (
        answered_questions / total_questions
    )

    st.progress(progress)

    st.caption(
        f"Progress: "
        f"{answered_questions}/{total_questions} answered"
    )


    # -----------------------------------------------------
    # QUIZ QUESTIONS
    # -----------------------------------------------------

    st.divider()

    st.subheader("📝 Your Quiz")

    for i, question in enumerate(
        st.session_state.questions
    ):

        st.markdown(
            f"### Question {i + 1} of {total_questions}"
        )

        st.write(
            question["question"]
        )

        st.radio(
            "Select your answer:",
            question["options"],
            index=None,
            key=f"answer_{i}"
        )

        st.divider()


    # -----------------------------------------------------
    # SUBMIT
    # -----------------------------------------------------

    if st.button(
        "✅ Submit Quiz",
        type="primary",
        use_container_width=True
    ):

        score = 0

        for i, question in enumerate(
            st.session_state.questions
        ):

            selected_answer = st.session_state.get(
                f"answer_{i}"
            )

            if selected_answer == question["answer"]:

                score += 1

        st.session_state.score = score

        st.session_state.submitted = True

        st.rerun()


    # -----------------------------------------------------
    # AUTO REFRESH TIMER
    # -----------------------------------------------------

    if remaining_time > 0:

        time.sleep(1)

        st.rerun()


# =========================================================
# RESULTS
# =========================================================

if (
    st.session_state.questions
    and st.session_state.submitted
):

    questions = st.session_state.questions

    total = len(questions)

    score = st.session_state.score

    percentage = (
        score / total
    ) * 100


    # -----------------------------------------------------
    # RESULT HEADER
    # -----------------------------------------------------

    st.divider()

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.subheader("🏆 Quiz Completed!")

    st.metric(
        "Score",
        f"{score} / {total}"
    )

    st.metric(
        "Percentage",
        f"{percentage:.0f}%"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # PERFORMANCE MESSAGE
    # -----------------------------------------------------

    if percentage >= 90:

        st.success(
            "🌟 Outstanding! You're a quiz master!"
        )

        st.balloons()

    elif percentage >= 75:

        st.success(
            "🎉 Excellent work! Keep it up!"
        )

    elif percentage >= 60:

        st.info(
            "👍 Good job! A little more practice will help."
        )

    elif percentage >= 40:

        st.warning(
            "📚 Keep practicing. You're getting there!"
        )

    else:

        st.error(
            "💪 Don't give up! Review the answers and try again."
        )


    # -----------------------------------------------------
    # PERFORMANCE BAR
    # -----------------------------------------------------

    st.subheader("📊 Performance")

    st.progress(
        percentage / 100
    )


    # -----------------------------------------------------
    # ANSWER REVIEW
    # -----------------------------------------------------

    st.subheader("📖 Answer Review")

    for i, question in enumerate(questions):

        selected_answer = st.session_state.get(
            f"answer_{i}"
        )

        st.markdown(
            f"### Question {i + 1}"
        )

        st.write(
            question["question"]
        )

        if selected_answer == question["answer"]:

            st.success(
                f"✅ Your answer: {selected_answer}"
            )

        else:

            st.error(
                f"❌ Your answer: "
                f"{selected_answer if selected_answer else 'Not answered'}"
            )

            st.info(
                f"Correct answer: {question['answer']}"
            )

        st.write(
            f"💡 {question['explanation']}"
        )

        st.divider()


    # -----------------------------------------------------
    # RESTART
    # -----------------------------------------------------

    if st.button(
        "🔄 Create Another Quiz",
        type="primary",
        use_container_width=True
    ):

        st.session_state.questions = []

        st.session_state.submitted = False

        st.session_state.score = 0

        st.session_state.quiz_started = False

        st.session_state.start_time = None

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "🧠 AI Quiz Generator • Python • Streamlit • Gemini AI"
)