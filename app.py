import streamlit as st
import random

# Page configuration
st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠"
)

# Title
st.title("🧠 AI Quiz Generator")
st.write("Create a quiz on any topic.")

# Topic
topic = st.text_input("Enter a topic")

# Difficulty
difficulty = st.selectbox(
    "Select difficulty",
    ["Easy", "Medium", "Hard"]
)

# Number of questions
num_questions = st.slider(
    "Number of questions",
    min_value=1,
    max_value=10,
    value=5
)

# Sample questions
quiz_data = {
    "python": [
        {
            "question": "Which keyword is used to define a function in Python?",
            "options": ["func", "def", "function", "define"],
            "answer": "def"
        },
        {
            "question": "Which data type is used to store True or False?",
            "options": ["int", "str", "bool", "float"],
            "answer": "bool"
        },
        {
            "question": "Which symbol is used for comments in Python?",
            "options": ["//", "#", "/*", "--"],
            "answer": "#"
        },
        {
            "question": "Which function is used to display output in Python?",
            "options": ["display()", "show()", "print()", "output()"],
            "answer": "print()"
        },
        {
            "question": "Which collection is ordered and changeable?",
            "options": ["Set", "Tuple", "List", "Dictionary"],
            "answer": "List"
        }
    ]
}

# Generate quiz
if st.button("Generate Quiz"):

    if not topic:
        st.warning("Please enter a topic first.")

    elif topic.lower().strip() == "python":

        questions = quiz_data["python"]

        # Randomize questions
        random.shuffle(questions)

        questions = questions[:min(num_questions, len(questions))]

        st.session_state.questions = questions
        st.session_state.quiz_started = True
        st.session_state.score = 0

    else:
        st.info(
            "Currently, sample questions are available for Python. "
            "More topics will be added soon!"
        )

# Display quiz
if st.session_state.get("quiz_started", False):

    st.subheader(f"📝 {topic.title()} Quiz")

    score = 0

    for i, question in enumerate(st.session_state.questions):

        st.write(f"### Question {i + 1}")
        st.write(question["question"])

        selected = st.radio(
            "Choose your answer:",
            question["options"],
            key=f"question_{i}"
        )

        if selected == question["answer"]:
            score += 1

    if st.button("Check Score"):
        st.success(
            f"🎉 Your Score: {score}/{len(st.session_state.questions)}"
        )