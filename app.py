import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
import re
from datetime import datetime
import pandas as pd
import time


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error(
        "🔐 Gemini API key not found.\n\n"
        "Please make sure your `.env` file contains "
        "`GEMINI_API_KEY`."
    )
    st.stop()

try:
    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=30000)
    )
except Exception:
    st.error(
        "⚠️ Unable to connect to the Gemini service. "
        "Please check your API configuration."
    )
    st.stop()


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
"""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}


/* =====================================================
   HERO
   ===================================================== */

.hero {
    padding: 32px 25px;
    border-radius: 22px;
    border: 1px solid rgba(128, 128, 128, 0.20);
    background: rgba(128, 128, 128, 0.035);
    text-align: center;
    margin-bottom: 30px;
}

.hero-title {
    font-size: 38px;
    font-weight: 800;
    margin-bottom: 10px;
}

.hero-text {
    color: #888;
    font-size: 17px;
}


/* =====================================================
   QUESTION CARD
   ===================================================== */

.question-card {
    padding: 28px;
    border-radius: 20px;
    border: 1px solid rgba(128, 128, 128, 0.20);
    background: rgba(128, 128, 128, 0.035);
    margin: 22px 0;
}

.question-card h2 {
    margin-bottom: 15px;
}

.question-card p {
    font-size: 18px;
    line-height: 1.6;
}


/* =====================================================
   HISTORY
   ===================================================== */

.history-title {
    font-size: 28px;
    font-weight: 750;
    margin-bottom: 12px;
}


/* =====================================================
   FOOTER
   ===================================================== */

.footer {
    text-align: center;
    color: #888;
    padding: 30px 0 10px 0;
    font-size: 14px;
}

</style>
""",
unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "questions": [],
    "current_question": 0,
    "answers": {},
    "submitted": False,
    "score": 0,
    "correct": 0,
    "wrong": 0,
    "unanswered": 0,
    "percentage": 0,
    "grade": "",
    "start_time": None,
    "quiz_duration": 0,
    "history_saved": False,
    "quiz_history": [],
    "quiz_topic": "",
    "quiz_difficulty": ""
}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def clear_answer_widgets():

    """
    Remove old answer widget states so that
    every new quiz starts fresh.
    """

    for key in list(st.session_state.keys()):

        if key.startswith("answer_"):

            del st.session_state[key]


# =========================================================
# GRADE FUNCTION
# =========================================================

def get_grade(percentage):

    if percentage >= 90:

        return "A+"

    elif percentage >= 80:

        return "A"

    elif percentage >= 70:

        return "B"

    elif percentage >= 60:

        return "C"

    elif percentage >= 50:

        return "D"

    return "F"


# =========================================================
# PERFORMANCE MESSAGE
# =========================================================

def get_performance_message(percentage):

    if percentage >= 90:

        return "🏆 Outstanding performance!"

    elif percentage >= 80:

        return "🌟 Excellent work!"

    elif percentage >= 70:

        return "👏 Great job!"

    elif percentage >= 60:

        return "👍 Good effort! Keep improving."

    elif percentage >= 50:

        return "📚 You're getting there. Keep practicing!"

    return "💪 Don't give up. Practice makes progress!"


# =========================================================
# GENERATE QUIZ
# =========================================================

def generate_quiz(topic, difficulty, num_questions):

    prompt = f"""
Create a multiple-choice quiz.

Topic: {topic}
Difficulty: {difficulty}
Number of questions: {num_questions}

Return ONLY valid JSON.

Use exactly this format:

[
  {{
    "question": "Question text",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "Correct option"
  }}
]

Rules:

- Exactly {num_questions} questions
- Exactly 4 options per question
- One correct answer
- The answer must exactly match one option
- No markdown
- No explanations
- Return JSON only
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

        if not response:

            raise ValueError(
                "Gemini returned no response."
            )

        if not response.text:

            raise ValueError(
                "Gemini returned an empty response."
            )

        text = response.text.strip()

        # Remove markdown code fences
        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"^```\s*",
            "",
            text
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

        text = text.strip()

        # Convert AI response to Python object
        quiz = json.loads(text)

        # -------------------------------------------------
        # Validate quiz
        # -------------------------------------------------

        if not isinstance(quiz, list):

            raise ValueError(
                "The AI returned an invalid quiz format."
            )

        if len(quiz) != num_questions:

            raise ValueError(
                f"Expected {num_questions} questions, "
                f"but received {len(quiz)}."
            )

        for index, question in enumerate(quiz):

            if not isinstance(question, dict):

                raise ValueError(
                    f"Question {index + 1} has an invalid format."
                )

            required_fields = [
                "question",
                "options",
                "answer"
            ]

            for field in required_fields:

                if field not in question:

                    raise ValueError(
                        f"Question {index + 1} is missing "
                        f"'{field}'."
                    )

            if not isinstance(
                question["options"],
                list
            ):

                raise ValueError(
                    f"Question {index + 1} has invalid options."
                )

            if len(question["options"]) != 4:

                raise ValueError(
                    f"Question {index + 1} must have exactly "
                    f"4 options."
                )

            if question["answer"] not in question["options"]:

                raise ValueError(
                    f"Question {index + 1} has an invalid "
                    f"correct answer."
                )

        return quiz

    except json.JSONDecodeError:

        st.error(
            "⚠️ The AI returned an unexpected format. "
            "Please try generating the quiz again."
        )

    except Exception as error:

        st.error(
            "❌ We couldn't generate your quiz."
        )

        with st.expander("Technical details"):

            st.code(str(error))

    return []


# =========================================================
# CALCULATE RESULTS
# =========================================================

def calculate_results():

    questions = st.session_state.questions

    answers = st.session_state.answers

    correct = 0

    wrong = 0

    unanswered = 0

    for index, question in enumerate(questions):

        selected = answers.get(index)

        if selected is None:

            unanswered += 1

        elif selected == question["answer"]:

            correct += 1

        else:

            wrong += 1

    total = len(questions)

    if total > 0:

        percentage = round(
            (correct / total) * 100,
            1
        )

    else:

        percentage = 0

    st.session_state.correct = correct

    st.session_state.wrong = wrong

    st.session_state.unanswered = unanswered

    st.session_state.score = correct

    st.session_state.percentage = percentage

    st.session_state.grade = get_grade(
        percentage
    )

    st.session_state.submitted = True


# =========================================================
# SAVE HISTORY
# =========================================================

def save_history():

    if st.session_state.history_saved:

        return

    questions = st.session_state.questions

    if not questions:

        return

    history_entry = {

        "Date": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),

        "Topic": st.session_state.quiz_topic,

        "Difficulty": st.session_state.quiz_difficulty,

        "Questions": len(questions),

        "Score": st.session_state.score,

        "Percentage": st.session_state.percentage,

        "Grade": st.session_state.grade,

        "Correct": st.session_state.correct,

        "Wrong": st.session_state.wrong,

        "Unanswered": st.session_state.unanswered
    }

    st.session_state.quiz_history.insert(
        0,
        history_entry
    )

    st.session_state.history_saved = True


# =========================================================
# START NEW QUIZ
# =========================================================

def start_new_quiz():

    clear_answer_widgets()

    st.session_state.questions = []

    st.session_state.current_question = 0

    st.session_state.answers = {}

    st.session_state.submitted = False

    st.session_state.score = 0

    st.session_state.correct = 0

    st.session_state.wrong = 0

    st.session_state.unanswered = 0

    st.session_state.percentage = 0

    st.session_state.grade = ""

    st.session_state.start_time = None

    st.session_state.quiz_duration = 0

    st.session_state.history_saved = False

    st.session_state.quiz_topic = ""

    st.session_state.quiz_difficulty = ""


# =========================================================
# HEADER
# =========================================================

st.markdown(
"""
<div class="hero">
    <div class="hero-title">
        🧠 AI Quiz Generator
    </div>
    <div class="hero-text">
        Learn smarter. Practice faster. Test your knowledge.
    </div>
</div>
""",
unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Quiz Settings")

    st.caption(
        "Customize your quiz before generating it."
    )

    # -----------------------------------------------------
    # CATEGORY
    # -----------------------------------------------------

    category = st.selectbox(
        "📚 Category",
        [
            "🐍 Python",
            "💻 Programming",
            "🧠 Data Structures",
            "🤖 Artificial Intelligence",
            "📊 Machine Learning",
            "🌐 Web Development",
            "🗄️ Databases",
            "🔢 Mathematics",
            "🔬 Science",
            "🌍 General Knowledge",
            "✏️ Custom Topic"
        ]
    )

    # -----------------------------------------------------
    # CUSTOM TOPIC
    # -----------------------------------------------------

    if category == "✏️ Custom Topic":

        custom_topic = st.text_input(
            "Enter your topic",
            placeholder="Example: Operating Systems"
        )

        topic = custom_topic.strip()

    else:

        topic = re.sub(
            r"^[^\w\s]+ ",
            "",
            category
        )

    # -----------------------------------------------------
    # DIFFICULTY
    # -----------------------------------------------------

    difficulty = st.selectbox(
        "🎯 Difficulty",
        [
            "Easy",
            "Medium",
            "Hard"
        ]
    )

    # -----------------------------------------------------
    # NUMBER OF QUESTIONS
    # -----------------------------------------------------

    num_questions = st.selectbox(
        "📝 Number of Questions",
        [
            3,
            5,
            7,
            10
        ],
        index=1
    )

    # -----------------------------------------------------
    # TIME PER QUESTION
    # -----------------------------------------------------

    time_per_question = st.selectbox(
        "⏱️ Time Per Question",
        [
            30,
            60,
            90,
            120
        ],
        index=1
    )

    total_time = (
        num_questions
        * time_per_question
    )

    total_minutes = total_time // 60

    total_seconds = total_time % 60

    if total_seconds:

        time_display = (
            f"{total_minutes} min "
            f"{total_seconds} sec"
        )

    else:

        time_display = (
            f"{total_minutes} min"
        )

    st.info(
        f"⏱️ Total quiz time: **{time_display}**"
    )

    # -----------------------------------------------------
    # GENERATE BUTTON
    # -----------------------------------------------------

    generate_button = st.button(
        "🚀 Generate Quiz",
        width="stretch",
        type="primary"
    )


# =========================================================
# GENERATE QUIZ
# =========================================================

if generate_button:

    if not topic:

        st.warning(
            "✏️ Please enter a topic before generating your quiz."
        )

    else:

        clear_answer_widgets()

        with st.spinner(
            "🤖 Creating your personalized quiz..."
        ):

            quiz = generate_quiz(
                topic,
                difficulty,
                num_questions
            )

        if quiz:

            st.session_state.questions = quiz

            st.session_state.current_question = 0

            st.session_state.answers = {}

            st.session_state.submitted = False

            st.session_state.score = 0

            st.session_state.correct = 0

            st.session_state.wrong = 0

            st.session_state.unanswered = 0

            st.session_state.percentage = 0

            st.session_state.grade = ""

            st.session_state.quiz_duration = total_time

            st.session_state.start_time = time.time()

            st.session_state.history_saved = False

            st.session_state.quiz_topic = topic

            st.session_state.quiz_difficulty = difficulty

            st.rerun()


# =========================================================
# ACTIVE QUIZ
# =========================================================

if (
    st.session_state.questions
    and not st.session_state.submitted
):

    questions = st.session_state.questions

    current = st.session_state.current_question

    total_questions = len(questions)

    # -----------------------------------------------------
    # TIMER
    # -----------------------------------------------------

    elapsed = int(
        time.time()
        - st.session_state.start_time
    )

    remaining = max(
        0,
        st.session_state.quiz_duration
        - elapsed
    )

    minutes = remaining // 60

    seconds = remaining % 60

    # -----------------------------------------------------
    # TIME EXPIRED
    # -----------------------------------------------------

    if remaining == 0:

        st.warning(
            "⏰ Time's up! Your quiz has been submitted."
        )

        calculate_results()

        save_history()

        st.rerun()

    # -----------------------------------------------------
    # QUIZ STATS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "📍 Question",
            f"{current + 1} / {total_questions}"
        )

    with col2:

        progress_percentage = int(
            (
                (current + 1)
                / total_questions
            )
            * 100
        )

        st.metric(
            "📈 Progress",
            f"{progress_percentage}%"
        )

    with col3:

        st.metric(
            "⏱️ Time Left",
            f"{minutes:02d}:{seconds:02d}"
        )

    st.progress(
        (current + 1)
        / total_questions
    )

    st.caption(
        f"📚 {st.session_state.quiz_topic}  •  "
        f"🎯 {st.session_state.quiz_difficulty}"
    )

    # -----------------------------------------------------
    # QUESTION
    # -----------------------------------------------------

    question = questions[current]

    question_text = str(
        question["question"]
    )

    st.markdown(
    f"""
    <div class="question-card">
        <h2>Question {current + 1}</h2>
        <p>{question_text}</p>
    </div>
    """,
    unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # ANSWER
    # -----------------------------------------------------

    selected_answer = st.radio(
        "Choose your answer:",
        question["options"],
        index=None,
        key=f"answer_{current}"
    )

    if selected_answer is not None:

        st.session_state.answers[current] = (
            selected_answer
        )

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    st.markdown("")

    nav1, nav2, nav3 = st.columns(
        [1, 1, 1]
    )

    with nav1:

        if current > 0:

            if st.button(
                "⬅️ Previous",
                width="stretch"
            ):

                st.session_state.current_question -= 1

                st.rerun()

    with nav2:

        answered_count = len(
            st.session_state.answers
        )

        st.caption(
            f"Answered: "
            f"{answered_count}/{total_questions}"
        )

    with nav3:

        if current < total_questions - 1:

            if st.button(
                "Next ➡️",
                width="stretch",
                type="primary"
            ):

                st.session_state.current_question += 1

                st.rerun()

        else:

            if st.button(
                "🏁 Submit Quiz",
                width="stretch",
                type="primary"
            ):

                calculate_results()

                save_history()

                st.rerun()

    # -----------------------------------------------------
    # TIMER REFRESH
    # -----------------------------------------------------

    time.sleep(1)

    st.rerun()


# =========================================================
# RESULTS DASHBOARD
# =========================================================

elif st.session_state.submitted:

    save_history()

    st.success(
        "🎉 Quiz completed successfully!"
    )

    st.markdown(
        "## 📊 Your Results"
    )

    st.caption(
        f"📚 {st.session_state.quiz_topic}  •  "
        f"🎯 {st.session_state.quiz_difficulty}"
    )

    # -----------------------------------------------------
    # MAIN RESULTS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🏆 Score",
            f"{st.session_state.score} / "
            f"{len(st.session_state.questions)}"
        )

    with col2:

        st.metric(
            "📈 Percentage",
            f"{st.session_state.percentage}%"
        )

    with col3:

        st.metric(
            "🎯 Grade",
            st.session_state.grade
        )

    with col4:

        st.metric(
            "✅ Correct",
            st.session_state.correct
        )

    st.progress(
        st.session_state.percentage
        / 100
    )

    st.markdown(
        f"### {get_performance_message(
            st.session_state.percentage
        )}"
    )

    # -----------------------------------------------------
    # BREAKDOWN
    # -----------------------------------------------------

    st.markdown(
        "### 📋 Answer Breakdown"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "✅ Correct",
            st.session_state.correct
        )

    with col2:

        st.metric(
            "❌ Wrong",
            st.session_state.wrong
        )

    with col3:

        st.metric(
            "⚪ Unanswered",
            st.session_state.unanswered
        )

    # -----------------------------------------------------
    # DETAILED REVIEW
    # -----------------------------------------------------

    st.markdown(
        "### 🔍 Detailed Review"
    )

    for i, question in enumerate(
        st.session_state.questions
    ):

        selected = st.session_state.answers.get(i)

        if selected == question["answer"]:

            icon = "✅"

        elif selected is None:

            icon = "⚪"

        else:

            icon = "❌"

        with st.expander(
            f"{icon} Question {i + 1}: "
            f"{question['question']}"
        ):

            if selected is None:

                st.warning(
                    "You did not answer this question."
                )

                st.info(
                    f"Correct answer: "
                    f"**{question['answer']}**"
                )

            elif selected == question["answer"]:

                st.success(
                    f"Your answer: "
                    f"**{selected}**"
                )

            else:

                st.error(
                    f"Your answer: "
                    f"**{selected}**"
                )

                st.info(
                    f"Correct answer: "
                    f"**{question['answer']}**"
                )

    # -----------------------------------------------------
    # NEW QUIZ
    # -----------------------------------------------------

    st.markdown("")

    if st.button(
        "🔄 Start New Quiz",
        width="stretch",
        type="primary"
    ):

        start_new_quiz()

        st.rerun()


# =========================================================
# QUIZ HISTORY
# =========================================================

st.markdown("---")

st.markdown(
"""
<div class="history-title">
    📚 Quiz History
</div>
""",
unsafe_allow_html=True
)

history = st.session_state.quiz_history


# =========================================================
# EMPTY HISTORY
# =========================================================

if not history:

    st.info(
        "📝 No quiz attempts yet. "
        "Generate your first quiz to start building "
        "your learning history."
    )


# =========================================================
# HISTORY EXISTS
# =========================================================

else:

    total_attempts = len(history)

    average_percentage = round(
        sum(
            item["Percentage"]
            for item in history
        )
        / total_attempts,
        1
    )

    best_percentage = max(
        item["Percentage"]
        for item in history
    )

    total_questions = sum(
        item["Questions"]
        for item in history
    )

    # -----------------------------------------------------
    # HISTORY STATS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "📝 Attempts",
            total_attempts
        )

    with col2:

        st.metric(
            "📊 Average",
            f"{average_percentage}%"
        )

    with col3:

        st.metric(
            "🏆 Best Score",
            f"{best_percentage}%"
        )

    with col4:

        st.metric(
            "❓ Questions",
            total_questions
        )

    # -----------------------------------------------------
    # HISTORY TABLE
    # -----------------------------------------------------

    st.markdown(
        "### 📖 Previous Attempts"
    )

    history_df = pd.DataFrame(
        history
    )

    st.dataframe(
        history_df,
        width="stretch",
        hide_index=True
    )

    # -----------------------------------------------------
    # CLEAR HISTORY
    # -----------------------------------------------------

    st.markdown("")

    if st.button(
        "🗑️ Clear Quiz History",
        width="content"
    ):

        st.session_state.quiz_history = []

        st.success(
            "Quiz history has been cleared."
        )

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
"""
<div class="footer">
    🧠 AI Quiz Generator
    <br>
    Learn • Practice • Improve
</div>
""",
unsafe_allow_html=True
)