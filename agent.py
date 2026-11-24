import os
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Please check your .env file."
    )
client = Groq(api_key=API_KEY)
MODEL = "openai/gpt-oss-20b"


class SyllabusAgent:

    def __init__(self):
        self.memory = []
        self.current_plan = None

    

    def ask_ai(self, prompt):

        try:
            response = client.chat.completions.create(
                model=MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": """
You are SyllabusSync AI, an autonomous academic
planning agent.

Your responsibilities are:

1. Understand syllabus content.
2. Identify subjects and topics.
3. Prioritize topics logically.
4. Create realistic study schedules.
5. Consider deadlines and available study time.
6. Track completed and pending tasks.
7. Detect missed tasks.
8. Adjust the schedule when tasks are missed.
9. Include revision.
10. Never invent syllabus topics.
11. Give practical and achievable plans.
12. Keep the student's workload realistic.

You are not just a chatbot.
You should reason about the student's study plan
and help maintain it over time.
"""
                    },

                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2
            )

            return response.choices[0].message.content

        except Exception as e:

            return f"AI ERROR: {str(e)}"

    def analyze_syllabus(self, syllabus_text):

        prompt = f"""
Analyze the following syllabus.

SYLLABUS:
{syllabus_text}

Return the result in this structure:

SUBJECTS:
- Subject name

For every subject:

- Important topics
- Topic priority: High / Medium / Low
- Suggested study order

Rules:

- Use ONLY topics present in the syllabus.
- Do not invent topics.
- Give clear and simple explanations.
"""

        result = self.ask_ai(prompt)

        self.memory.append({
            "type": "syllabus_analysis",
            "content": result
        })

        return result

    def generate_plan(
        self,
        syllabus_text,
        start_date,
        end_date,
        hours_per_day
    ):

        prompt = f"""
Create a realistic semester study plan.

SYLLABUS:
{syllabus_text}

START DATE:
{start_date}

END DATE:
{end_date}

AVAILABLE STUDY TIME:
{hours_per_day} hours per day

Create a day-by-day study plan.

For every day include:

- Date
- Subject
- Topic
- Estimated study time
- Priority
- Revision requirement

Rules:

1. Do not schedule more hours than available.
2. Complete important topics before low-priority topics.
3. Include revision.
4. Do not invent syllabus topics.
5. Keep workload realistic.
6. Leave enough time for revision.
7. Consider the end date.
"""

        result = self.ask_ai(prompt)

        self.current_plan = result

        self.memory.append({
            "type": "study_plan",
            "content": result
        })

        return result

    
    def replan(
        self,
        original_plan,
        completed_tasks,
        missed_tasks,
        remaining_days
    ):

        prompt = f"""
You are an autonomous academic planning agent.

The student has an existing study plan.

ORIGINAL PLAN:
{original_plan}

COMPLETED TASKS:
{completed_tasks}

MISSED TASKS:
{missed_tasks}

REMAINING DAYS:
{remaining_days}

Create an UPDATED study plan.

Requirements:

1. Keep completed tasks completed.
2. Move missed tasks to suitable future dates.
3. Do not overload one day.
4. Respect available study time.
5. Prioritize important topics.
6. Include revision.
7. Keep the plan realistic.
8. Clearly explain what changed.
"""

        result = self.ask_ai(prompt)

        self.current_plan = result

        self.memory.append({
            "type": "replanned_schedule",
            "content": result
        })

        return result
    def analyze_progress(
        self,
        total_tasks,
        completed_tasks,
        missed_tasks
    ):

        prompt = f"""
Analyze the student's academic progress.

TOTAL TASKS:
{total_tasks}

COMPLETED TASKS:
{completed_tasks}

MISSED TASKS:
{missed_tasks}

Provide:

1. Completion percentage
2. Current progress status
3. Main problem
4. Recommended action
5. Whether the schedule should be adjusted
"""

        return self.ask_ai(prompt)

    def get_memory(self):

        return self.memory

    def clear_memory(self):

        self.memory = []
        self.current_plan = None


if __name__ == "__main__":

    print("\n===================================")
    print("       SYLLABUSSYNC AI")
    print("===================================\n")

    print("Connecting to Groq AI...\n")

    agent = SyllabusAgent()

    test_prompt = """
I have an Operating Systems syllabus containing:

1. Process Management
2. CPU Scheduling
3. Deadlocks
4. Memory Management
5. File Management

I have 2 hours per day available.

Tell me how you would prioritize these topics.

Give the answer in a simple numbered list.
"""

    result = agent.ask_ai(test_prompt)

    print("===== AI RESPONSE =====\n")

    print(result)

    print("\n==============================")
    print("AI Agent test completed.")
    print("==============================\n")