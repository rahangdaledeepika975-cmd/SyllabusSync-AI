import sqlite3
from datetime import datetime


class Memory:

    def __init__(self, db_name="syllabus_sync.db"):
        self.db_name = db_name
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()

       
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                study_date TEXT,
                topic TEXT,
                status TEXT DEFAULT 'Pending'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT,
                value TEXT,
                created_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS syllabus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                content TEXT,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()

  

    def save_task(self, task):
        conn = self.connect()
        cursor = conn.cursor()

        task_id = str(task.get("id", datetime.now().timestamp()))
        study_date = task.get("date", task.get("study_date", ""))
        topic = task.get("topic", "")
        status = task.get("status", "Pending")

        cursor.execute("""
            INSERT OR REPLACE INTO tasks
            (id, study_date, topic, status)
            VALUES (?, ?, ?, ?)
        """, (
            task_id,
            study_date,
            topic,
            status
        ))

        conn.commit()
        conn.close()

    def save_plan(self, tasks):
        for task in tasks:
            self.save_task(task)

    def get_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, study_date, topic, status
            FROM tasks
            ORDER BY study_date
        """)

        rows = cursor.fetchall()
        conn.close()

        return self._convert_tasks(rows)

    def get_pending_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, study_date, topic, status
            FROM tasks
            WHERE status = 'Pending'
            ORDER BY study_date
        """)

        rows = cursor.fetchall()
        conn.close()

        return self._convert_tasks(rows)

    def get_completed_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, study_date, topic, status
            FROM tasks
            WHERE status = 'Completed'
            ORDER BY study_date
        """)

        rows = cursor.fetchall()
        conn.close()

        return self._convert_tasks(rows)

    def get_missed_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, study_date, topic, status
            FROM tasks
            WHERE status = 'Missed'
            ORDER BY study_date
        """)

        rows = cursor.fetchall()
        conn.close()

        return self._convert_tasks(rows)

    def update_task_status(self, task_id, status):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tasks
            SET status = ?
            WHERE id = ?
        """, (status, str(task_id)))

        conn.commit()
        conn.close()

   

    def save_memory(self, key, value):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_memory
            (key, value, created_at)
            VALUES (?, ?, ?)
        """, (
            key,
            str(value),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def get_memory(self, key=None):
        conn = self.connect()
        cursor = conn.cursor()

        if key:
            cursor.execute("""
                SELECT value
                FROM agent_memory
                WHERE key = ?
                ORDER BY id DESC
            """, (key,))
        else:
            cursor.execute("""
                SELECT key, value
                FROM agent_memory
                ORDER BY id DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return rows

    
    def save_syllabus(self, subject, content):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO syllabus
            (subject, content, created_at)
            VALUES (?, ?, ?)
        """, (
            subject,
            content,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def get_syllabus(self, subject=None):
        conn = self.connect()
        cursor = conn.cursor()

        if subject:
            cursor.execute("""
                SELECT subject, content
                FROM syllabus
                WHERE subject = ?
                ORDER BY id DESC
            """, (subject,))
        else:
            cursor.execute("""
                SELECT subject, content
                FROM syllabus
                ORDER BY id DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return rows

   
    def get_statistics(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE status = 'Completed'
        """)
        completed = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE status = 'Missed'
        """)
        missed = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE status = 'Pending'
        """)
        pending = cursor.fetchone()[0]

        conn.close()

        percentage = 0

        if total > 0:
            percentage = round((completed / total) * 100, 2)

        return {
            "total": total,
            "completed": completed,
            "missed": missed,
            "pending": pending,
            "percentage": percentage
        }

  

    def clear_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tasks")

        conn.commit()
        conn.close()

    

    def _convert_tasks(self, rows):

        tasks = []

        for row in rows:

            tasks.append({
                "id": row[0],
                "date": row[1],
                "study_date": row[1],
                "topic": row[2],
                "status": row[3]
            })

        return tasks



if __name__ == "__main__":

    print("===================================")
    print("       SYLLABUSSYNC MEMORY")
    print("===================================")

    memory = Memory()

    test_task = {
        "id": "test_001",
        "date": "2026-11-09",
        "topic": "Process Management",
        "status": "Pending"
    }

    memory.save_task(test_task)

    print("\nTask saved successfully!")

    print("\nAll Tasks:")
    print(memory.get_tasks())

    print("\nStatistics:")
    print(memory.get_statistics())

    print("\n===================================")
    print("Memory test completed.")
    print("===================================")