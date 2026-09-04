# 🧠 AI Quiz Generator

An AI-powered quiz generation platform that creates personalized multiple-choice quizzes using Google's Gemini AI.

Users can choose a category, difficulty level, number of questions, and time limit, then test their knowledge through an interactive quiz experience.

---

## ✨ Features

- 🤖 AI-powered quiz generation
- 📚 Multiple quiz categories
- ✏️ Custom topic support
- 🎯 Easy, Medium, and Hard difficulty levels
- 📝 3, 5, 7, or 10 questions
- ⏱️ Configurable quiz timer
- 📊 Real-time progress tracking
- ⬅️ Previous / Next question navigation
- 🏆 Automatic score calculation
- 📈 Performance dashboard
- 🔍 Detailed answer review
- 📚 Quiz history
- 🗑️ Clear quiz history
- ⚠️ Error handling and input validation
- 📱 Responsive Streamlit interface

---

## 🎥 Project Demo

> Add a screenshot or demo GIF here after deployment.

<!-- ![AI Quiz Generator](screenshots/app.png) -->

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application framework |
| Google Gemini | AI quiz generation |
| Google GenAI SDK | Gemini API integration |
| Pandas | Quiz history data handling |
| python-dotenv | Environment variable management |
| Git | Version control |
| GitHub | Source code hosting |

---

## 🏗️ How It Works

```text
User
  │
  ▼
Choose Topic
  │
  ▼
Choose Difficulty
  │
  ▼
Choose Number of Questions
  │
  ▼
Choose Time Limit
  │
  ▼
Gemini AI
  │
  ▼
Generate Quiz
  │
  ▼
Take Quiz
  │
  ▼
Calculate Results
  │
  ▼
Performance Dashboard
  │
  ▼
Quiz History
```

---

## 📂 Project Structure

```text
ai-quiz-generator/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
└── venv/
```

> `.env` and `venv/` are excluded from GitHub for security and environment management.

---

## ⚙️ Installation

**1. Clone the repository**
```bash
git clone https://github.com/annapoorna147/ai-quiz-generator.git
```

**2. Open the project**
```bash
cd ai-quiz-generator
```

**3. Create a virtual environment**
```bash
python3 -m venv venv
```

**4. Activate the virtual environment**

macOS / Linux:
```bash
source venv/bin/activate
```

Windows:
```bash
venv\Scripts\activate
```

**5. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## 🔑 Gemini API Setup

This project uses Google's Gemini API to generate quizzes.

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

> ⚠️ Do not commit your API key to GitHub. The `.gitignore` file already excludes `.env`.

---

## ▶️ Run the Application

Activate the virtual environment, then run:

```bash
streamlit run app.py
```

The application will open locally in your browser.

---

## 🧪 Testing

The application has been tested for:

- Quiz generation
- Multiple categories
- Custom topics
- Difficulty selection
- Question count selection
- Timer functionality
- Question navigation
- Answer selection
- Unanswered questions
- Automatic scoring
- Performance calculations
- Detailed answer review
- Quiz history
- Clearing quiz history
- Starting a new quiz
- Invalid custom topic handling
- Gemini response validation

---

## 📊 Current Quiz Flow

**1. Configure**
Choose category, difficulty, number of questions, and time per question.

**2. Generate**
Gemini AI creates a personalized multiple-choice quiz.

**3. Learn & Test**
Answer questions one at a time while tracking your progress and remaining time.

**4. Review**
After submission, the application calculates:
- Score
- Percentage
- Grade
- Correct answers
- Wrong answers
- Unanswered questions

**5. Track**
Completed quizzes appear in the Quiz History section.

---

## 🚀 Future Improvements

The current version is the foundation for a larger AI-powered learning platform.

Planned improvements include:

- 🌐 Public web version
- 👤 User accounts
- 💾 Permanent quiz history
- 📊 Advanced learning analytics
- 🔥 Learning streaks
- 🏆 Achievements and badges
- 📚 AI-generated explanations
- 🧠 Personalized learning recommendations
- 📈 Topic-based progress tracking
- 🌙 Advanced theme customization
- 📱 Improved mobile experience
- 🔐 Secure production backend
- ☁️ Cloud deployment

---

## 🎯 Vision

The long-term goal is to transform the AI Quiz Generator from a personal project into a public learning platform where anyone can:

- Learn anything.
- Practice intelligently.
- Test their knowledge.
- Track their progress.

---

## 👩‍💻 Author

**Annapoorna**

Built as an AI-powered learning project using Python, Streamlit, and Google Gemini.

- GitHub: [@annapoorna147](https://github.com/annapoorna147)
- LinkedIn: [Annapoorna S U](https://www.linkedin.com/in/annapoorna-s-u-789035341/)

---

## 📄 License

This project is intended for educational and portfolio purposes.

---

## ⭐ If You Find This Project Useful

Give the repository a ⭐ on GitHub and follow the project as it evolves into a complete AI learning platform.
