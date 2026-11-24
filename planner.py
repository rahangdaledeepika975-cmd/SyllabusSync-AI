from datetime import datetime, timedelta


class StudyPlanner:
    """
    SyllabusSync AI Study Planner

    This class creates a realistic study schedule
    from syllabus topics and available study time.
    """

    def __init__(self, hours_per_day=2):
        self.hours_per_day = float(hours_per_day)
        self.plan = []


    def create_plan(
        self,
        topics,
        start_date,
        end_date
    ):
        """
        Create a day-by-day study plan.

        topics format:

        [
            {
                "subject": "Operating Systems",
                "topic": "Process Management",
                "priority": "High"
            }
        ]
        """

        self.plan = []

        # Convert dates
        if isinstance(start_date, str):
            start_date = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()

        total_days = (end_date - start_date).days + 1

        if total_days <= 0:
            raise ValueError(
                "End date must be after start date."
            )

        if not topics:
            return []

        
        priority_order = {
            "High": 1,
            "Medium": 2,
            "Low": 3
        }

        topics = sorted(
            topics,
            key=lambda x: priority_order.get(
                x.get("priority", "Medium"),
                2
            )
        )

        current_date = start_date

        topic_index = 0

        while (
            current_date <= end_date
            and topic_index < len(topics)
        ):

            daily_hours = self.hours_per_day

            
            while (
                daily_hours > 0
                and topic_index < len(topics)
            ):

                topic = topics[topic_index]

                study_time = min(
                    1.0,
                    daily_hours
                )

                task = {
                    "date": current_date.strftime(
                        "%Y-%m-%d"
                    ),
                    "subject": topic.get(
                        "subject",
                        "Unknown"
                    ),
                    "topic": topic.get(
                        "topic",
                        "Unknown"
                    ),
                    "priority": topic.get(
                        "priority",
                        "Medium"
                    ),
                    "study_hours": study_time,
                    "status": "Pending"
                }

                self.plan.append(task)

                daily_hours -= study_time

                topic_index += 1

            current_date += timedelta(days=1)

        return self.plan

   

    def add_revision_days(self):
        """
        Add revision tasks after the main
        study schedule.
        """

        if not self.plan:
            return self.plan

        subjects = {}

        for task in self.plan:

            subject = task["subject"]

            if subject not in subjects:
                subjects[subject] = []

            subjects[subject].append(
                task["topic"]
            )

        last_date = datetime.strptime(
            self.plan[-1]["date"],
            "%Y-%m-%d"
        ).date()

        revision_tasks = []

        for subject, topics in subjects.items():

            last_date += timedelta(days=1)

            revision_tasks.append({
                "date": last_date.strftime(
                    "%Y-%m-%d"
                ),
                "subject": subject,
                "topic": (
                    "Revision: "
                    + ", ".join(topics)
                ),
                "priority": "High",
                "study_hours": self.hours_per_day,
                "status": "Pending"
            })

        self.plan.extend(revision_tasks)

        return self.plan

    

    def mark_completed(self, task_index):

        if (
            0 <= task_index < len(self.plan)
        ):
            self.plan[task_index]["status"] = (
                "Completed"
            )

            return True

        return False

    

    def mark_missed(self, task_index):

        if (
            0 <= task_index < len(self.plan)
        ):
            self.plan[task_index]["status"] = (
                "Missed"
            )

            return True

        return False


    def get_pending_tasks(self):

        return [
            task
            for task in self.plan
            if task["status"] == "Pending"
        ]


    def get_completed_tasks(self):

        return [
            task
            for task in self.plan
            if task["status"] == "Completed"
        ]


    def get_missed_tasks(self):

        return [
            task
            for task in self.plan
            if task["status"] == "Missed"
        ]

    def get_progress(self):

        total = len(self.plan)

        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "missed": 0,
                "pending": 0,
                "percentage": 0
            }

        completed = len(
            self.get_completed_tasks()
        )

        missed = len(
            self.get_missed_tasks()
        )

        pending = len(
            self.get_pending_tasks()
        )

        percentage = (
            completed / total
        ) * 100

        return {
            "total": total,
            "completed": completed,
            "missed": missed,
            "pending": pending,
            "percentage": round(
                percentage,
                2
            )
        }


    def display_plan(self):

        if not self.plan:
            print("No study plan available.")
            return

        print("\n========== STUDY PLAN ==========\n")

        for index, task in enumerate(
            self.plan,
            start=1
        ):

            print(
                f"{index}. "
                f"{task['date']} | "
                f"{task['subject']} | "
                f"{task['topic']} | "
                f"{task['priority']} | "
                f"{task['study_hours']} hr | "
                f"{task['status']}"
            )

        print(
            "\n================================\n"
        )

if __name__ == "__main__":

    print("\n===================================")
    print("       SYLLABUSSYNC PLANNER")
    print("===================================\n")

    topics = [
        {
            "subject": "Operating Systems",
            "topic": "Process Management",
            "priority": "High"
        },
        {
            "subject": "Operating Systems",
            "topic": "CPU Scheduling",
            "priority": "High"
        },
        {
            "subject": "Operating Systems",
            "topic": "Deadlocks",
            "priority": "High"
        },
        {
            "subject": "Operating Systems",
            "topic": "Memory Management",
            "priority": "Medium"
        },
        {
            "subject": "Operating Systems",
            "topic": "File Management",
            "priority": "Low"
        }
    ]

    planner = StudyPlanner(
        hours_per_day=2
    )

    plan = planner.create_plan(
        topics=topics,
        start_date="2026-11-09",
        end_date="2026-11-13"
    )

    planner.add_revision_days()

    planner.display_plan()

    print("Progress:")

    print(
        planner.get_progress()
    )