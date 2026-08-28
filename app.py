import streamlit as st
import random

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="centered"
)

# -----------------------------
# Title
# -----------------------------
st.title("🧠 AI Quiz Generator")
st.write("Create a quiz on any topic.")

# -----------------------------
# Sample Question Database
# -----------------------------
quiz_database = {
    "python": [
        {
            "question": "Which keyword is used to define a function in Python?",
            "options": ["function", "def", "fun", "define"],
            "answer": "def"
        },
        {
            "question": "Which data type is used to store True or False?",
            "options": ["String", "Integer", "Boolean", "Float"],
            "answer": "Boolean"
        },
        {
            "question": "Which symbol is used for comments in Python?",
            "options": ["//", "#", "/*", "--"],
            "answer": "#"
        },
        {
            "question": "Which collection is ordered and changeable?",
            "options": ["Set", "Tuple", "List", "Dictionary"],
            "answer": "List"
        },
        {
            "question": "Which function is used to display output in Python?",
            "options": ["display()", "show()", "print()", "output()"],
            "answer": "print()"
        },
        {
            "question": "What is the extension of a Python file?",
            "options": [".java", ".py", ".python", ".pt"],
            "answer": ".py"
        },
        {
            "question": "Which operator is used for exponentiation in Python?",
            "options": ["^", "**", "//", "%%"],
            "answer": "**"
        },
        {
            "question": "Which keyword is used to create a loop over a sequence?",
            "options": ["loop", "repeat", "for", "while"],
            "answer": "for"
        },
        {
            "question": "Which function returns the length of a list?",
            "options": ["size()", "length()", "count()", "len()"],
            "answer": "len()"
        },
        {
            "question": "Which keyword is used to import a module?",
            "options": ["include", "import", "using", "module"],
            "answer": "import"
        }
    ]
}

# -----------------------------
# User Inputs
# -----------------------------
topic = st.text_input(
    "Enter a topic",
    placeholder="Example: Python"
)

difficulty = st.selectbox(
    "Select difficulty",
    ["Easy", "Medium", "Hard"]
)

num_questions = st.slider(
    "Number of questions",
    min_value=1,
    max_value=10,
    value=5
)

# -----------------------------
# Generate Quiz
# -----------------------------
if st.button("Generate Quiz"):

    topic_key = topic.strip().lower()

    if not topic_key:
        st.warning("⚠️ Please enter a topic.")
    
    elif topic_key not in quiz_database:
        st.info(
            "Currently, sample questions are available for Python. "
            "More topics will be added soon! 😊"
        )

    else:
        questions = quiz_database[topic_key].copy()

        # Randomize questions
        random.shuffle(questions)

        # Select requested number
        questions = questions[:num_questions]

        # Store quiz in session
        st.session_state.questions = questions
        st.session_state.quiz_started = True
        st.session_state.submitted = False

# -----------------------------
# Display Quiz
# -----------------------------
if st.session_state.get("quiz_started", False):

    st.divider()

    st.subheader("📝 Your Quiz")

    # Display questions
    for i, question in enumerate(st.session_state.questions):

        st.markdown(
            f"### Question {i + 1}: {question['question']}"
        )

        st.radio(
            "Select your answer:",
            question["options"],
            key=f"question_{i}"
        )

        st.write("")

    # -------------------------
    # Submit Quiz
    # -------------------------
    if st.button("Check Score"):

        score = 0

        for i, question in enumerate(st.session_state.questions):

            selected_answer = st.session_state.get(
                f"question_{i}"
            )

            if selected_answer == question["answer"]:
                score += 1

        total = len(st.session_state.questions)

        st.session_state.score = score
        st.session_state.submitted = True

    # -------------------------
    # Show Result
    # -------------------------
    if st.session_state.get("submitted", False):

        score = st.session_state.score
        total = len(st.session_state.questions)

        percentage = (score / total) * 100

        st.divider()

        st.subheader("🎉 Quiz Result")

        st.success(
            f"Your Score: {score}/{total}"
        )

        st.write(
            f"Percentage: **{percentage:.0f}%**"
        )

        if percentage == 100:
            st.balloons()
            st.success("🏆 Perfect score! Excellent work!")

        elif percentage >= 70:
            st.success("👏 Great job! Keep learning!")

        elif percentage >= 40:
            st.warning("👍 Good attempt! You can improve!")

        else:
            st.error("💪 Keep practicing. You will get better!")

        # -------------------------
        # Show Correct Answers
        # -------------------------
        st.subheader("📚 Correct Answers")

        for i, question in enumerate(st.session_state.questions):

            selected_answer = st.session_state.get(
                f"question_{i}"
            )

            if selected_answer == question["answer"]:
                st.write(
                    f"✅ **Q{i + 1}:** {question['answer']}"
                )
            else:
                st.write(
                    f"❌ **Q{i + 1}:** Correct answer → "
                    f"**{question['answer']}**"
                )

# -----------------------------
# Footer
# -----------------------------
st.divider()

st.caption(
    "🧠 AI Quiz Generator | Built with Python & Streamlit"
)