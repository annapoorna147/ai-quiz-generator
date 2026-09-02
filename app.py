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
    st.error("❌ GEMINI_API_KEY not found. Please check your .env file.")
    st.stop()

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(timeout=30000)
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #777;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .stat-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.2);
        text-align: center;
        margin-bottom: 15px;
    }

    .stat-number {
        font-size: 30px;
        font-weight: 800;
    }

    .stat-label {
        font-size: 14px;
        color: #777;
    }

    .question-box {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.2);
        margin-bottom: 20px;
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
    "quiz_history": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def clear_answer_widgets():
    """Remove old answer widget states."""
    for key in list(st.session_state.keys()):
        if key.startswith("answer_"):
            del st.session_state[key]


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
    else:
        return "F"


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
    else:
        return "💪 Don't give up. Practice makes progress!"


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
- The answer must exactly match one of the options
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

        text = response.text.strip()

        # Remove accidental markdown fences
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

        quiz = json.loads(text)

        if not isinstance(quiz, list):
            raise ValueError("Invalid quiz format.")

        if len(quiz) != num_questions:
            raise ValueError("Incorrect number of questions.")

        for q in quiz:
            if (
                "question" not in q
                or "options" not in q
                or "answer" not in q
            ):
                raise ValueError("Invalid question structure.")

            if len(q["options"]) != 4:
                raise ValueError("Each question must have 4 options.")

            if q["answer"] not in q["options"]:
                raise ValueError("Answer does not match an option.")

        return quiz

    except Exception as e:
        st.error(f"❌ Failed to generate quiz: {e}")
        return []


def calculate_results():

    questions = st.session_state.questions
    answers = st.session_state.answers

    correct = 0
    wrong = 0
    unanswered = 0

    for i, question in enumerate(questions):

        selected = answers.get(i)

        if selected is None:
            unanswered += 1

        elif selected == question["answer"]:
            correct += 1

        else:
            wrong += 1

    total = len(questions)

    percentage = round((correct / total) * 100, 1) if total else 0

    st.session_state.correct = correct
    st.session_state.wrong = wrong
    st.session_state.unanswered = unanswered
    st.session_state.score = correct
    st.session_state.percentage = percentage
    st.session_state.grade = get_grade(percentage)
    st.session_state.submitted = True


def save_history():

    if st.session_state.history_saved:
        return

    questions = st.session_state.questions

    if not questions:
        return

    # Get topic from session state
    topic = st.session_state.get("quiz_topic", "Custom Quiz")

    history_entry = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Topic": topic,
        "Difficulty": st.session_state.get("quiz_difficulty", "Unknown"),
        "Questions": len(questions),
        "Score": st.session_state.score,
        "Percentage": st.session_state.percentage,
        "Grade": st.session_state.grade,
        "Correct": st.session_state.correct,
        "Wrong": st.session_state.wrong,
        "Unanswered": st.session_state.unanswered
    }

    st.session_state.quiz_history.insert(0, history_entry)

    st.session_state.history_saved = True


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


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🧠 AI Quiz Generator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Create intelligent quizzes powered by Gemini AI</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Quiz Settings")

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

    if category == "✏️ Custom Topic":

        custom_topic = st.text_input(
            "Enter your topic",
            placeholder="Example: Operating Systems"
        )

        topic = custom_topic if custom_topic else "General Knowledge"

    else:

        topic = re.sub(
            r"^[^\w\s]+ ",
            "",
            category
        )

    difficulty = st.selectbox(
        "🎯 Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    num_questions = st.selectbox(
        "📝 Number of Questions",
        [3, 5, 7, 10],
        index=1
    )

    time_per_question = st.selectbox(
        "⏱️ Time Per Question",
        [30, 60, 90, 120],
        index=1
    )

    total_time = num_questions * time_per_question

    st.info(
        f"⏱️ Total quiz time: **{total_time // 60} min "
        f"{total_time % 60} sec**"
    )

    generate_button = st.button(
        "🚀 Generate Quiz",
        use_container_width=True
    )


# =========================================================
# GENERATE QUIZ
# =========================================================

if generate_button:

    clear_answer_widgets()

    with st.spinner("🤖 Generating your quiz..."):

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
# QUIZ ACTIVE
# =========================================================

if st.session_state.questions and not st.session_state.submitted:

    questions = st.session_state.questions
    current = st.session_state.current_question
    total_questions = len(questions)

    # -----------------------------------------------------
    # TIMER
    # -----------------------------------------------------

    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(
        0,
        st.session_state.quiz_duration - elapsed
    )

    minutes = remaining // 60
    seconds = remaining % 60

    if remaining == 0:

        st.warning("⏰ Time's up!")

        calculate_results()
        save_history()

        st.rerun()

    # -----------------------------------------------------
    # TOP STATS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Question",
            f"{current + 1} / {total_questions}"
        )

    with col2:
        st.metric(
            "Progress",
            f"{int(((current + 1) / total_questions) * 100)}%"
        )

    with col3:
        st.metric(
            "Time Left",
            f"{minutes:02d}:{seconds:02d}"
        )

    st.progress(
        (current + 1) / total_questions
    )

    st.markdown("---")

    # -----------------------------------------------------
    # QUESTION
    # -----------------------------------------------------

    question = questions[current]

    st.markdown(
        f"""
        <div class="question-box">
            <h3>Question {current + 1}</h3>
            <p>{question["question"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    selected_answer = st.radio(
        "Choose your answer:",
        question["options"],
        index=None,
        key=f"answer_{current}"
    )

    if selected_answer is not None:

        st.session_state.answers[current] = selected_answer

    st.markdown("")

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:

        if current > 0:

            if st.button(
                "⬅️ Previous",
                use_container_width=True
            ):

                st.session_state.current_question -= 1
                st.rerun()

    with col2:

        st.write("")

    with col3:

        if current < total_questions - 1:

            if st.button(
                "Next ➡️",
                use_container_width=True
            ):

                st.session_state.current_question += 1
                st.rerun()

        else:

            if st.button(
                "🏁 Submit Quiz",
                use_container_width=True
            ):

                calculate_results()
                save_history()

                st.rerun()

    # -----------------------------------------------------
    # AUTO REFRESH TIMER
    # -----------------------------------------------------

    time.sleep(1)
    st.rerun()


# =========================================================
# RESULTS
# =========================================================

elif st.session_state.submitted:

    save_history()

    st.success("🎉 Quiz Completed!")

    st.markdown("## 📊 Performance Dashboard")

    # -----------------------------------------------------
    # MAIN STATS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🏆 Score",
            f"{st.session_state.score} / {len(st.session_state.questions)}"
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
        st.session_state.percentage / 100
    )

    st.markdown(
        f"### {get_performance_message(st.session_state.percentage)}"
    )

    # -----------------------------------------------------
    # ANSWER BREAKDOWN
    # -----------------------------------------------------

    st.markdown("### 📋 Answer Breakdown")

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
    # REVIEW
    # -----------------------------------------------------

    st.markdown("### 🔍 Detailed Review")

    for i, question in enumerate(
        st.session_state.questions
    ):

        selected = st.session_state.answers.get(i)

        with st.expander(
            f"Question {i + 1}: {question['question']}"
        ):

            if selected == question["answer"]:

                st.success(
                    f"✅ Your answer: {selected}"
                )

            elif selected is None:

                st.warning(
                    "⚪ You did not answer this question."
                )

            else:

                st.error(
                    f"❌ Your answer: {selected}"
                )

                st.info(
                    f"✅ Correct answer: {question['answer']}"
                )

    # -----------------------------------------------------
    # NEW QUIZ
    # -----------------------------------------------------

    st.markdown("")

    if st.button(
        "🔄 Start New Quiz",
        use_container_width=True
    ):

        start_new_quiz()
        st.rerun()


# =========================================================
# QUIZ HISTORY
# =========================================================

st.markdown("---")

st.markdown("## 📚 Quiz History")

history = st.session_state.quiz_history

if not history:

    st.info(
        "Your completed quizzes will appear here."
    )

else:

    # -----------------------------------------------------
    # HISTORY STATISTICS
    # -----------------------------------------------------

    total_attempts = len(history)

    average_percentage = round(
        sum(item["Percentage"] for item in history)
        / total_attempts,
        1
    )

    best_percentage = max(
        item["Percentage"] for item in history
    )

    total_questions = sum(
        item["Questions"] for item in history
    )

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

    st.markdown("### 📖 Previous Attempts")

    history_df = pd.DataFrame(history)

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # CLEAR HISTORY
    # -----------------------------------------------------

    st.markdown("")

    if st.button(
        "🗑️ Clear Quiz History"
    ):

        st.session_state.quiz_history = []

        st.success(
            "Quiz history cleared."
        )

        st.rerun()