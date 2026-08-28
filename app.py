import streamlit as st
import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


# =========================================================
# PAGE CONFIGURATION
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
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .question-box {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
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
    '<div class="subtitle">Generate an intelligent quiz on any topic using Gemini AI</div>',
    unsafe_allow_html=True
)


# =========================================================
# CHECK API KEY
# =========================================================

if not API_KEY:

    st.error(
        "❌ Gemini API key not found."
    )

    st.info(
        "Make sure your .env file contains: GEMINI_API_KEY=your_key"
    )

    st.stop()


# =========================================================
# CREATE GEMINI CLIENT
# =========================================================

try:

    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(
            timeout=30000
        )
    )

except Exception as e:

    st.error(
        f"❌ Could not connect to Gemini: {e}"
    )

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


# =========================================================
# QUIZ SETTINGS
# =========================================================

st.subheader("⚙️ Quiz Settings")

topic = st.text_input(
    "📚 Enter Topic",
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
3. The answer must exactly match one of the four options.
4. Questions must be related to {topic}.
5. Follow the {difficulty} difficulty level.
6. Give a short explanation for every answer.
7. Do not use Markdown.
8. Do not add any text before or after the JSON.
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

        # Remove Markdown code fences if Gemini adds them
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

        # Validate questions
        if not isinstance(questions, list):

            raise ValueError(
                "Invalid quiz format."
            )

        if len(questions) != number_of_questions:

            raise ValueError(
                f"Expected {number_of_questions} questions "
                f"but received {len(questions)}."
            )

        for question in questions:

            if "question" not in question:
                raise ValueError("Question text is missing.")

            if "options" not in question:
                raise ValueError("Options are missing.")

            if "answer" not in question:
                raise ValueError("Answer is missing.")

            if "explanation" not in question:
                question["explanation"] = (
                    "This is the correct answer."
                )

            if len(question["options"]) != 4:

                raise ValueError(
                    "Each question must have exactly 4 options."
                )

            if question["answer"] not in question["options"]:

                raise ValueError(
                    "Correct answer does not match an option."
                )

        return questions, None

    except Exception as e:

        return None, str(e)


# =========================================================
# GENERATE QUIZ BUTTON
# =========================================================

if st.button(
    "🚀 Generate Quiz",
    type="primary"
):

    if not topic.strip():

        st.warning(
            "⚠️ Please enter a topic first."
        )

    else:

        # Reset previous quiz
        st.session_state.questions = []
        st.session_state.submitted = False
        st.session_state.score = 0

        with st.spinner(
            "🧠 Gemini is creating your quiz..."
        ):

            questions, error = generate_quiz(
                topic,
                difficulty,
                number_of_questions
            )

        if questions:

            st.session_state.questions = questions

            st.success(
                "🎉 Quiz generated successfully!"
            )

        else:

            st.error(
                "❌ Could not generate the quiz."
            )

            st.code(
                error
                if error
                else "Unknown error."
            )


# =========================================================
# DISPLAY QUIZ
# =========================================================

if st.session_state.questions:

    st.divider()

    st.subheader("📝 Your Quiz")

    for i, question in enumerate(
        st.session_state.questions
    ):

        st.markdown(
            f"### Question {i + 1}"
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


    # =====================================================
    # CHECK ANSWERS
    # =====================================================

    st.divider()

    if st.button(
        "✅ Submit Quiz",
        type="primary"
    ):

        score = 0

        for i, question in enumerate(
            st.session_state.questions
        ):

            selected_answer = st.session_state.get(
                f"answer_{i}"
            )

            if selected_answer is None:

                continue

            if selected_answer == question["answer"]:

                score += 1

        st.session_state.score = score
        st.session_state.submitted = True


# =========================================================
# SHOW RESULTS
# =========================================================

if st.session_state.submitted:

    total = len(
        st.session_state.questions
    )

    score = st.session_state.score

    percentage = (
        score / total
    ) * 100

    st.divider()

    st.subheader("🏆 Quiz Results")

    st.metric(
        "Your Score",
        f"{score} / {total}"
    )

    st.metric(
        "Percentage",
        f"{percentage:.0f}%"
    )

    if percentage >= 80:

        st.success(
            "🌟 Excellent! You really know this topic!"
        )

        st.balloons()

    elif percentage >= 60:

        st.info(
            "👏 Good job! Keep practicing."
        )

    else:

        st.warning(
            "💪 Keep learning and try again!"
        )


    # =====================================================
    # ANSWER REVIEW
    # =====================================================

    st.subheader("📖 Answer Review")

    for i, question in enumerate(
        st.session_state.questions
    ):

        selected_answer = st.session_state.get(
            f"answer_{i}"
        )

        st.markdown(
            f"**Question {i + 1}:** "
            f"{question['question']}"
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


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "Built with Python 🐍 • Streamlit • Gemini AI"
)