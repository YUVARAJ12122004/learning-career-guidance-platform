import sqlite3
import json

def seed_coding_problems():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create coding_problems table
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

    # Create coding_submissions table
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

    # Get Java Foundation course ID
    row = c.execute("SELECT id FROM courses WHERE LOWER(title) LIKE '%java%'").fetchone()
    if not row:
        print("Java Foundation course not found!")
        conn.close()
        return
    java_id = row[0]

    # Clear existing coding problems for this course
    c.execute("DELETE FROM coding_problems WHERE course_id=?", (java_id,))

    problems = [
        # ═══════════════════════════════════════════════════════════════
        # EASY 1: Two Sum
        # ═══════════════════════════════════════════════════════════════
        {
            "course_id": java_id,
            "title": "Two Sum",
            "difficulty": "Easy",
            "description": """Given an array of integers `nums` and an integer `target`, return the **indices** of the two numbers such that they add up to `target`.

You may assume that each input would have **exactly one solution**, and you may not use the same element twice.

Return the answer as a list of two indices sorted in ascending order.""",
            "examples": json.dumps([
                {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."},
                {"input": "nums = [3, 2, 4], target = 6", "output": "[1, 2]", "explanation": "Because nums[1] + nums[2] == 6, we return [1, 2]."},
                {"input": "nums = [3, 3], target = 6", "output": "[0, 1]", "explanation": "Because nums[0] + nums[1] == 6, we return [0, 1]."}
            ]),
            "constraints": "2 <= len(nums) <= 10^4\n-10^9 <= nums[i] <= 10^9\nOnly one valid answer exists.",
            "starter_code": """def two_sum(nums, target):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = two_sum(input_data["nums"], input_data["target"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
                {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
                {"input": {"nums": [3, 3], "target": 6}, "expected": [0, 1]},
                {"input": {"nums": [1, 5, 3, 7], "target": 8}, "expected": [1, 2]},
                {"input": {"nums": [-1, 0, 1, 2], "target": 1}, "expected": [0, 2]},
            ])
        },

        # ═══════════════════════════════════════════════════════════════
        # EASY 2: Reverse Integer
        # ═══════════════════════════════════════════════════════════════
        {
            "course_id": java_id,
            "title": "Reverse Integer",
            "difficulty": "Easy",
            "description": """Given a signed 32-bit integer `x`, return `x` with its digits reversed.

If reversing `x` causes the value to go outside the signed 32-bit integer range `[-2^31, 2^31 - 1]`, then return `0`.""",
            "examples": json.dumps([
                {"input": "x = 123", "output": "321", "explanation": "Reversed digits of 123 is 321."},
                {"input": "x = -123", "output": "-321", "explanation": "Reversed digits of -123 is -321."},
                {"input": "x = 120", "output": "21", "explanation": "Reversed digits of 120 is 21 (leading zeros are dropped)."}
            ]),
            "constraints": "-2^31 <= x <= 2^31 - 1",
            "starter_code": """def reverse_integer(x):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = reverse_integer(input_data["x"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"x": 123}, "expected": 321},
                {"input": {"x": -123}, "expected": -321},
                {"input": {"x": 120}, "expected": 21},
                {"input": {"x": 0}, "expected": 0},
                {"input": {"x": 1534236469}, "expected": 0},
            ])
        },

        # ═══════════════════════════════════════════════════════════════
        # EASY 3: Palindrome Number
        # ═══════════════════════════════════════════════════════════════
        {
            "course_id": java_id,
            "title": "Palindrome Number",
            "difficulty": "Easy",
            "description": """Given an integer `x`, return `True` if `x` is a **palindrome**, and `False` otherwise.

An integer is a palindrome when it reads the same forward and backward. For example, `121` is a palindrome while `123` is not.

**Negative numbers are NOT palindromes.**""",
            "examples": json.dumps([
                {"input": "x = 121", "output": "true", "explanation": "121 reads as 121 from left to right and from right to left."},
                {"input": "x = -121", "output": "false", "explanation": "From left to right, it reads -121. From right to left it becomes 121-. Therefore it is not a palindrome."},
                {"input": "x = 10", "output": "false", "explanation": "Reads 01 from right to left. Therefore it is not a palindrome."}
            ]),
            "constraints": "-2^31 <= x <= 2^31 - 1",
            "starter_code": """def is_palindrome(x):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = is_palindrome(input_data["x"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"x": 121}, "expected": True},
                {"input": {"x": -121}, "expected": False},
                {"input": {"x": 10}, "expected": False},
                {"input": {"x": 12321}, "expected": True},
                {"input": {"x": 0}, "expected": True},
            ])
        },

        # ═══════════════════════════════════════════════════════════════
        # MEDIUM 1: Longest Substring Without Repeating Characters
        # ═══════════════════════════════════════════════════════════════
        {
            "course_id": java_id,
            "title": "Longest Substring Without Repeating Characters",
            "difficulty": "Medium",
            "description": """Given a string `s`, find the **length of the longest substring** without repeating characters.

A **substring** is a contiguous non-empty sequence of characters within a string.""",
            "examples": json.dumps([
                {"input": "s = \"abcabcbb\"", "output": "3", "explanation": "The answer is 'abc', with the length of 3."},
                {"input": "s = \"bbbbb\"", "output": "1", "explanation": "The answer is 'b', with the length of 1."},
                {"input": "s = \"pwwkew\"", "output": "3", "explanation": "The answer is 'wke', with the length of 3."}
            ]),
            "constraints": "0 <= len(s) <= 5 * 10^4\ns consists of English letters, digits, symbols and spaces.",
            "starter_code": """def length_of_longest_substring(s):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = length_of_longest_substring(input_data["s"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"s": "abcabcbb"}, "expected": 3},
                {"input": {"s": "bbbbb"}, "expected": 1},
                {"input": {"s": "pwwkew"}, "expected": 3},
                {"input": {"s": ""}, "expected": 0},
                {"input": {"s": "abcdef"}, "expected": 6},
                {"input": {"s": "aab"}, "expected": 2},
            ])
        },

        # ═══════════════════════════════════════════════════════════════
        # MEDIUM 2: Container With Most Water
        # ═══════════════════════════════════════════════════════════════
        {
            "course_id": java_id,
            "title": "Container With Most Water",
            "difficulty": "Medium",
            "description": """You are given an integer array `height` of length `n`. There are `n` vertical lines drawn such that the two endpoints of the i-th line are `(i, 0)` and `(i, height[i])`.

Find two lines that together with the x-axis form a container, such that the container contains the **most water**.

Return the **maximum amount of water** a container can store.

**Note:** You may not slant the container.""",
            "examples": json.dumps([
                {"input": "height = [1,8,6,2,5,4,8,3,7]", "output": "49", "explanation": "The max area is between lines at index 1 and 8 (heights 8 and 7), giving area = min(8,7) * (8-1) = 49."},
                {"input": "height = [1,1]", "output": "1", "explanation": "Only two lines, area = min(1,1) * (1-0) = 1."}
            ]),
            "constraints": "n == len(height)\n2 <= n <= 10^5\n0 <= height[i] <= 10^4",
            "starter_code": """def max_area(height):
    # Write your code here
    pass

# Do NOT modify below this line
import sys, json
input_data = json.loads(sys.stdin.read())
result = max_area(input_data["height"])
print(json.dumps(result))""",
            "test_cases": json.dumps([
                {"input": {"height": [1,8,6,2,5,4,8,3,7]}, "expected": 49},
                {"input": {"height": [1,1]}, "expected": 1},
                {"input": {"height": [4,3,2,1,4]}, "expected": 16},
                {"input": {"height": [1,2,1]}, "expected": 2},
                {"input": {"height": [2,3,4,5,18,17,6]}, "expected": 17},
            ])
        },
    ]

    for p in problems:
        c.execute(
            "INSERT INTO coding_problems (course_id, title, difficulty, description, examples, constraints, starter_code, test_cases) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (p["course_id"], p["title"], p["difficulty"], p["description"], p["examples"], p["constraints"], p["starter_code"], p["test_cases"])
        )

    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(problems)} coding problems for Java Foundation.")

if __name__ == "__main__":
    seed_coding_problems()
