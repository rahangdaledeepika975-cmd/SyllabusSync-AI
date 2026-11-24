import os
import json
import sqlite3
import uuid

from datetime import date, timedelta
from dotenv import load_dotenv
from openai import OpenAI

import fitz
import streamlit as st

load_dotenv()

DB_NAME = "syllabus_sync.db"

st.set_page_config(
    page_title="SyllabusSync AI",
    page_icon="📚",
    layout="wide"
)


def get_grok_client():
    api_key = os.getenv("XAI_API_KEY")

    if not api_key:
        raise ValueError(
            "XAI_API_KEY missing hai. Apni .env file check karo."
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
        timeout=120.0
    )


def ask_grok(prompt):
    client = get_grok_client()

    response = client.chat.completions.create(
        model="grok-4.7",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are SyllabusSync AI, an academic planning "
                    "assistant. Analyze syllabus carefully, prioritize "
                    "topics logically, and never invent syllabus topics."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                study_date TEXT,
                topic TEXT,
                status TEXT DEFAULT 'Pending'
            )
        """)


def load_tasks():
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute("""
            SELECT id, study_date, topic, status
            FROM tasks
            ORDER BY study_date
        """).fetchall()

    return [
        {
            "id": row[0],
            "date": row[1],
            "topic": row[2],
            "status": row[3]
        }
        for row in rows
    ]


def save_plan(topics, start_date, exam_date):
    total_days = (exam_date - start_date).days + 1

    if not topics or total_days < 1:
        raise ValueError("Topics aur dates check karo.")

    plan = []

    for day_number in range(total_days):
        current_date = start_date + timedelta(days=day_number)

        if day_number == total_days - 1:
            topic = "Final Revision"
        else:
            topic = topics[day_number % len(topics)]

        plan.append((
            str(uuid.uuid4()),
            current_date.isoformat(),
            topic,
            "Pending"
        ))

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM tasks")

        conn.executemany("""
            INSERT INTO tasks (id, study_date, topic, status)
            VALUES (?, ?, ?, ?)
        """, plan)


def update_status(task_id, completed):
    status = "Completed" if completed else "Pending"

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id)
        )


def reschedule_missed_tasks():
    today = date.today()

    tasks = load_tasks()

    missed = [
        task for task in tasks
        if task["date"] < today.isoformat()
        and task["status"] == "Pending"
    ]

    if not missed:
        return 0

    future_dates = sorted({
        task["date"] for task in tasks
        if task["date"] >= today.isoformat()
        and task["status"] == "Pending"
    })


    next_day = (
        date.fromisoformat(future_dates[-1]) + timedelta(days=1)
        if future_dates
        else today
    )

    with sqlite3.connect(DB_NAME) as conn:
        for task in missed:
            if future_dates:
                new_date = future_dates.pop(0)
            else:
                new_date = next_day.isoformat()
                next_day += timedelta(days=1)

            conn.execute(
                "UPDATE tasks SET study_date = ? WHERE id = ?",
                (new_date, task["id"])
            )

    return len(missed)


init_db()

st.title("📚 SyllabusSync AI")
st.subheader("From Syllabus to Success")

st.write(
    "An AI-powered academic planning agent that analyzes your "
    "syllabus, creates study plans and tracks learning progress."
)

st.success("SyllabusSync AI dashboard is running!")

st.header("📄 Upload Your Syllabus")

uploaded_pdf = st.file_uploader(
    "Choose your syllabus PDF",
    type=["pdf"]
)

pdf_text = ""

if uploaded_pdf:
    try:
        with fitz.open(
            stream=uploaded_pdf.getvalue(),
            filetype="pdf"
        ) as document:

            pdf_text = "\n".join(
                page.get_text()
                for page in document
            )

        st.success("PDF successfully extracted!")

        st.caption(
            f"Extracted {len(pdf_text):,} characters."
        )

        with st.expander("Preview PDF text"):
            st.text(pdf_text[:4000] or "No selectable text found.")

        if not pdf_text.strip():
            st.warning(
                "PDF mein selectable text nahi mila. "
                "Scanned PDF ke liye OCR ki zaroorat ho sakti hai."
            )

    except Exception as error:
        st.error(f"PDF read nahi ho payi: {error}")


st.header("🧠 AI Syllabus Analysis")

if st.button("Analyze Syllabus with Grok AI"):

    if not pdf_text.strip():
        st.warning("Pehle readable syllabus PDF upload karo.")

    else:
        # Limit text sent to the API to control request size.
        syllabus_excerpt = pdf_text[:20000]

        prompt = f"""
Analyze this academic syllabus.

Extract the subjects, units and specific study topics.
Prioritize topics in a sensible learning order.

Return ONLY a JSON object in this format:
{{
  "topics": [
    "Topic 1",
    "Topic 2",
    "Topic 3"
  ]
}}

Do not include Markdown fences.
Only include topics supported by the provided syllabus.
If the text is incomplete, extract only the topics you can identify.

SYLLABUS TEXT:
{syllabus_excerpt}
"""

        try:
            with st.spinner("Grok AI is analyzing your syllabus..."):
                answer = ask_grok(prompt)

            # Parse the AI response as JSON.
            cleaned = answer.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "", 1)
                cleaned = cleaned.replace("```", "").strip()

            result = json.loads(cleaned)
            topics = result.get("topics", [])

            topics = [
                topic.strip()
                for topic in topics
                if isinstance(topic, str) and topic.strip()
            ]

            if not topics:
                st.warning("AI se valid topics nahi mile.")
            else:
                st.session_state["ai_topics"] = topics

                st.success(
                    f"Grok AI identified {len(topics)} topics."
                )

                for topic in topics:
                    st.write(f"• {topic}")

        except Exception as error:
            st.error(f"AI analysis failed: {error}")


st.divider()
st.header("🗓️ Create Your Study Plan")

default_topics = st.session_state.get("ai_topics", [])

with st.form("study_planner"):

    topics_text = st.text_area(
        "Subjects or topics — one per line",
        value="\n".join(default_topics),
        placeholder="Operating System\nProcess Management\nCPU Scheduling"
    )

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Study start date",
            value=date.today()
        )

    with col2:
        exam_date = st.date_input(
            "Exam / target date",
            value=date.today() + timedelta(days=7)
        )

    daily_hours = st.slider(
        "Available study hours per day",
        min_value=1,
        max_value=12,
        value=3
    )

    generate = st.form_submit_button("Generate AI Study Plan")


if generate:
    topics = [
        line.strip()
        for line in topics_text.splitlines()
        if line.strip()
    ]

    if not topics:
        st.error("At least one topic enter karo.")

    elif exam_date < start_date:
        st.error("Exam date start date se pehle nahi ho sakti.")

    else:
        try:
    
            prompt = f"""
Arrange these syllabus topics in a sensible study order.

Return ONLY a JSON object:
{{"topics": ["Topic 1", "Topic 2"]}}

Do not invent new topics.

Topics:
{json.dumps(topics)}

Available hours per day: {daily_hours}
Start date: {start_date}
Exam date: {exam_date}
"""

            with st.spinner("Grok AI is planning your semester..."):
                answer = ask_grok(prompt)

            cleaned = answer.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "", 1)
                cleaned = cleaned.replace("```", "").strip()

            result = json.loads(cleaned)
            ordered_topics = result.get("topics", [])

            if not ordered_topics:
                raise ValueError("AI ne valid study order return nahi kiya.")

            save_plan(
                ordered_topics,
                start_date,
                exam_date
            )

            st.session_state["daily_hours"] = daily_hours

            st.success("AI study plan successfully generated!")

        except Exception as error:
            st.error(f"AI planning failed: {error}")


# ---------------- PROGRESS TRACKING ----------------

st.divider()
st.header("📈 Study Progress")

tasks = load_tasks()

if tasks:
    completed = sum(
        task["status"] == "Completed"
        for task in tasks
    )

    st.progress(completed / len(tasks))

    st.write(f"Completed: {completed} / {len(tasks)} sessions")

    for task in tasks:
        col1, col2 = st.columns([1, 3])

        with col1:
            st.caption(task["date"])

        with col2:
            checked = st.checkbox(
                task["topic"],
                value=(task["status"] == "Completed"),
                key=f"task_{task['id']}"
            )

            if checked != (task["status"] == "Completed"):
                update_status(task["id"], checked)
                st.rerun()

    if st.button("🔄 Reschedule Missed Tasks"):
        moved = reschedule_missed_tasks()

        if moved:
            st.success(
                f"{moved} missed task(s) rescheduled."
            )
        else:
            st.info("No missed tasks found.")

        st.rerun()

else:
    st.info("Generate a study plan to start tracking progress.")


st.divider()

st.caption(
    "SyllabusSync AI | Adaptive Academic Planning Assistant"
)