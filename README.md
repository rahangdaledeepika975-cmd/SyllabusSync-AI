 SyllabusSync AI

### From Syllabus to Success — Your AI-Powered Academic Planner

SyllabusSync AI is an AI-powered academic planning agent that analyzes a student's syllabus, identifies meaningful topics, creates personalized study plans, tracks progress, and helps adjust missed study tasks.

 Features

 **Syllabus PDF Analysis**  
  Upload a syllabus PDF and extract its content automatically.

 **AI Syllabus Analysis**  
  Uses AI to identify and organize meaningful syllabus topics.

 **Personalized Study Planning**  
  Creates a study plan based on:
  - Study start date
  - Study end date
  - Study hours per day

   **Missed Task Adjustment**  
  Helps reorganize study tasks when planned sessions are missed.

 **Study Progress Tracking**  
  Tracks total sessions, completed sessions, and overall progress.

 **Academic Planning Agent**  
  Designed to support students in managing their semester preparation efficiently.

 Technologies Used

- Python
- Streamlit
- AI / LLM
- PDF Text Extraction
- SQLite
- Python Virtual Environment

 Project Structure

```text
SyllabusSync-AI/
│
├── app.py
├── agent.py
├── memory.py
├── planner.py
├── app_backup_2.py
├── .gitignore
└── README.md
```

## ▶️ How to Run

### 1. Clone the repository

```bash
git clone https://github.com/rahangdaledeepika975-cmd/SyllabusSync-AI.git
```

### 2. Open the project

```bash
cd SyllabusSync-AI
```

### 3. Create and activate virtual environment

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install streamlit
```

Install any additional dependencies required by the project.

### 5. Configure environment variables

Create a `.env` file in the project root and add your API key.

```text
GROQ_API_KEY=your_api_key_here
```

⚠️ Never upload your `.env` file or API keys to GitHub.

### 6. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

## 🎯 Project Goal

The goal of SyllabusSync AI is to make academic preparation more organized by converting a syllabus into an actionable study plan.

Instead of manually deciding what to study each day, students can upload their syllabus and let the system help organize their preparation.

## 🔮 Future Improvements

- 🤖 Improved autonomous AI agent
- 🧠 Long-term student memory
- 📝 Task completion through the dashboard
- 📊 Advanced progress analytics
- ⏰ Exam deadline prioritization
- 🔁 Automatic schedule regeneration
- 📱 Improved responsive UI

