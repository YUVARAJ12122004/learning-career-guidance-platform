import sqlite3
import random

def seed_aptitude_questions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Ensure Aptitude courses exist
    courses = [
        ("Logical Aptitude", "Develop logical reasoning skills essential for aptitude tests", "/static/videos/logical.mp4", "Aptitude", 0),
        ("Quantitative Aptitude", "Master quantitative and mathematical problem-solving", "/static/videos/quantitative.mp4", "Aptitude", 1),
        ("Communication Aptitude", "Enhance verbal and communication abilities for assessments", "/static/videos/communication.mp4", "Aptitude", 2)
    ]
    
    course_ids = {}
    for title, desc, url, cat, idx in courses:
        c.execute("SELECT id FROM courses WHERE title=?", (title,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO courses (title, description, pdf_file, category, order_index) VALUES (?, ?, ?, ?, ?)", (title, desc, url, cat, idx))
            course_ids[title] = c.lastrowid
        else:
            course_ids[title] = row[0]

    for cid in course_ids.values():
        c.execute("DELETE FROM questions WHERE course_id=?", (cid,))

    logical_id = course_ids["Logical Aptitude"]
    quant_id = course_ids["Quantitative Aptitude"]
    comm_id = course_ids["Communication Aptitude"]

    questions = []

    # --- Quantitative Aptitude (50) ---
    base_values_quant = [
        # Work
        [(10, 15), (20, 30), (12, 24), (8, 24), (15, 30), (18, 9), (6, 12), (16, 48), (25, 75), (14, 35)],  
        # Speed
        [(100, 36), (150, 54), (200, 72), (250, 90), (300, 108), (120, 72), (180, 54), (240, 36), (280, 54), (320, 72)], 
        # Profit
        [(1000, 1200), (500, 750), (400, 500), (2000, 2500), (800, 1000), (300, 360), (1500, 1800), (250, 300), (600, 900), (1200, 1500)], 
        # SI
        [(5000, 5), (8000, 10), (12000, 8), (4000, 12), (15000, 6), (7500, 4), (10000, 9), (6000, 7), (20000, 5), (2500, 8)], 
        # Ratio
        [(40, 3), (60, 2), (80, 4), (100, 3), (45, 8), (50, 4), (75, 2), (90, 5), (30, 2), (120, 3)] 
    ]
    
    for i in range(10):
        # 1. Work
        v1, v2 = base_values_quant[0][i]
        ans = (v1 * v2) / (v1 + v2)
        qtext = f"TCS Pattern: A can do a piece of work in {v1} days and B in {v2} days. If they work together, in how many days will they finish it?"
        o1, o2, o3, o4 = f"{ans:.1f}", f"{ans + 2.5:.1f}", f"{ans - 1.2:.1f}", f"{ans * 1.5:.1f}"
        if ans == int(ans): o1, o2, o3, o4 = str(int(ans)), str(int(ans + 2)), str(int(ans - 1)), str(int(ans * 2))
        questions.append((quant_id, qtext, o1, o2, o3, o4, 1))
        
        # 2. Speed 
        v1, v2 = base_values_quant[1][i]
        ans = v1 / (v2 * 5 / 18)
        qtext = f"Wipro Pattern: A train {v1}m long running at {v2} km/hr will cross a pole in how many seconds?"
        o1, o2, o3, o4 = f"{ans:.1f}", f"{ans + 5:.1f}", f"{ans - 2:.1f}", f"{ans * 1.5:.1f}"
        if ans == int(ans): o1, o2, o3, o4 = str(int(ans)), str(int(ans + 5)), str(int(ans - 2)), str(int(ans * 2))
        questions.append((quant_id, qtext, o1, o2, o3, o4, 1))

        # 3. Profit
        v1, v2 = base_values_quant[2][i]
        ans = ((v2 - v1) / v1) * 100
        qtext = f"Infosys Pattern: If the cost price of an article is Rs. {v1} and selling price is Rs. {v2}, what is the profit percentage?"
        o1, o2, o3, o4 = f"{ans:.1f}%", f"{ans + 5:.1f}%", f"{ans - 5:.1f}%", f"{ans * 1.5:.1f}%"
        if ans == int(ans): o1, o2, o3, o4 = f"{int(ans)}%", f"{int(ans + 5)}%", f"{int(ans - 5)}%", f"{int(ans * 2)}%"
        questions.append((quant_id, qtext, o1, o2, o3, o4, 1))

        # 4. SI
        v1, v2 = base_values_quant[3][i]
        ans = (v1 * v2 * 2) / 100
        qtext = f"Cognizant Level: The simple interest on Rs. {v1} for 2 years at {v2}% per annum is?"
        o1, o2, o3, o4 = str(int(ans)), str(int(ans + 100)), str(int(ans - 150)), str(int(ans * 1.5))
        questions.append((quant_id, qtext, o1, o2, o3, o4, 1))

        # 5. Ratio mixture
        v1, v2 = base_values_quant[4][i]
        ans = (v1 * v2) / (v2 + 1)
        qtext = f"Accenture Pattern: A mixture of {v1} liters contains milk and water in the ratio {v2}:1. How much milk is present?"
        o1, o2, o3, o4 = f"{ans:.1f}L", f"{ans + 5:.1f}L", f"{ans - 3:.1f}L", f"{ans * 1.5:.1f}L"
        if ans == int(ans): o1, o2, o3, o4 = f"{int(ans)}L", f"{int(ans + 5)}L", f"{int(ans - 3)}L", f"{int(ans * 2)}L"
        questions.append((quant_id, qtext, o1, o2, o3, o4, 1))

    # --- Logical Aptitude (50) ---
    for i in range(1, 11):
        # 1. AP Series
        base = i * 3
        s = (base, base+2, base+4, base+6, base+8)
        ans = s[4]
        questions.append((logical_id, f"TCS NQT: Find the next number in the series: {s[0]}, {s[1]}, {s[2]}, {s[3]}, ?", str(ans), str(ans+1), str(ans+2), str(ans-1), 1))
        
        # 2. GP Series
        s = (i, i*2, i*4, i*8, i*16)
        ans = s[4]
        questions.append((logical_id, f"Infosys Level: Find the next number: {s[0]}, {s[1]}, {s[2]}, {s[3]}, ?", str(ans), str(ans+4), str(ans*2), str(ans+2), 1))
        
        # 3. Directions
        dist1, dist2 = i*2, (i*2)+3
        ans = ((dist1**2) + (dist2**2))**0.5
        qtext = f"Capgemini Pattern: A man walks {dist1} km East, then turns right and walks {dist2} km. How far is he from the starting point?"
        questions.append((logical_id, qtext, f"{ans:.1f} km", f"{ans+2:.1f} km", f"{ans+4:.1f} km", f"{ans+1:.1f} km", 1))
        
        # 4. Coding
        shift = i
        coded = "".join(chr((ord(c)-65+shift)%26+65) for c in "NEXT")
        qtext = f"Wipro Pattern: In a certain code, ABCD is written as {''.join(chr((ord(c)-65+shift)%26+65) for c in 'ABCD')}. How is NEXT written?"
        questions.append((logical_id, qtext, coded, coded[::-1], "M" + coded[1:], coded[1:] + "Z", 1))
        
        # 5. Blood Relations
        blood_relations = [
            ("Pointing to a photograph, a person says 'He is the son of my father's only son'. How is the person related to the speaker?", "Son", "Brother", "Father", "Cousin"),
            ("A man said to a lady, 'Your mother's husband's sister is my aunt.' How is the lady related to the man?", "Sister", "Mother", "Daughter", "Aunt"),
            ("Pointing to a girl, a man said, 'She is the daughter of my grandfather's only child.' How is the girl related to the man?", "Sister", "Cousin", "Niece", "Mother"),
            ("If A is the brother of B; B is the sister of C; and C is the father of D, how D is related to A?", "Nephew or Niece", "Brother", "Uncle", "Cannot be determined"),
            ("Pointing a photograph, X said to his friend Y, 'She is the only daughter of the father of my mother.' How X is related to the person of photograph?", "Son", "Nephew", "Brother", "Cousin"),
            ("A family consists of six members A, B, C, D, E and F. B is the son of C but C is not the mother of B. A and C are married couple. E is the brother of C. D is the daughter of A. F is the brother of B. How many male members are there in the family?", "4", "3", "2", "5"),
            ("A girl introduced a boy as the son of the daughter of the father of her uncle. The boy is girl's?", "Brother", "Son", "Uncle", "Nephew"),
            ("Pointing to a lady a person said, \"The son of her only brother is the brother of my wife.\" How is the lady related to the person?", "Sister of father-in-law", "Mother-in-law", "Maternal aunt", "None of these"),
            ("P is the brother of Q and R. S is R's mother. T is P's father. Which of the following statements cannot be definitely true?", "T is Q's husband", "T is S's husband", "S is P's mother", "P is S's son"),
            ("Pointing to a gentleman, Deepak said, \"His only brother is the father of my daughter's father.\" How is the gentleman related to Deepak?", "Uncle", "Grandfather", "Father", "Brother-in-law")
        ]
        q_text, ans, w1, w2, w3 = blood_relations[i-1]
        questions.append((logical_id, f"Cognizant Pattern (Scenario {i}): {q_text}", ans, w1, w2, w3, 1))

    # --- Communication Aptitude (50) ---
    vocab_syn = [("Lucid","Clear","Vague","Dark","Muddy"), 
                 ("Mitigate","Lessen","Increase","Aggravate","Worsen"),
                 ("Candid","Frank","Deceptive","Secretive","Shy"),
                 ("Ephemeral","Short-lived","Permanent","Lasting","Eternal"),
                 ("Tenacious","Persistent","Weak","Frail","Yielding"),
                 ("Audacious","Bold","Timid","Fearful","Cowardly"),
                 ("Pragmatic","Practical","Theoretical","Idealistic","Impractical"),
                 ("Meticulous","Careful","Careless","Sloppy","Reckless"),
                 ("Obscure","Unclear","Obvious","Evident","Lucid"),
                 ("Superfluous","Extra","Necessary","Essential","Crucial")]
    
    vocab_ant = [("Abundant","Scarce","Plentiful","Ample","Copious"),
                 ("Diligent","Lazy","Hardworking","Active","Attentive"),
                 ("Optimistic","Pessimistic","Hopeful","Confident","Positive"),
                 ("Arrogant","Humble","Proud","Haughty","Conceited"),
                 ("Barren","Fertile","Empty","Desolate","Dry"),
                 ("Dynamic","Static","Active","Energetic","Lively"),
                 ("Harsh","Gentle","Severe","Strict","Cruel"),
                 ("Frugal","Extravagant","Thrifty","Economical","Sparing"),
                 ("Gloomy","Cheerful","Dark","Dim","Sad"),
                 ("Hostile","Friendly","Unfriendly","Aggressive","Belligerent")]
    
    preps = [
        ("He is good ___ mathematics.", "at", "in", "on", "with"),
        ("She has been living here ___ 2010.", "since", "from", "for", "by"),
        ("The cat jumped ___ the table.", "onto", "in", "above", "underneath"),
        ("He prefers tea ___ coffee.", "to", "over", "than", "from"),
        ("They agreed ___ the proposed plan.", "to", "with", "on", "for"),
        ("The book was written ___ a famous author.", "by", "with", "from", "through"),
        ("She is afraid ___ spiders.", "of", "from", "by", "with"),
        ("We will meet ___ Monday.", "on", "in", "at", "by"),
        ("He was accused ___ theft.", "of", "for", "with", "about"),
        ("She is looking forward ___ seeing him.", "to", "for", "about", "at")
    ]
    
    spels = [
        ("Accommodate", "Acommodate", "Accomodate", "Acomodate"), 
        ("Embarrass", "Embarass", "Embaras", "Emmbarrass"),
        ("Occasion", "Ocassion", "Occassion", "Ocaasion"),
        ("Receive", "Recieve", "Receve", "Receeve"),
        ("Separate", "Seperate", "Seprate", "Saperate"),
        ("Definitely", "Definately", "Definitly", "Defanately"),
        ("Committee", "Comittee", "Commitee", "Comitee"),
        ("Pronunciation", "Pronounciation", "Pronunsiation", "Pronunciaton"),
        ("Restaurant", "Restarant", "Resaurant", "Restraunt"),
        ("Rhythm", "Rythm", "Rhythum", "Rythum")
    ]
    
    errs = [
        ("He returned back to his hometown.", "returned", "returned back", "return back", "had returned back"),
        ("We need to discuss about the matter.", "discuss the matter", "discuss on the matter", "discuss around the matter", "discussing about the matter"),
        ("It was a huge blunder mistake.", "blunder", "mistake blunder", "blunder mistake", "big blunder mistake"),
        ("I cannot cope up with this pressure.", "cope with", "cope up with", "coping up with", "cope up to"),
        ("This is more better than that.", "better", "more better", "much more better", "most better"),
        ("Please reply back to my email.", "reply", "reply back", "replying back", "replied back"),
        ("I will revert back to you shortly.", "revert", "revert back", "reverting back", "reverted back"),
        ("They reached the final conclusion.", "conclusion", "final conclusion", "finall conclusion", "last final conclusion"),
        ("The past history of the fort is fascinating.", "history", "past history", "historical past", "time history"),
        ("She gave me a free gift.", "gift", "free gift", "free gifts", "cost free gift")
    ]

    for i in range(10):
        # 1. Syn
        v, ans, w1, w2, w3 = vocab_syn[i]
        questions.append((comm_id, f"TCS Verbal: Choose the correct synonym for '{v}':", ans, w1, w2, w3, 1))
        # 2. Ant
        v, ans, w1, w2, w3 = vocab_ant[i]
        questions.append((comm_id, f"Infosys English: Choose the correct antonym for '{v}':", ans, w1, w2, w3, 1))
        # 3. Prep
        qtext, ans, w1, w2, w3 = preps[i]
        questions.append((comm_id, f"Wipro Verbal: Fill in the blank: {qtext}", ans, w1, w2, w3, 1))
        # 4. Spel
        ans, w1, w2, w3 = spels[i]
        questions.append((comm_id, f"Cognizant Communication: Select the correctly spelt word:", ans, w1, w2, w3, 1))
        # 5. Err
        sentence, ans, w1, w2, w3 = errs[i]
        questions.append((comm_id, f"Accenture Verbal: Select the correct formulation for the erroneous sentence '{sentence}'", ans, w1, w2, w3, 1))

    # To mix correct answer position, we can shuffle options, but keeping answer as 1,2,3,4. 
    # For a robust system, we shuffle options and update the answer index.
    final_questions = []
    for q in questions:
        cid, qtext, o1, o2, o3, o4, ans_idx = q
        opts = [o1, o2, o3, o4]
        correct_val = opts[ans_idx - 1]
        random.shuffle(opts)
        new_ans_idx = opts.index(correct_val) + 1
        final_questions.append((cid, qtext, opts[0], opts[1], opts[2], opts[3], new_ans_idx))

    # Insert into DB
    c.executemany("INSERT INTO questions (course_id, question, option1, option2, option3, option4, answer) VALUES (?, ?, ?, ?, ?, ?, ?)", final_questions)
    conn.commit()
    conn.close()

    print(f"Successfully seeded {len(final_questions)} aptitude questions.")

if __name__ == "__main__":
    seed_aptitude_questions()
