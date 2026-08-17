import sqlite3

def remove_extra_questions():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    # Remove Java course (assuming ID 1) questions of type 'coding'
    # The user said they are MCQs but were added as "coding" type in seed_java.py
    c.execute("DELETE FROM questions WHERE course_id = 1 AND question_type = 'coding'")
    deleted = c.rowcount
    conn.commit()
    conn.close()
    print(f"Deleted {deleted} extra questions from course 1.")

if __name__ == "__main__":
    remove_extra_questions()
