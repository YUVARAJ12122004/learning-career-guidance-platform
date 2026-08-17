import sqlite3

def verify_questions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT c.title, COUNT(q.id) 
        FROM courses c 
        LEFT JOIN questions q ON c.id=q.course_id 
        WHERE c.category="Aptitude" 
        GROUP BY c.title
    ''')
    for row in c.fetchall():
        print(f"{row[0]}: {row[1]} questions")
    conn.close()

if __name__ == "__main__":
    verify_questions()
