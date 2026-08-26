import streamlit as st

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠"
)

st.title("🧠 AI Quiz Generator")
st.write("Create a quiz on any topic using AI.")

topic = st.text_input("Enter a topic")

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

if st.button("Generate Quiz"):
    st.write("Your quiz will appear here!")