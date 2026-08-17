import sqlite3
import json
import random

def seed_sql_course():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Find or create SQL course
    c.execute("SELECT id FROM courses WHERE LOWER(title) LIKE '%sql%'")
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO courses (title, description, pdf_file, category, order_index) VALUES (?, ?, ?, ?, ?)",
                  ("SQL Fundamentals", "Master SQL queries, database design, and data manipulation", "", "IT", 1))
        sql_id = c.lastrowid
        print(f"Created SQL Fundamentals course with ID {sql_id}")
    else:
        sql_id = row[0]
        print(f"Found existing SQL course with ID {sql_id}")

    # Clear existing questions for this course
    c.execute("DELETE FROM questions WHERE course_id=?", (sql_id,))

    questions = []

    # ═══════════════════════════════════════════════════════
    # 50 SQL MCQ QUESTIONS
    # ═══════════════════════════════════════════════════════
    mcq_data = [
        # SQL Basics
        ("Which SQL statement is used to extract data from a database?", "SELECT", "GET", "EXTRACT", "OPEN", 1),
        ("Which SQL statement is used to update data in a database?", "UPDATE", "MODIFY", "CHANGE", "SAVE", 1),
        ("Which SQL statement is used to delete data from a database?", "DELETE", "REMOVE", "COLLAPSE", "DROP", 1),
        ("Which SQL statement is used to insert new data?", "INSERT INTO", "ADD INTO", "PUT INTO", "PUSH INTO", 1),
        ("Which SQL clause is used to filter records?", "WHERE", "FILTER", "HAVING", "CONDITION", 1),
        # Aggregation
        ("Which function returns the number of rows?", "COUNT()", "SUM()", "TOTAL()", "NUM()", 1),
        ("Which function returns the average value?", "AVG()", "MEAN()", "AVERAGE()", "MID()", 1),
        ("Which function returns the highest value?", "MAX()", "TOP()", "HIGHEST()", "UPPER()", 1),
        ("Which function returns the lowest value?", "MIN()", "BOTTOM()", "LOWEST()", "LOWER()", 1),
        ("Which clause is used with aggregate functions to group results?", "GROUP BY", "ORDER BY", "SORT BY", "ARRANGE BY", 1),
        # Joins
        ("Which JOIN returns only matching rows from both tables?", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", 1),
        ("Which JOIN returns all rows from the left table?", "LEFT JOIN", "INNER JOIN", "RIGHT JOIN", "CROSS JOIN", 1),
        ("Which JOIN returns all rows from both tables?", "FULL OUTER JOIN", "INNER JOIN", "LEFT JOIN", "CROSS JOIN", 1),
        ("Which JOIN produces a Cartesian product?", "CROSS JOIN", "INNER JOIN", "LEFT JOIN", "SELF JOIN", 1),
        ("What is a SELF JOIN?", "A table joined with itself", "Join with no condition", "Join between 3 tables", "Join using primary key only", 1),
        # Keys
        ("What is a PRIMARY KEY?", "Uniquely identifies each record", "Foreign reference", "Index column", "Auto increment only", 1),
        ("What is a FOREIGN KEY?", "Links two tables together", "Primary identifier", "Unique constraint", "Index reference", 1),
        ("Can a table have multiple PRIMARY KEYs?", "No, only one", "Yes, unlimited", "Yes, up to 3", "Depends on DBMS", 1),
        ("What constraint ensures all values in a column are different?", "UNIQUE", "DISTINCT", "PRIMARY", "CHECK", 1),
        ("What does NOT NULL constraint do?", "Prevents empty values", "Removes null rows", "Sets default value", "Creates index", 1),
        # Advanced
        ("Which keyword eliminates duplicate rows?", "DISTINCT", "UNIQUE", "DIFFERENT", "NO_DUPLICATE", 1),
        ("Which clause sorts the result set?", "ORDER BY", "SORT BY", "GROUP BY", "ARRANGE BY", 1),
        ("What does LIMIT do in SQL?", "Restricts number of rows returned", "Limits column width", "Sets max value", "Truncates data", 1),
        ("Which operator checks for a value within a range?", "BETWEEN", "WITHIN", "RANGE", "IN_RANGE", 1),
        ("Which operator is used for pattern matching?", "LIKE", "MATCH", "PATTERN", "REGEX", 1),
        # Subqueries
        ("What is a subquery?", "A query within another query", "A backup query", "A stored procedure", "A trigger", 1),
        ("Which keyword is used with subqueries returning multiple values?", "IN", "EXISTS", "BETWEEN", "HAVING", 1),
        ("What does EXISTS do?", "Tests for existence of rows", "Creates a table", "Checks column type", "Validates data", 1),
        ("Can a subquery be used in a WHERE clause?", "Yes", "No", "Only with JOIN", "Only in SELECT", 1),
        ("What is a correlated subquery?", "Subquery that references outer query", "Independent subquery", "Nested function", "Recursive query", 1),
        # DDL
        ("Which SQL command creates a new table?", "CREATE TABLE", "MAKE TABLE", "NEW TABLE", "ADD TABLE", 1),
        ("Which command modifies table structure?", "ALTER TABLE", "MODIFY TABLE", "CHANGE TABLE", "UPDATE TABLE", 1),
        ("Which command removes a table completely?", "DROP TABLE", "DELETE TABLE", "REMOVE TABLE", "CLEAR TABLE", 1),
        ("What does TRUNCATE TABLE do?", "Removes all rows but keeps structure", "Drops the table", "Renames the table", "Backs up the table", 1),
        ("Which is faster: DELETE or TRUNCATE?", "TRUNCATE", "DELETE", "Both are same", "Depends on data size", 1),
        # Views and Indexes
        ("What is a VIEW in SQL?", "Virtual table based on a query", "Physical table copy", "Stored procedure", "Temporary table", 1),
        ("What is an INDEX used for?", "Speeding up data retrieval", "Sorting data permanently", "Encrypting data", "Backing up data", 1),
        ("Can you update data through a VIEW?", "Yes, with limitations", "Never", "Always", "Only with triggers", 1),
        ("What type of index is created on a PRIMARY KEY?", "Clustered", "Non-clustered", "Bitmap", "Hash", 1),
        ("Which command creates an index?", "CREATE INDEX", "ADD INDEX", "MAKE INDEX", "BUILD INDEX", 1),
        # Transactions
        ("Which command saves changes permanently?", "COMMIT", "SAVE", "PERSIST", "STORE", 1),
        ("Which command undoes changes?", "ROLLBACK", "UNDO", "REVERT", "CANCEL", 1),
        ("What does SAVEPOINT do?", "Creates a point to rollback to", "Saves the entire database", "Commits partially", "Locks a table", 1),
        ("What does ACID stand for in databases?", "Atomicity, Consistency, Isolation, Durability", "Add, Create, Insert, Delete", "Access, Control, Index, Data", "Auto, Commit, Insert, Drop", 1),
        ("What is a deadlock?", "Two transactions waiting for each other", "A crashed database", "A locked table", "An infinite loop in query", 1),
        # Normalization
        ("What is normalization?", "Organizing data to reduce redundancy", "Adding more tables", "Removing all constraints", "Encrypting data", 1),
        ("What is 1NF (First Normal Form)?", "Each column has atomic values", "No duplicate tables", "All columns are indexed", "Foreign keys exist", 1),
        ("What is denormalization?", "Adding redundancy for performance", "Removing all tables", "Dropping indexes", "Reversing constraints", 1),
        ("What is 3NF?", "No transitive dependencies", "Three tables minimum", "Three columns per table", "Three indexes required", 1),
        ("What is a composite key?", "Primary key with multiple columns", "Foreign key pair", "Unique constraint", "Auto-generated key", 1),
    ]

    # Shuffle options for each question
    for q_text, o1, o2, o3, o4, correct_idx in mcq_data:
        opts = [o1, o2, o3, o4]
        correct_val = opts[correct_idx - 1]
        random.shuffle(opts)
        new_idx = opts.index(correct_val) + 1
        questions.append((sql_id, q_text, opts[0], opts[1], opts[2], opts[3], new_idx))

    c.executemany(
        "INSERT INTO questions (course_id, question, option1, option2, option3, option4, answer) VALUES (?, ?, ?, ?, ?, ?, ?)",
        questions
    )

    # ═══════════════════════════════════════════════════════
    # 5 SQL CODING (QUERY) PROBLEMS
    # ═══════════════════════════════════════════════════════
    c.execute('''CREATE TABLE IF NOT EXISTS coding_problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT,
        difficulty TEXT,
        description TEXT,
        examples TEXT,
        constraints TEXT,
        starter_code TEXT,
        test_cases TEXT,
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS coding_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        problem_id INTEGER,
        code TEXT,
        passed INTEGER DEFAULT 0,
        total_tests INTEGER DEFAULT 0,
        passed_tests INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(problem_id) REFERENCES coding_problems(id)
    )''')

    # Clear existing coding problems for SQL course
    c.execute("DELETE FROM coding_problems WHERE course_id=?", (sql_id,))

    sql_problems = [
        {
            "course_id": sql_id,
            "title": "Find Maximum Salary",
            "difficulty": "Easy",
            "description": "Write a Python function that takes a list of employee dictionaries (with 'name' and 'salary' keys) and returns the name of the employee with the highest salary.",
            "examples": json.dumps([
                {"input": "employees = [{'name': 'Alice', 'salary': 50000}, {'name': 'Bob', 'salary': 70000}]", "output": "'Bob'", "explanation": "Bob has the highest salary of 70000."}
            ]),
            "constraints": "At least one employee in the list.",
            "starter_code": """def find_max_salary(employees):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = find_max_salary(input_data["employees"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"employees": [{"name": "Alice", "salary": 50000}, {"name": "Bob", "salary": 70000}]}, "expected": "Bob"},
                {"input": {"employees": [{"name": "Charlie", "salary": 90000}, {"name": "Dave", "salary": 45000}]}, "expected": "Charlie"},
                {"input": {"employees": [{"name": "Eve", "salary": 60000}]}, "expected": "Eve"},
            ])
        },
        {
            "course_id": sql_id,
            "title": "Filter by Department",
            "difficulty": "Easy",
            "description": "Write a function that takes a list of employee dicts (with 'name', 'department') and a target department, and returns a list of names in that department.",
            "examples": json.dumps([
                {"input": "employees = [{'name': 'A', 'department': 'IT'}, {'name': 'B', 'department': 'HR'}], dept = 'IT'", "output": "['A']", "explanation": "Only A is in IT."}
            ]),
            "constraints": "Return an empty list if no employees in that department.",
            "starter_code": """def filter_by_dept(employees, dept):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = filter_by_dept(input_data["employees"], input_data["dept"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"employees": [{"name": "A", "department": "IT"}, {"name": "B", "department": "HR"}, {"name": "C", "department": "IT"}], "dept": "IT"}, "expected": ["A", "C"]},
                {"input": {"employees": [{"name": "X", "department": "Finance"}], "dept": "HR"}, "expected": []},
                {"input": {"employees": [{"name": "Y", "department": "HR"}, {"name": "Z", "department": "HR"}], "dept": "HR"}, "expected": ["Y", "Z"]},
            ])
        },
        {
            "course_id": sql_id,
            "title": "Average Salary by Department",
            "difficulty": "Medium",
            "description": "Given a list of employee dicts with 'name', 'department', 'salary', return a dict mapping each department to its average salary (rounded to 2 decimal places).",
            "examples": json.dumps([
                {"input": "employees = [{'name': 'A', 'department': 'IT', 'salary': 50000}, {'name': 'B', 'department': 'IT', 'salary': 60000}]", "output": "{'IT': 55000.0}", "explanation": "Average of 50000 and 60000 = 55000."}
            ]),
            "constraints": "At least one employee.",
            "starter_code": """def avg_salary_by_dept(employees):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = avg_salary_by_dept(input_data["employees"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"employees": [{"name": "A", "department": "IT", "salary": 50000}, {"name": "B", "department": "IT", "salary": 60000}, {"name": "C", "department": "HR", "salary": 45000}]}, "expected": {"IT": 55000.0, "HR": 45000.0}},
                {"input": {"employees": [{"name": "D", "department": "Finance", "salary": 70000}]}, "expected": {"Finance": 70000.0}},
            ])
        },
        {
            "course_id": sql_id,
            "title": "Inner Join Simulation",
            "difficulty": "Medium",
            "description": "Given two lists: 'employees' (with 'id', 'name', 'dept_id') and 'departments' (with 'id', 'dept_name'), return a list of dicts with 'name' and 'dept_name' for matching records (like SQL INNER JOIN on dept_id = id).",
            "examples": json.dumps([
                {"input": "employees = [{'id': 1, 'name': 'Alice', 'dept_id': 10}], departments = [{'id': 10, 'dept_name': 'IT'}]", "output": "[{'name': 'Alice', 'dept_name': 'IT'}]", "explanation": "Alice's dept_id matches department id 10."}
            ]),
            "constraints": "Return empty list if no matches.",
            "starter_code": """def inner_join(employees, departments):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = inner_join(input_data["employees"], input_data["departments"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"employees": [{"id": 1, "name": "Alice", "dept_id": 10}, {"id": 2, "name": "Bob", "dept_id": 20}], "departments": [{"id": 10, "dept_name": "IT"}, {"id": 20, "dept_name": "HR"}]}, "expected": [{"name": "Alice", "dept_name": "IT"}, {"name": "Bob", "dept_name": "HR"}]},
                {"input": {"employees": [{"id": 1, "name": "Charlie", "dept_id": 99}], "departments": [{"id": 10, "dept_name": "IT"}]}, "expected": []},
            ])
        },
        {
            "course_id": sql_id,
            "title": "Group By with Having",
            "difficulty": "Hard",
            "description": "Given a list of order dicts (with 'customer', 'amount'), return a list of customers whose total order amount exceeds a given threshold, sorted alphabetically.",
            "examples": json.dumps([
                {"input": "orders = [{'customer': 'A', 'amount': 100}, {'customer': 'A', 'amount': 200}, {'customer': 'B', 'amount': 50}], threshold = 150", "output": "['A']", "explanation": "A's total is 300 (> 150), B's total is 50 (< 150)."}
            ]),
            "constraints": "Return empty list if no customer exceeds threshold.",
            "starter_code": """def group_by_having(orders, threshold):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = group_by_having(input_data["orders"], input_data["threshold"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"orders": [{"customer": "A", "amount": 100}, {"customer": "A", "amount": 200}, {"customer": "B", "amount": 50}], "threshold": 150}, "expected": ["A"]},
                {"input": {"orders": [{"customer": "X", "amount": 500}, {"customer": "Y", "amount": 300}, {"customer": "Y", "amount": 400}], "threshold": 600}, "expected": ["Y"]},
                {"input": {"orders": [{"customer": "Z", "amount": 10}], "threshold": 100}, "expected": []},
            ])
        },
    ]

    for p in sql_problems:
        c.execute(
            "INSERT INTO coding_problems (course_id, title, difficulty, description, examples, constraints, starter_code, test_cases) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (p["course_id"], p["title"], p["difficulty"], p["description"], p["examples"], p["constraints"], p["starter_code"], p["test_cases"])
        )

    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(questions)} SQL MCQs and {len(sql_problems)} SQL coding problems.")

if __name__ == "__main__":
    seed_sql_course()
