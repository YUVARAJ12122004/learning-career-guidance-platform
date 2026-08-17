import sqlite3
import random

def seed_java_questions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Add question_type column if not exists
    try:
        c.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'mcq'")
        print("Added question_type column.")
    except:
        print("question_type column already exists.")

    # Get Java Foundation course ID
    row = c.execute("SELECT id FROM courses WHERE title='java foundation'").fetchone()
    if not row:
        row = c.execute("SELECT id FROM courses WHERE LOWER(title) LIKE '%java%'").fetchone()
    if not row:
        print("Java Foundation course not found!")
        conn.close()
        return
    
    java_id = row[0]
    print(f"Java Foundation course ID: {java_id}")

    # Clear existing questions for this course
    c.execute("DELETE FROM questions WHERE course_id=?", (java_id,))

    questions = []

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1: 50 Java Theory MCQ Questions (unique, covering core topics)
    # ═══════════════════════════════════════════════════════════════════════

    mcqs = [
        # --- Basics & Syntax (Q1-Q10) ---
        ("Which keyword is used to define a class in Java?", "class", "define", "struct", "object", 1),
        ("What is the default value of an int variable in Java?", "0", "null", "1", "undefined", 1),
        ("Which method is the entry point of a Java program?", "main()", "start()", "init()", "run()", 1),
        ("Java is a ___-oriented programming language.", "Object", "Procedure", "Function", "Logic", 1),
        ("Which of these is NOT a primitive data type in Java?", "String", "int", "boolean", "double", 1),
        ("What does JVM stand for?", "Java Virtual Machine", "Java Variable Manager", "Java Version Module", "Java Visual Machine", 1),
        ("Which symbol is used for single-line comments in Java?", "//", "/* */", "#", "--", 1),
        ("What is the size of an int in Java?", "4 bytes", "2 bytes", "8 bytes", "1 byte", 1),
        ("Which of the following is a valid variable name in Java?", "_count", "2value", "class", "my-var", 1),
        ("What is the output of: System.out.println(5 + 3 + \"Java\");?", "8Java", "53Java", "Java53", "Java8", 1),

        # --- OOP Concepts (Q11-Q20) ---
        ("Which OOP principle allows a class to inherit properties from another class?", "Inheritance", "Encapsulation", "Polymorphism", "Abstraction", 1),
        ("Which keyword is used to inherit a class in Java?", "extends", "implements", "inherits", "super", 1),
        ("What is encapsulation?", "Wrapping data and methods together", "Hiding methods from other classes", "Creating multiple objects", "Overriding a method", 1),
        ("Which keyword prevents a class from being inherited?", "final", "static", "abstract", "private", 1),
        ("What is polymorphism in Java?", "Same method behaving differently", "Creating new classes", "Hiding data", "Using multiple threads", 1),
        ("Which keyword is used to refer to the current object?", "this", "self", "current", "me", 1),
        ("An abstract class can have:", "Both abstract and concrete methods", "Only abstract methods", "Only concrete methods", "No methods at all", 1),
        ("Which of the following supports multiple inheritance in Java?", "Interface", "Abstract class", "Final class", "Static class", 1),
        ("What is method overloading?", "Same method name with different parameters", "Same method name in parent and child class", "A method with no return type", "A method that calls itself", 1),
        ("Constructor in Java is used to:", "Initialize objects", "Destroy objects", "Return values", "Import packages", 1),

        # --- Control Flow (Q21-Q25) ---
        ("Which loop is guaranteed to execute at least once?", "do-while", "for", "while", "foreach", 1),
        ("What is the output of: for(int i=0; i<3; i++) { } System.out.println(i);?", "Compilation error", "3", "2", "0", 1),
        ("Which statement is used to exit a loop prematurely?", "break", "continue", "return", "exit", 1),
        ("What does the 'continue' statement do?", "Skips the current iteration", "Exits the loop", "Restarts the loop", "Terminates the program", 1),
        ("The switch statement in Java can accept which data type?", "All of the above", "int", "String", "char", 1),

        # --- Exception Handling (Q26-Q30) ---
        ("Which keyword is used to handle exceptions in Java?", "try-catch", "if-else", "do-while", "switch-case", 1),
        ("What is the parent class of all exceptions in Java?", "Throwable", "Exception", "Error", "RuntimeException", 1),
        ("Which block always executes whether an exception occurs or not?", "finally", "catch", "try", "throw", 1),
        ("What type of exception is ArrayIndexOutOfBoundsException?", "Unchecked", "Checked", "Error", "Compile-time", 1),
        ("Which keyword is used to explicitly throw an exception?", "throw", "throws", "try", "catch", 1),

        # --- Collections & Arrays (Q31-Q35) ---
        ("What is the index of the first element of an array in Java?", "0", "1", "-1", "null", 1),
        ("Which collection allows duplicate elements?", "ArrayList", "HashSet", "TreeSet", "LinkedHashSet", 1),
        ("HashMap stores data in which format?", "Key-Value pair", "Index-Value pair", "Stack order", "Queue order", 1),
        ("Which interface does ArrayList implement?", "List", "Set", "Map", "Queue", 1),
        ("What is the time complexity of ArrayList.get(index)?", "O(1)", "O(n)", "O(log n)", "O(n²)", 1),

        # --- Strings (Q36-Q40) ---
        ("Strings in Java are:", "Immutable", "Mutable", "Primitive", "Static", 1),
        ("Which method is used to compare two strings in Java?", "equals()", "==", "compare()", "match()", 1),
        ("What does the charAt() method return?", "A character at the given index", "A substring", "The string length", "A boolean", 1),
        ("What is the output of: \"Hello\".length();?", "5", "4", "6", "Error", 1),
        ("StringBuilder is preferred over String because:", "It is mutable and faster for concatenation", "It is immutable", "It uses less memory always", "It is thread-safe", 1),

        # --- Multithreading & Advanced (Q41-Q45) ---
        ("Which class is used to create a thread in Java?", "Thread", "Runnable", "Process", "Task", 1),
        ("Which keyword is used to synchronize a method?", "synchronized", "volatile", "transient", "static", 1),
        ("What is a deadlock in Java?", "Two threads waiting for each other indefinitely", "A thread that runs forever", "An exception in threading", "A thread with no run method", 1),
        ("Which interface must be implemented to create a thread?", "Runnable", "Callable", "Serializable", "Comparable", 1),
        ("What does the volatile keyword do?", "Ensures visibility of changes across threads", "Makes a variable constant", "Creates a new thread", "Locks a method", 1),

        # --- Miscellaneous (Q46-Q50) ---
        ("What is the purpose of the 'static' keyword?", "Shared across all instances of a class", "Creates a new object", "Makes a method abstract", "Prevents inheritance", 1),
        ("Which access modifier makes a member accessible only within the same class?", "private", "public", "protected", "default", 1),
        ("What is autoboxing in Java?", "Automatic conversion of primitive to wrapper class", "Automatic type casting", "Boxing a class inside another", "Creating arrays automatically", 1),
        ("Which feature was introduced in Java 8?", "Lambda expressions", "Generics", "Annotations", "Enums", 1),
        ("What is the purpose of the 'super' keyword?", "To call the parent class constructor or method", "To create a new object", "To define a static method", "To handle exceptions", 1),
    ]

    for q_text, o1, o2, o3, o4, ans in mcqs:
        questions.append((java_id, q_text, o1, o2, o3, o4, ans, 'mcq'))

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 2: 5 LeetCode-Style Coding MCQ Questions
    # ═══════════════════════════════════════════════════════════════════════

    # Shuffle options for each question (keeping correct answer tracked)
    final_questions = []
    for q in questions:
        cid, qtext, o1, o2, o3, o4, ans_idx, qtype = q
        opts = [o1, o2, o3, o4]
        correct_val = opts[ans_idx - 1]
        random.shuffle(opts)
        new_ans_idx = opts.index(correct_val) + 1
        final_questions.append((cid, qtext, opts[0], opts[1], opts[2], opts[3], new_ans_idx, qtype))

    # Insert into DB
    c.executemany(
        "INSERT INTO questions (course_id, question, option1, option2, option3, option4, answer, question_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        final_questions
    )
    conn.commit()
    conn.close()

    mcq_count = sum(1 for q in final_questions if q[7] == 'mcq')
    coding_count = sum(1 for q in final_questions if q[7] == 'coding')
    print(f"Successfully seeded {len(final_questions)} Java Foundation questions ({mcq_count} MCQ + {coding_count} Coding).")

if __name__ == "__main__":
    seed_java_questions()
