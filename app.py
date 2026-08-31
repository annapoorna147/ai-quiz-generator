import streamlit as st
import os
import json
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="centered"
)


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ Gemini API key not found.")
    st.info("Please add GEMINI_API_KEY to your .env file.")
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
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 46px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .quiz-card {
        padding: 25px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        margin: 20px 0;
    }

    .question-number {
        font-size: 15px;
        font-weight: 600;
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
    "submitted": False,
    "score": 0,
    "quiz_started": False,
    "start_time": None,
    "quiz_duration": 300,
    "topic": "",
    "difficulty": "Medium",
    "number_of_questions": 5,
    "time_per_question": 60,
    "current_question": 0,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🧠 AI Quiz Generator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Learn • Practice • Improve with AI</div>',
    unsafe_allow_html=True
)


# =========================================================
# GENERATE QUIZ
# =========================================================

def generate_quiz(
    topic,
    difficulty,
    number_of_questions
):

    prompt = f"""
You are an expert educational quiz creator.

Create a multiple-choice quiz.

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
3. The correct answer must exactly match one option.
4. Questions must be relevant to the topic.
5. Follow the requested difficulty.
6. Avoid duplicate questions.
7. Give a short explanation.
8. Return JSON only.
9. Do not use Markdown.
10. Do not add text outside the JSON.
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

        # Remove Markdown code fences
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

        # Find JSON array
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

        # Validate questions
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
                    "Every question must have exactly 4 options."
                )

            if question["answer"] not in question["options"]:

                raise ValueError(
                    "Correct answer does not match an option."
                )

        return questions, None

    except Exception as e:

        return None, str(e)


# =========================================================
# HOME / DASHBOARD
# =========================================================

if not st.session_state.questions:

    st.markdown(
        """
        <div class="quiz-card">

        <h3>🚀 Create Your AI-Powered Quiz</h3>

        <p>
        Choose a topic, difficulty and quiz size.
        Gemini AI will generate a personalized quiz for you.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("📚 Choose a Quiz Category")

    categories = [
        "🐍 Python",
        "💻 Programming",
        "🤖 Artificial Intelligence",
        "🧠 Machine Learning",
        "📊 Data Science",
        "🌐 Web Development",
        "🗄️ Database",
        "🔐 Cyber Security",
        "⚡ Electronics",
        "📐 Mathematics",
        "🔬 Science",
        "🌎 General Knowledge"
    ]

    selected_category = st.selectbox(
        "Select a category",
        categories
    )

    custom_topic = st.text_input(
        "✏️ Or enter your own topic",
        placeholder="Example: Operating Systems"
    )

    # Remove emoji from category
    category_topic = re.sub(
        r"^[^\w\s]+ ",
        "",
        selected_category
    )

    if custom_topic.strip():

        final_topic = custom_topic.strip()

    else:

        final_topic = category_topic


    # =====================================================
    # SETTINGS
    # =====================================================

    st.subheader("⚙️ Quiz Settings")

    col1, col2 = st.columns(2)

    with col1:

        difficulty = st.selectbox(
            "🎯 Difficulty",
            [
                "Easy",
                "Medium",
                "Hard"
            ],
            index=1
        )

    with col2:

        number_of_questions = st.selectbox(
            "🔢 Questions",
            [
                3,
                5,
                7,
                10
            ],
            index=1
        )


    # =====================================================
    # TIMER
    # =====================================================

    st.subheader("⏱️ Time Settings")

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

    total_time = (
        number_of_questions
        * time_per_question
    )

    minutes = total_time // 60
    seconds = total_time % 60

    st.info(
        f"⏱️ Total quiz time: "
        f"{minutes} min {seconds} sec"
    )


    # =====================================================
    # GENERATE BUTTON
    # =====================================================

    if st.button(
        "🚀 Generate AI Quiz",
        type="primary",
        use_container_width=True
    ):

        if not final_topic.strip():

            st.warning(
                "⚠️ Please enter a topic."
            )

        else:

            with st.spinner(
                "🧠 Gemini AI is creating your quiz..."
            ):

                questions, error = generate_quiz(
                    final_topic,
                    difficulty,
                    number_of_questions
                )

            if questions:

                st.session_state.questions = questions

                st.session_state.topic = final_topic

                st.session_state.difficulty = difficulty

                st.session_state.number_of_questions = (
                    number_of_questions
                )

                st.session_state.time_per_question = (
                    time_per_question
                )

                st.session_state.quiz_duration = (
                    total_time
                )

                st.session_state.start_time = time.time()

                st.session_state.quiz_started = True

                st.session_state.submitted = False

                st.session_state.score = 0

                st.session_state.current_question = 0

                st.rerun()

            else:

                st.error(
                    "❌ Could not generate quiz."
                )

                st.code(
                    error
                    if error
                    else "Unknown error."
                )


# =========================================================
# ACTIVE QUIZ
# =========================================================

if (
    st.session_state.questions
    and not st.session_state.submitted
):

    questions = st.session_state.questions

    total_questions = len(questions)

    current = st.session_state.current_question

    # Safety check
    if current < 0:

        current = 0

        st.session_state.current_question = 0

    if current >= total_questions:

        current = total_questions - 1

        st.session_state.current_question = (
            total_questions - 1
        )


    # =====================================================
    # QUIZ HEADER
    # =====================================================

    st.markdown(
        f"### 📚 {st.session_state.topic}"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.caption(
            f"🎯 {st.session_state.difficulty}"
        )

    with col2:

        st.caption(
            f"Question {current + 1} of {total_questions}"
        )


    # =====================================================
    # TIMER
    # =====================================================

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


    if remaining_time > 60:

        st.info(
            f"⏱️ Time Remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )

    elif remaining_time > 0:

        st.warning(
            f"⚠️ Time Remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )

    else:

        st.error(
            "⏰ Time's up! Please submit your quiz."
        )


    # =====================================================
    # PROGRESS
    # =====================================================

    progress = (
        (current + 1)
        / total_questions
    )

    st.progress(progress)

    st.caption(
        f"Quiz Progress: "
        f"{current + 1}/{total_questions}"
    )


    # =====================================================
    # QUESTION CARD
    # =====================================================

    question = questions[current]

    st.markdown(
        '<div class="quiz-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        f"### Question {current + 1}"
    )

    st.write(
        question["question"]
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # =====================================================
    # ANSWER
    # =====================================================

    st.radio(
        "Choose your answer:",
        question["options"],
        index=None,
        key=f"answer_{current}"
    )


    # =====================================================
    # NAVIGATION
    # =====================================================

    st.divider()

    nav1, nav2, nav3 = st.columns(
        [1, 1, 1]
    )

    with nav1:

        if current > 0:

            if st.button(
                "⬅️ Previous",
                use_container_width=True
            ):

                st.session_state.current_question -= 1

                st.rerun()


    with nav2:

        st.write(
            f"**{current + 1} / {total_questions}**"
        )


    with nav3:

        if current < total_questions - 1:

            if st.button(
                "Next ➡️",
                use_container_width=True
            ):

                st.session_state.current_question += 1

                st.rerun()


    # =====================================================
    # SUBMIT BUTTON
    # =====================================================

    if current == total_questions - 1:

        st.markdown("")

        if st.button(
            "🏁 Submit Quiz",
            type="primary",
            use_container_width=True
        ):

            score = 0

            for i, q in enumerate(questions):

                selected_answer = (
                    st.session_state.get(
                        f"answer_{i}"
                    )
                )

                if (
                    selected_answer
                    == q["answer"]
                ):

                    score += 1

            st.session_state.score = score

            st.session_state.submitted = True

            st.rerun()


    # =====================================================
    # TIMER REFRESH
    # =====================================================

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


    # =====================================================
    # RESULTS HEADER
    # =====================================================

    st.divider()

    st.markdown("## 🏆 Quiz Results")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Score",
            f"{score}/{total}"
        )

    with col2:

        st.metric(
            "Percentage",
            f"{percentage:.0f}%"
        )

    with col3:

        if percentage >= 80:

            grade = "A"

        elif percentage >= 60:

            grade = "B"

        elif percentage >= 40:

            grade = "C"

        else:

            grade = "D"

        st.metric(
            "Grade",
            grade
        )


    # =====================================================
    # PERFORMANCE
    # =====================================================

    if percentage >= 90:

        st.success(
            "🌟 Outstanding! You're a quiz master!"
        )

        st.balloons()

    elif percentage >= 75:

        st.success(
            "🎉 Excellent work! Keep going!"
        )

    elif percentage >= 60:

        st.info(
            "👍 Good job! Keep practicing."
        )

    elif percentage >= 40:

        st.warning(
            "📚 Keep learning. You're improving!"
        )

    else:

        st.error(
            "💪 Don't give up. Review and try again!"
        )


    # =====================================================
    # PERFORMANCE BAR
    # =====================================================

    st.subheader("📊 Performance")

    st.progress(
        percentage / 100
    )


    # =====================================================
    # ANSWER REVIEW
    # =====================================================

    st.subheader("📖 Answer Review")

    for i, question in enumerate(questions):

        selected_answer = (
            st.session_state.get(
                f"answer_{i}"
            )
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
                "❌ Your answer: "
                + (
                    selected_answer
                    if selected_answer
                    else "Not answered"
                )
            )

            st.info(
                f"Correct answer: "
                f"{question['answer']}"
            )

        st.write(
            f"💡 {question['explanation']}"
        )

        st.divider()


    # =====================================================
    # NEW QUIZ
    # =====================================================

    if st.button(
        "🔄 Create New Quiz",
        type="primary",
        use_container_width=True
    ):

        st.session_state.questions = []

        st.session_state.submitted = False

        st.session_state.score = 0

        st.session_state.quiz_started = False

        st.session_state.start_time = None

        st.session_state.current_question = 0

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "🧠 AI Quiz Generator • "
    "Powered by Gemini AI • "
    "Built with Python & Streamlit"
)