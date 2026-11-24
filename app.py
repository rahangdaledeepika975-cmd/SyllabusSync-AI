
import os
import re
import sqlite3
import uuid
from datetime import date, timedelta

import fitz
import pytesseract
from PIL import Image
import streamlit as st
from dotenv import load_dotenv
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

DB_NAME = "syllabus_sync.db"

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SyllabusSync AI",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 20px;
        color: #666;
        margin-top: 0px;
    }

    .section-title {
        font-size: 28px;
        font-weight: 650;
        margin-top: 25px;
    }

    .success-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #e8f5e9;
        border: 1px solid #81c784;
        margin-bottom: 20px;
    }

    .topic-card {
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-bottom: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# GROQ CLIENT
# ============================================================

@st.cache_resource
def get_groq_client():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to the .env file."
        )

    return Groq(api_key=api_key)


# ============================================================
# AI CALL
# ============================================================

def ask_ai(prompt):

    client = get_groq_client()

    models = [
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant"
    ]

    last_error = None

    for model in models:

        try:

            if model == "openai/gpt-oss-20b":

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are SyllabusSync AI, an academic "
                                "planning assistant. "
                                "Understand OCR errors and formatting noise. "
                                "Do not invent information. "
                                "Follow the requested output format exactly."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    reasoning_effort="low",
                    max_completion_tokens=4096
                )

            else:

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are SyllabusSync AI. "
                                "Analyze academic syllabus information. "
                                "Understand OCR errors. "
                                "Do not invent unsupported topics. "
                                "Follow the requested output format."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=2048
                )

            if not response.choices:
                continue

            content = response.choices[0].message.content

            if content:

                content = str(content).strip()

                if content:
                    return content

        except Exception as error:

            last_error = error

            continue

    if last_error:
        raise RuntimeError(
            f"All AI models failed. Last error: {last_error}"
        )

    raise RuntimeError(
        "AI returned an empty response."
    )


# ============================================================
# DATABASE
# ============================================================

def get_db():

    return sqlite3.connect(DB_NAME)


def init_db():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            study_date TEXT,
            topic TEXT,
            status TEXT DEFAULT 'Pending'
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_tasks():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, study_date, topic, status
        FROM tasks
        ORDER BY study_date
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


def save_plan(plan):

    conn = get_db()

    cursor = conn.cursor()

    # Remove old generated schedule.
    # The syllabus and database are not deleted.
    cursor.execute("DELETE FROM tasks")

    for item in plan:

        cursor.execute(
            """
            INSERT INTO tasks
            (id, study_date, topic, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                item["date"],
                item["topic"],
                "Pending"
            )
        )

    conn.commit()
    conn.close()


def update_task_status(task_id, status):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?
        WHERE id = ?
        """,
        (status, task_id)
    )

    conn.commit()
    conn.close()


def get_progress():

    tasks = get_tasks()

    if not tasks:
        return 0, 0, 0

    total = len(tasks)

    completed = sum(
        1
        for task in tasks
        if task[3] == "Completed"
    )

    percentage = (
        completed / total * 100
        if total
        else 0
    )

    return total, completed, percentage


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    pdf_bytes = uploaded_file.read()

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    normal_text = ""

    for page in document:

        text = page.get_text()

        if text:
            normal_text += text + "\n"

    # Normal PDF
    if len(normal_text.strip()) >= 500:

        document.close()

        return normal_text.strip(), False

    # OCR PDF
    ocr_text = ""

    for page_number, page in enumerate(document):

        try:

            pix = page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5),
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            text = pytesseract.image_to_string(
                image,
                config="--psm 6"
            )

            ocr_text += (
                f"\n--- Page {page_number + 1} ---\n"
            )

            ocr_text += text

        except Exception as error:

            ocr_text += (
                f"\n[OCR failed on page "
                f"{page_number + 1}: {error}]\n"
            )

    document.close()

    return ocr_text.strip(), True


# ============================================================
# CLEAN OCR
# ============================================================

def clean_ocr_text(text):

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# CHUNK TEXT
# ============================================================

def chunk_text(text, max_chars=7000):

    paragraphs = text.split("\n")

    chunks = []

    current = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(current) + len(paragraph) + 1 <= max_chars:

            current += paragraph + "\n"

        else:

            if current.strip():
                chunks.append(
                    current.strip()
                )

            current = paragraph + "\n"

    if current.strip():
        chunks.append(
            current.strip()
        )

    return chunks


# ============================================================
# PARSE NUMBERED LIST
# ============================================================

def parse_numbered_list(response):

    if not response:
        return []

    lines = response.splitlines()

    results = []

    for line in lines:

        line = line.strip()

        line = re.sub(
            r"^\s*\d+\s*[\.\)\-:]\s*",
            "",
            line
        )

        line = re.sub(
            r"^\s*[-*•]\s*",
            "",
            line
        )

        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        if lower.startswith(
            (
                "here are",
                "topics:",
                "the topics are",
                "analysis:",
                "based on",
                "the syllabus contains",
                "according to"
            )
        ):
            continue

        if len(line) > 140:
            continue

        results.append(line)

    final = []

    seen = set()

    for item in results:

        key = item.lower()

        if key not in seen:

            seen.add(key)
            final.append(item)

    return final


# ============================================================
# INITIAL TOPIC EXTRACTION
# ============================================================

def analyze_syllabus_with_ai(text):

    chunks = chunk_text(
        text,
        max_chars=7000
    )

    if not chunks:
        return []

    all_topics = []

    progress = st.progress(0)

    status = st.empty()

    total = len(chunks)

    for index, chunk in enumerate(chunks):

        status.write(
            f"Analyzing syllabus section "
            f"{index + 1} of {total}..."
        )

        prompt = f"""
Analyze the following OCR-extracted academic syllabus.

The text may contain OCR errors, spelling mistakes,
broken words, page numbers and formatting noise.

Identify only academic topics that are explicitly
supported by the supplied text.

Do not invent topics.

Return only a numbered list of short topic names.

Do not provide explanations.

Example:

1. Operating System Concepts
2. Operating System Services
3. System Calls
4. Process Management
5. CPU Scheduling

OCR TEXT:

{chunk}
"""

        try:

            answer = ask_ai(prompt)

            topics = parse_numbered_list(answer)

            all_topics.extend(topics)

        except Exception as error:

            st.warning(
                f"Section {index + 1} failed: {error}"
            )

        progress.progress(
            (index + 1) / total
        )

    progress.empty()
    status.empty()

    # Deduplicate
    final_topics = []

    seen = set()

    for topic in all_topics:

        key = topic.lower()

        if key not in seen:

            seen.add(key)
            final_topics.append(topic)

    return final_topics


# ============================================================
# AI TOPIC CLEANER
# ============================================================

def clean_topics_with_ai(topics):

    if not topics:
        return []

    topic_text = "\n".join(
        f"{index + 1}. {topic}"
        for index, topic in enumerate(topics)
    )

    prompt = f"""
You are cleaning an OCR-generated academic syllabus topic list.

The list may contain:

- duplicate topics
- repeated topics
- overly broad topics
- closely related topics
- OCR-generated variations
- the same concept written in different ways

Your task is to create a clean, compact syllabus topic list.

Rules:

1. Merge obvious duplicates.
2. Merge nearly identical topics.
3. Keep meaningful academic topics.
4. Do not invent topics.
5. Do not add topics that are not supported by the input.
6. Keep important subtopics when they are clearly present.
7. Prefer concise names.
8. Return at most 30 topics.
9. Return ONLY a numbered list.
10. Do not provide explanations.

INPUT TOPICS:

{topic_text}
"""

    answer = ask_ai(prompt)

    cleaned = parse_numbered_list(answer)

    return cleaned[:30]


# ============================================================
# AI STUDY PLAN
# ============================================================

def generate_ai_study_plan(
    topics,
    start_date,
    end_date,
    hours_per_day
):

    if not topics:
        return []

    total_days = (
        end_date - start_date
    ).days + 1

    if total_days <= 0:
        return []

    dates = []

    for i in range(total_days):

        current_date = (
            start_date +
            timedelta(days=i)
        )

        dates.append(
            current_date.isoformat()
        )

    date_text = "\n".join(
        f"{i + 1}. {d}"
        for i, d in enumerate(dates)
    )

    topic_text = "\n".join(
        f"{i + 1}. {topic}"
        for i, topic in enumerate(topics)
    )

    prompt = f"""
Create a realistic academic study plan.

Student study time:
{hours_per_day} hours per day.

Available dates:

{date_text}

Syllabus topics:

{topic_text}

Planning rules:

1. Cover the important syllabus topics.
2. Do not invent topics.
3. Put difficult or foundational topics earlier.
4. Related topics may be grouped.
5. Keep the daily workload realistic.
6. Use revision near the end if enough days are available.
7. Do not put multiple unrelated major topics into one day.
8. Every available date should have one study session.
9. Use the exact dates provided.
10. Return ONLY a numbered list.
11. Each line must follow this exact format:

DATE | TOPIC

Example:

2026-11-11 | Operating System Concepts
2026-11-12 | Process Management
2026-11-13 | CPU Scheduling

Do not add explanations.
Do not add headings.
"""

    answer = ask_ai(prompt)

    lines = answer.splitlines()

    plan = []

    for line in lines:

        line = line.strip()

        line = re.sub(
            r"^\s*\d+\s*[\.\)\-:]\s*",
            "",
            line
        )

        if "|" not in line:
            continue

        parts = line.split("|", 1)

        plan_date = parts[0].strip()
        topic = parts[1].strip()

        # Validate date
        try:

            date.fromisoformat(
                plan_date
            )

        except ValueError:

            continue

        if not topic:
            continue

        plan.append(
            {
                "date": plan_date,
                "topic": topic
            }
        )

    # Keep only requested dates
    valid_dates = set(dates)

    filtered = [
        item
        for item in plan
        if item["date"] in valid_dates
    ]

    # Remove duplicate dates
    final = []

    seen_dates = set()

    for item in filtered:

        if item["date"] not in seen_dates:

            seen_dates.add(
                item["date"]
            )

            final.append(item)

    return final


# ============================================================
# FALLBACK STUDY PLAN
# ============================================================

def fallback_study_plan(
    topics,
    start_date,
    end_date
):

    total_days = (
        end_date - start_date
    ).days + 1

    if total_days <= 0:
        return []

    plan = []

    for index in range(total_days):

        study_date = (
            start_date +
            timedelta(days=index)
        )

        if index < len(topics):

            topic = topics[index]

        else:

            topic = "Revision"

        plan.append(
            {
                "date": study_date.isoformat(),
                "topic": topic
            }
        )

    return plan


# ============================================================
# MISSED TASK RESCHEDULING
# ============================================================

def reschedule_missed_tasks():

    tasks = get_tasks()

    today = date.today()

    missed = []

    for task in tasks:

        task_id = task[0]
        task_date = task[1]
        topic = task[2]
        status = task[3]

        try:

            task_day = date.fromisoformat(
                task_date
            )

        except ValueError:

            continue

        if (
            task_day < today
            and status != "Completed"
        ):

            missed.append(
                (
                    task_id,
                    topic
                )
            )

    if not missed:
        return 0

    conn = get_db()

    cursor = conn.cursor()

    for index, item in enumerate(missed):

        task_id = item[0]

        new_date = (
            today +
            timedelta(days=index)
        )

        cursor.execute(
            """
            UPDATE tasks
            SET study_date = ?
            WHERE id = ?
            """,
            (
                new_date.isoformat(),
                task_id
            )
        )

    conn.commit()
    conn.close()

    return len(missed)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📚 SyllabusSync AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'From Syllabus to Success'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "An AI-powered academic planning agent that analyzes "
    "your syllabus, creates study plans, and tracks "
    "your learning progress."
)

st.markdown(
    """
    <div class="success-box">
    <b>🚀 SyllabusSync AI dashboard is running!</b>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "syllabus_text" not in st.session_state:
    st.session_state.syllabus_text = ""

if "raw_topics" not in st.session_state:
    st.session_state.raw_topics = []

if "clean_topics" not in st.session_state:
    st.session_state.clean_topics = []

if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""

if "ocr_used" not in st.session_state:
    st.session_state.ocr_used = False


# ============================================================
# UPLOAD
# ============================================================

st.markdown(
    '<div class="section-title">📄 Upload Your Syllabus</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Choose your syllabus PDF",
    type=["pdf"]
)


if uploaded_file:

    if st.button(
        "📖 Extract Syllabus",
        use_container_width=True
    ):

        with st.spinner(
            "Extracting syllabus..."
        ):

            try:

                text, used_ocr = extract_pdf_text(
                    uploaded_file
                )

                text = clean_ocr_text(text)

                st.session_state.syllabus_text = text
                st.session_state.ocr_used = used_ocr

                # Reset old AI analysis
                st.session_state.raw_topics = []
                st.session_state.clean_topics = []

                if used_ocr:

                    st.info(
                        "📷 Scanned PDF detected. "
                        "Tesseract OCR is being used..."
                    )

                    st.success(
                        "✅ PDF successfully extracted!"
                    )

                else:

                    st.success(
                        "✅ PDF text extracted successfully!"
                    )

            except Exception as error:

                st.error(
                    f"PDF extraction failed: {error}"
                )


# ============================================================
# PREVIEW
# ============================================================

if st.session_state.syllabus_text:

    st.markdown(
        '<div class="section-title">📄 Preview PDF Text</div>',
        unsafe_allow_html=True
    )

    text = st.session_state.syllabus_text

    st.write(
        f"Extracted characters: **{len(text):,}**"
    )

    with st.expander(
        "View extracted syllabus text"
    ):

        st.text(
            text[:5000]
        )

        if len(text) > 5000:

            st.caption(
                "Showing first 5,000 characters."
            )


# ============================================================
# AI ANALYSIS
# ============================================================

if st.session_state.syllabus_text:

    st.markdown(
        '<div class="section-title">🧠 AI Syllabus Analysis</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🤖 Analyze Syllabus with AI",
        use_container_width=True
    ):

        with st.spinner(
            "AI is analyzing the syllabus..."
        ):

            try:

                raw_topics = analyze_syllabus_with_ai(
                    st.session_state.syllabus_text
                )

                st.session_state.raw_topics = raw_topics

                if raw_topics:

                    st.success(
                        f"AI initially identified "
                        f"{len(raw_topics)} topics."
                    )

                    with st.spinner(
                        "AI is cleaning and merging duplicate topics..."
                    ):

                        cleaned_topics = clean_topics_with_ai(
                            raw_topics
                        )

                    st.session_state.clean_topics = (
                        cleaned_topics
                    )

                    st.success(
                        f"✅ Final syllabus contains "
                        f"{len(cleaned_topics)} meaningful topics."
                    )

                else:

                    st.warning(
                        "No topics were identified."
                    )

            except Exception as error:

                st.error(
                    f"AI syllabus analysis failed: {error}"
                )


# ============================================================
# DISPLAY CLEAN TOPICS
# ============================================================

if st.session_state.clean_topics:

    st.subheader(
        "📚 Cleaned Syllabus Topics"
    )

    for index, topic in enumerate(
        st.session_state.clean_topics,
        start=1
    ):

        st.markdown(
            f"""
            <div class="topic-card">
            <b>{index}.</b> {topic}
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# STUDY PLAN
# ============================================================

st.markdown(
    '<div class="section-title">🗓️ Create Your Study Plan</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    start_date = st.date_input(
        "Study Start Date",
        value=date.today()
    )

with col2:

    end_date = st.date_input(
        "Study End Date",
        value=date.today() + timedelta(days=7)
    )

hours_per_day = st.number_input(
    "Study Hours Per Day",
    min_value=1,
    max_value=12,
    value=3
)


if st.session_state.clean_topics:

    if st.button(
        "📅 Generate AI Study Plan",
        use_container_width=True
    ):

        if end_date < start_date:

            st.error(
                "End date cannot be before start date."
            )

        else:

            with st.spinner(
                "AI is creating your personalized study plan..."
            ):

                try:

                    plan = generate_ai_study_plan(
                        st.session_state.clean_topics,
                        start_date,
                        end_date,
                        hours_per_day
                    )

                except Exception as error:

                    st.warning(
                        f"AI planning failed: {error}"
                    )

                    plan = []

            # Fallback
            if not plan:

                st.info(
                    "Using automatic fallback study planning."
                )

                plan = fallback_study_plan(
                    st.session_state.clean_topics,
                    start_date,
                    end_date
                )

            if plan:

                save_plan(plan)

                st.success(
                    f"✅ AI study plan created with "
                    f"{len(plan)} sessions."
                )

                st.rerun()

else:

    st.info(
        "Analyze your syllabus first to create "
        "an AI-powered study plan."
    )


# ============================================================
# CURRENT STUDY PLAN
# ============================================================

tasks = get_tasks()

if tasks:

    st.subheader(
        "📅 Current Study Plan"
    )

    for task in tasks:

        task_id = task[0]
        task_date = task[1]
        topic = task[2]
        status = task[3]

        col1, col2, col3 = st.columns(
            [1.5, 5, 2]
        )

        with col1:

            st.write(
                f"**{task_date}**"
            )

        with col2:

            st.write(topic)

        with col3:

            if status == "Completed":

                st.success(
                    "Completed"
                )

            else:

                if st.button(
                    "Mark Complete",
                    key=f"complete_{task_id}"
                ):

                    update_task_status(
                        task_id,
                        "Completed"
                    )

                    st.rerun()


# ============================================================
# MISSED TASKS
# ============================================================

st.subheader(
    "🔄 Missed Task Adjustment"
)

if st.button(
    "🔄 Reschedule Missed Tasks",
    use_container_width=True
):

    moved = reschedule_missed_tasks()

    if moved:

        st.success(
            f"✅ {moved} missed task(s) "
            f"were rescheduled."
        )

        st.rerun()

    else:

        st.info(
            "No missed tasks found."
        )


# ============================================================
# PROGRESS
# ============================================================

st.markdown(
    '<div class="section-title">📈 Study Progress</div>',
    unsafe_allow_html=True
)

total, completed, percentage = get_progress()

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Total Sessions",
        total
    )

with col2:

    st.metric(
        "Completed",
        completed
    )

with col3:

    st.metric(
        "Progress",
        f"{percentage:.1f}%"
    )

st.progress(
    int(percentage)
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "SyllabusSync AI • From Syllabus to Success — "
    "Your AI-Powered Academic Planner"
)