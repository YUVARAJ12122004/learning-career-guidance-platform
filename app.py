from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3, os, io, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
from flask import jsonify

from werkzeug.utils import secure_filename
import PyPDF2
import docx
import re
import requests
import time
import urllib.parse

lemmatizer = WordNetLemmatizer()
model = load_model("web course/chatbot_model.h5")

words = pickle.load(open("web course/words.pkl", "rb"))
classes = pickle.load(open("web course/classes.pkl", "rb"))

with open("web course/intents.json", encoding="utf-8") as f:
    intents = json.load(f)

app = Flask(__name__)
app.secret_key = "123"
DB_PATH = "database.db"

# Folder configurations setup for resumes
UPLOAD_FOLDER = 'static/resumes'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""create table if not exists users(
        id integer primary key autoincrement,
        name text,
        email text unique,
        password text,
        education text default '',
        experience text default '',
        skills text default '',
        resume_url text default ''
    )""")
    try:
        c.execute("ALTER TABLE users ADD COLUMN education TEXT DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN experience TEXT DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN skills TEXT DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN resume_url TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    c.execute("""create table if not exists courses(
        id integer primary key autoincrement,
        title text,
        description text,
        pdf_file text,
        category text,
        order_index integer default 0
    )""")
    try:
        c.execute("ALTER TABLE courses ADD COLUMN order_index INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE courses ADD COLUMN pdf_file TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    c.execute("create table if not exists enrollments(id integer primary key autoincrement,user_id integer,course_id integer,completed integer default 0,last_page integer default 1,unique(user_id,course_id))")
    try:
        c.execute("ALTER TABLE enrollments ADD COLUMN last_page INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    c.execute("create table if not exists questions(id integer primary key autoincrement,course_id integer,question text,option1 text,option2 text,option3 text,option4 text,answer integer)")
    c.execute("create table if not exists marks(id integer primary key autoincrement,user_id integer,course_id integer,score integer,created_at text)")
    
    # Create jobs table with education_required
    c.execute("""create table if not exists jobs(
        id integer primary key autoincrement,
        title text,
        company text,
        description text,
        required_skills text,
        education_required text default ''
    )""")
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN education_required TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    aptitude_courses = [
        ("Logical Aptitude", "Develop logical reasoning skills essential for aptitude tests", "", "Aptitude", 0),
        ("Quantitative Aptitude", "Master quantitative and mathematical problem-solving", "", "Aptitude", 1),
        ("Communication Aptitude", "Enhance verbal and communication abilities for assessments", "", "Aptitude", 2)
    ]

def current_user():
    if "user_id" in session:
        conn = db()
        u = conn.execute("select * from users where id=?", (session["user_id"],)).fetchone()
        conn.close()
        return u
    return None

def is_aptitude_completed(user_id):
    conn = db()
    apt_courses = conn.execute("select id from courses where category='Aptitude'").fetchall()
    if not apt_courses:
        conn.close()
        return True
    completed = True
    total_score = 0
    count = 0
    for ac in apt_courses:
        mark = conn.execute("select score from marks where user_id=? and course_id=? order by id desc limit 1", (user_id, ac['id'])).fetchone()
        if mark:
            total_score += mark['score']
            count += 1
        if not mark or mark['score'] < 45:
            completed = False
            break
    common_aptitude_score = total_score / max(count, 1) if count > 0 else 0
    conn.execute("CREATE TABLE IF NOT EXISTS aptitude_scores (user_id INTEGER PRIMARY KEY, common_score REAL)")
    conn.execute("INSERT OR REPLACE INTO aptitude_scores (user_id, common_score) VALUES (?, ?)", (user_id, common_aptitude_score))
    conn.commit()
    conn.close()
    return completed

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(w.lower()) for w in sentence_words]
    return sentence_words

def bow(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [1 if w in sentence_words else 0 for w in words]
    return np.array(bag)

def predict_class(sentence):
    p = bow(sentence, words)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.1
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return [{"intent": classes[r[0]], "probability": str(r[1])} for r in results]

def get_response(ints):
    if len(ints) == 0:
        return "I am not sure how to answer that."
    tag = ints[0]["intent"]
    list_of_intents = intents["intents"]
    for i in list_of_intents:
        if i["tag"] == tag:
            return np.random.choice(i["responses"])
    return "I am not sure how to answer that."

@app.route("/")
def index():
    return render_template("index.html", user=current_user())

@app.route("/student")
def student_index():
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    all_courses_query = conn.execute("select c.*, e.id as enrolled, e.completed from courses c left join enrollments e on e.course_id=c.id and e.user_id=? order by c.order_index ASC", (u["id"],)).fetchall()
    
    all_courses = [dict(row) for row in all_courses_query]
    
    last_marks = {}
    seen_courses = set()
    mark_rows = conn.execute("select course_id, score from marks where user_id=? order by created_at desc", (u["id"],)).fetchall()
    for row in mark_rows:
        cid = row['course_id']
        if cid not in seen_courses:
            last_marks[cid] = row['score']
            seen_courses.add(cid)
    
    for c in all_courses:
        c['last_score'] = last_marks.get(c['id'])
    
    aptitude_courses = [c for c in all_courses if c['category'] == 'Aptitude']
    non_aptitude_courses = [c for c in all_courses if c['category'] != 'Aptitude']

    aptitude_details = []
    all_apt_passed = True
    num_apt_enrolled = 0
    for c in aptitude_courses:
        enrolled = c['enrolled'] is not None
        video_done = enrolled and c['completed'] == 1
        score = c['last_score']
        quiz_done = score is not None
        passed = quiz_done and score >= 45
        if not passed:
            all_apt_passed = False
        status_class = 'completed' if passed else 'in-progress' if enrolled else 'locked'
        status_text = 'Completed' if passed else 'In Progress' if enrolled else 'Start Now'
        aptitude_details.append({
            'title': c['title'],
            'status_class': status_class,
            'status_text': status_text,
            'enrolled': enrolled,
            'id': c['id'],
            'course_id': c['id'],
            'score': score
        })
        if enrolled:
            num_apt_enrolled += 1
    
    aptitude_done = all_apt_passed or is_aptitude_completed(u['id'])  # Fallback to existing function
    aptitude_progress = (num_apt_enrolled / len(aptitude_courses) * 100) if aptitude_courses else 0
    
    # Calculate Recommendations based on Skill Gaps
    # Only if aptitude is completed 
    recommended_courses = []
    if aptitude_done:
        # Fetch Top Jobs for the user to find missing skills
        jobs = conn.execute("SELECT * FROM jobs").fetchall()
        missing_skills_pool = set()
        
        for job_row in jobs:
            job = dict(job_row)
            req_skills_str = job['required_skills'] if job.get('required_skills') else ""
            job_desc = job['description'] if 'description' in job.keys() else ""
            match_pct, missing = analyze_profile_match(u, job_desc, req_skills_str)
            # Consider missing skills from jobs where the user is at least a 40% match
            if match_pct >= 40:
                missing_skills_pool.update(missing)
                
        # Find courses that teach the missing skills
        for course in non_aptitude_courses:
            title_desc = (course['title'] + " " + (course['description'] or "")).lower()
            course_teaches_missing = False
            for ms in missing_skills_pool:
                if ms.lower() in title_desc:
                    course_teaches_missing = True
                    break
            
            if course_teaches_missing:
                recommended_courses.append(course)

    conn.close()
    return render_template("student_index.html", user=u, aptitude_courses=aptitude_courses, non_aptitude_courses=non_aptitude_courses, recommended_courses=recommended_courses, aptitude_done=aptitude_done, aptitude_progress=aptitude_progress, aptitude_details=aptitude_details)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    
    if request.method == "POST":
        education = request.form.get("education", "").strip()
        experience = request.form.get("experience", "").strip()
        projects = request.form.get("projects", "").strip()
        skills = request.form.get("skills", "").strip()
        
        conn = db()
        conn.execute("UPDATE users SET education=?, experience=?, projects=?, skills=? WHERE id=?", 
                     (education, experience, projects, skills, u["id"]))
        conn.commit()
        conn.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))
        
    return render_template("profile.html", user=u)

# Predefined skills list for extraction
TECH_SKILLS = ["python", "java", "c++", "c#", "javascript", "html", "css", "sql", 
               "machine learning", "deep learning", "nlp", "react", "node.js", 
               "flask", "django", "aws", "docker", "kubernetes", "tensorflow", "keras"]

# ── JSearch / RapidAPI Integration ────────────────────────────────────────────
RAPIDAPI_KEY = "a2404cbc81msh22982e8de9b9d1ap16ab41jsn2892848ad52f"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"

# Simple in-memory cache  {cache_key: (timestamp, data)}
_job_cache = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes

def fetch_live_jobs(user_profile):
    """
    Fetch real job listings from JSearch (aggregates LinkedIn, Naukri, Indeed, etc.)
    Uses a broad query combining user's skills, experience, education, and projects.
    """
    if not RAPIDAPI_KEY:
        return []

    if hasattr(user_profile, 'keys'):
        user_profile = dict(user_profile)

    query_parts = []
    
    # Extract skills
    skills_str = user_profile.get('skills', '')
    skill_list = [s.strip() for s in skills_str.split(',') if s.strip()] if skills_str else []
    safe_skills = [s for s in skill_list if re.match(r'^[a-zA-Z][a-zA-Z0-9 ]*$', s.strip())][:3]
    query_parts.extend(safe_skills)
    
    # Extract key terms from other fields (basic keyword extraction)
    for field in ['experience', 'education', 'projects']:
        text = user_profile.get(field, '')
        if text and len(text) > 3:
            # simple extraction: first few words of the field to add context
            words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', text) if w.lower() not in {'and', 'the', 'for', 'with', 'from'}]
            if words:
                query_parts.extend(words[:2])

    # Uniquify and build query
    unique_parts = []
    for p in query_parts:
        if p.lower() not in [u.lower() for u in unique_parts]:
            unique_parts.append(p)
            
    if unique_parts:
        query = " ".join(unique_parts[:5]) + " developer jobs India"
    else:
        query = "software developer jobs India"

    cache_key = query.lower()
    now = time.time()

    # Return cached result if still fresh (30 min)
    if cache_key in _job_cache:
        ts, cached_data = _job_cache[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return cached_data

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    try:
        resp = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers=headers,
            params={
                "query": query,
                "num_pages": "2",
                "page": "1",
                "country": "in",
                "date_posted": "month"
            },
            timeout=12
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])

        results = []
        for job in data[:15]:  # fetch up to 15 live jobs
            job_id = job.get("job_id", "")
            if not job_id:
                continue

            # Derive required skills from qualifications highlighted in the job 
            highlights = job.get("job_highlights", {})
            qual_list = highlights.get("Qualifications", [])
            # Extract keywords from qualifications (first 5 bullet points)
            required_skills_str = ", ".join(qual_list[:4]) if qual_list else ", ".join(safe_skills)

            city = job.get("job_city") or ""
            country = job.get("job_country") or "India"
            location = f"{city}, {country}" if city else country

            results.append({
                "id": job_id,
                "title": job.get("job_title", "N/A"),
                "company": job.get("employer_name", "N/A"),
                "description": (job.get("job_description") or "")[:350].strip() + "...",
                "required_skills": required_skills_str,
                "job_url": job.get("job_apply_link") or job.get("job_google_link") or "#",
                "source": job.get("job_publisher", "Job Board"),
                "location": location
            })

        _job_cache[cache_key] = (now, results)
        print(f"[JSearch] Fetched {len(results)} live jobs for query: '{query}'")
        return results

    except Exception as e:
        print(f"[JSearch] API error: {e}")
        return []

# ─────────────────────────────────────────────────────────────────────────────

@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    u = current_user()
    if not u:
        return redirect(url_for("index"))

    if 'resume' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("profile"))
        
    file = request.files['resume']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for("profile"))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{u['id']}_{int(datetime.datetime.utcnow().timestamp())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text based on file type
        text = ""
        try:
            if filename.endswith(".pdf"):
                reader = PyPDF2.PdfReader(filepath)
                for page in reader.pages:
                    text += page.extract_text() + " "
            elif filename.endswith(".docx"):
                doc = docx.Document(filepath)
                for para in doc.paragraphs:
                    text += para.text + " "
        except Exception as e:
            flash(f"Error reading resume file: {e}", "danger")
            return redirect(url_for("profile"))
            
        # Skill Extraction
        text_lower = text.lower()
        extracted_skills = set()
        for skill in TECH_SKILLS:
            # Using regex to find whole words match
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                extracted_skills.add(skill.title())
                
        # --- NEW EXPERIMENTAL EXTRACTION LOGIC ---
        
        # 1. Education Extraction
        edu_keywords = ['b.tech', 'btech', 'b.e.', 'm.tech', 'mtech', 'bsc', 'msc', 'bca', 'mca', 'bachelor', 'master', 'degree', 'diploma']
        extracted_edu = set()
        for word in edu_keywords:
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                extracted_edu.add(word.title())

        # 2. Section Based Extraction for Experience and Projects
        # A simple heuristic: split the text by newlines and try to find headers
        # Since PDF/DOCX extraction sometimes loses newlines, we'll try a regex approach looking for keywords
        
        experience_sentences = []
        projects_sentences = []
        
        # Split text into rough sentences based on punctuation or newlines
        sentences = re.split(r'(?<=[.!?\n])\s+', text)
        
        for sentence in sentences:
            s_lower = sentence.lower()
            # If the sentence mentions experience keywords, it might describe past work
            if any(k in s_lower for k in ['experience', 'worked as', 'intern', 'internship', 'developer at', 'employed']):
                if len(sentence.split()) > 3 and len(sentence) < 200: # filter out single keywords or massive blocks
                    experience_sentences.append(sentence.strip())
            
            # If the sentence mentions project keywords
            if any(k in s_lower for k in ['project', 'developed a', 'built a', 'created a', 'deployed a']):
                if len(sentence.split()) > 3 and len(sentence) < 200: 
                    projects_sentences.append(sentence.strip())
        
        extracted_edu_str = ", ".join(extracted_edu) if extracted_edu else ""
        extracted_exp_str = "; ".join(experience_sentences[:3]) if experience_sentences else "" # Take top 3
        extracted_proj_str = "; ".join(projects_sentences[:3]) if projects_sentences else ""
        
        # Only use the newly extracted skills
        existing_skills_list = [es for es in extracted_skills]
                
        updated_skills = ", ".join(existing_skills_list)
        resume_url = "/" + filepath.replace("\\", "/")
        
        # Update user's records gracefully merging existing with new
        conn = db()
        curr_edu = u['education'] if u['education'] else ""
        curr_exp = u['experience'] if u['experience'] else ""
        
        try:
            curr_proj = u['projects'] if u['projects'] else ""
        except:
            curr_proj = ""
            
        final_edu = extracted_edu_str if extracted_edu_str else curr_edu
        final_exp = extracted_exp_str if extracted_exp_str else curr_exp
        final_proj = extracted_proj_str if extracted_proj_str else curr_proj
        
        conn.execute("UPDATE users SET skills=?, education=?, experience=?, projects=?, resume_url=? WHERE id=?", 
                     (updated_skills, final_edu, final_exp, final_proj, resume_url, u["id"]))
        conn.commit()
        conn.close()
        
        flash("Resume uploaded and details (Skills, Education, Experience, Projects) successfully extracted!", "success")
        return redirect(url_for("profile"))
        
    flash("Invalid file format. Please upload PDF or DOCX.", "danger")
    return redirect(url_for("profile"))


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name","").strip()
    email = request.form.get("email","").strip().lower()
    password = request.form.get("password","")
    if not name or not email or not password:
        flash("All fields required","danger")
        return redirect(url_for("index"))
    pw = generate_password_hash(password)
    try:
        conn = db()
        conn.execute("insert into users(name,email,password) values(?,?,?)",(name,email,pw))
        conn.commit()
        user = conn.execute("select * from users where email=?", (email,)).fetchone()
        conn.close()
        session["user_id"] = user["id"]
        return redirect(url_for("student_index"))
    except sqlite3.IntegrityError:
        flash("Email already registered","danger")
        return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email","").strip().lower()
    password = request.form.get("password","")
    conn = db()
    user = conn.execute("select * from users where email=?", (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        return redirect(url_for("student_index"))
    flash("Invalid credentials","danger")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin_login", methods=["POST"])
def admin_login():
    username = request.form.get("username","").strip()
    password = request.form.get("password","").strip()
    if username == "admin" and password == "123":
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    flash("Invalid admin credentials","danger")
    return redirect(url_for("index"))

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

@app.route("/admin")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("index"))
    conn = db()
    it = conn.execute("select * from courses where category='IT' order by order_index ASC").fetchall()
    apt = conn.execute("select * from courses where category='Aptitude' order by order_index ASC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", it_courses=it, apt_courses=apt)

@app.route("/admin/course/new", methods=["POST"])
def admin_add_course():
    if not session.get("admin"):
        return redirect(url_for("index"))
    
    title = request.form.get("title","").strip()
    description = request.form.get("description","").strip()
    category = request.form.get("category","IT").strip()
    pdf_file = request.files.get("pdf_file")
    if not title or category not in ("IT","Aptitude"):
        flash("Missing fields or invalid category.","danger")
        return redirect(url_for("admin_dashboard"))

    pdf_url = None
    if pdf_file and pdf_file.filename != "":
        filename = secure_filename(f"{datetime.datetime.utcnow().timestamp()}_{pdf_file.filename}")
        filepath = os.path.join("static", filename)
        pdf_file.save(filepath)
        pdf_url = "/" + filepath.replace("\\","/")
    conn = db()
    max_index = conn.execute("SELECT MAX(order_index) FROM courses WHERE category=?", (category,)).fetchone()[0] or 0
    next_index = max_index + 1

    conn.execute(
        "INSERT INTO courses(title,description,pdf_file,category,order_index) VALUES(?,?,?,?,?)",
        (title, description, pdf_url, category, next_index)
    )
    conn.commit()
    conn.close()
    flash("Course added","success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/course/update", methods=["POST"])
def admin_update_course():
    if not session.get("admin"):
        return redirect(url_for("index"))
    course_id = request.form.get("course_id")
    title = request.form.get("title","").strip()
    description = request.form.get("description","").strip()
    category = request.form.get("category","IT").strip()
    pdf_file = request.files.get("pdf_file")

    if not course_id or not title or category not in ("IT","Aptitude"):
        flash("Missing required fields", "danger")
        return redirect(url_for("admin_dashboard"))

    conn = db()
    original = conn.execute("SELECT category FROM courses WHERE id=?", (course_id,)).fetchone()
    if not original:
        flash("Course not found", "danger")
        conn.close()
        return redirect(url_for("admin_dashboard"))
    
    original_category = original['category']
    if original_category != 'Aptitude' and category == 'Aptitude':
        apt_count = conn.execute("SELECT COUNT(*) FROM courses WHERE category='Aptitude'").fetchone()[0]
        if apt_count >= 3:
            flash("Cannot change category to Aptitude. Maximum of 3 Aptitude courses allowed (Logical, Quantitative, and Communication are predefined).", "danger")
            conn.close()
            return redirect(url_for("admin_dashboard"))

    pdf_url = None
    if pdf_file and pdf_file.filename != "":
        filename = secure_filename(f"{datetime.datetime.utcnow().timestamp()}_{pdf_file.filename}")
        filepath = os.path.join("static", filename)
        pdf_file.save(filepath)
        pdf_url = "/" + filepath.replace("\\","/")

    
    if pdf_url:
        conn.execute("UPDATE courses SET title=?, description=?, category=?, pdf_file=? WHERE id=?",
                     (title, description, category, pdf_url, course_id))
    else:
        conn.execute("UPDATE courses SET title=?, description=?, category=? WHERE id=?",
                     (title, description, category, course_id))
    conn.commit()
    conn.close()
    flash("Course updated successfully", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/course/<int:course_id>/delete", methods=["POST"])
def admin_delete_course(course_id):
    if not session.get("admin"):
        return redirect(url_for("index"))
    conn = db()
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.execute("DELETE FROM questions WHERE course_id=?", (course_id,))
    conn.execute("DELETE FROM enrollments WHERE course_id=?", (course_id,))
    conn.commit()
    conn.close()
    flash("Course deleted", "success")
    return redirect(url_for("admin_dashboard"))

@app.route('/admin/save_course_order', methods=['POST'])
def admin_save_course_order():
    data = request.get_json()
    course_ids = data.get('course_ids', [])
    category = data.get('category')

    conn = db()
    for idx, cid in enumerate(course_ids):
        conn.execute("UPDATE courses SET order_index=? WHERE id=? AND category=?", (idx, cid, category))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Order updated"})

@app.route("/admin/clean_duplicates", methods=["GET", "POST"])
def clean_duplicates():
    if not session.get("admin"):
        flash("Admin access required", "danger")
        return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST": 
        conn = db()
        c = conn.cursor()
        
        
        aptitude_titles = {
            "Logical Aptitude": None,
            "Quantitative Aptitude": None,
            "Communication Aptitude": None
        }
        
       
        apt_courses = c.execute("SELECT id, title FROM courses WHERE category='Aptitude' ORDER BY id ASC").fetchall()
        
        to_keep = set()
        for course in apt_courses:
            title = course['title']
            if title in aptitude_titles and aptitude_titles[title] is None:
                aptitude_titles[title] = course['id']
                to_keep.add(course['id'])
        
        to_delete = [course['id'] for course in apt_courses if course['id'] not in to_keep]
        for cid in to_delete:
            c.execute("DELETE FROM questions WHERE course_id=?", (cid,))
            c.execute("DELETE FROM enrollments WHERE course_id=?", (cid,))
            c.execute("DELETE FROM marks WHERE course_id=?", (cid,))
            c.execute("DELETE FROM courses WHERE id=?", (cid,))
        
       
        for category in ["IT"]:
            cat_courses = c.execute("SELECT id FROM courses WHERE category=? ORDER BY id ASC", (category,)).fetchall()
            if len(cat_courses) > 3:
                extras = [course['id'] for course in cat_courses[3:]]  
                for cid in extras:
                    c.execute("DELETE FROM questions WHERE course_id=?", (cid,))
                    c.execute("DELETE FROM enrollments WHERE course_id=?", (cid,))
                    c.execute("DELETE FROM marks WHERE course_id=?", (cid,))
                    c.execute("DELETE FROM courses WHERE id=?", (cid,))
        
        for category in ["IT", "Aptitude"]:
            cat_courses = c.execute("SELECT id FROM courses WHERE category=? ORDER BY id ASC LIMIT 3", (category,)).fetchall()
            for idx, course in enumerate(cat_courses):
                c.execute("UPDATE courses SET order_index=? WHERE id=?", (idx, course['id']))
        
        conn.commit()
        conn.close()
        conn = db()
        counts = {
            "IT": conn.execute("SELECT COUNT(*) FROM courses WHERE category='IT'").fetchone()[0],
            "Aptitude": conn.execute("SELECT COUNT(*) FROM courses WHERE category='Aptitude'").fetchone()[0]
        }
        conn.close()
        
        flash(f"Cleaning complete! Now balanced: IT={counts['IT']}, Aptitude={counts['Aptitude']} (duplicates removed).", "success")
        return redirect(url_for("admin_dashboard"))
    
    return render_template("confirm_clean.html", message="This will remove all duplicate Aptitude courses")


@app.route("/admin/course/<int:course_id>/questions")
def admin_questions(course_id):
    if not session.get("admin"):
        return redirect(url_for("index"))
    conn = db()
    course = conn.execute("select * from courses where id=?", (course_id,)).fetchone()
    qs = conn.execute("select * from questions where course_id=? order by id", (course_id,)).fetchall()
    conn.close()
    if not course:
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_questions.html", course=course, questions=qs)

@app.route("/admin/course/<int:course_id>/questions", methods=["POST"])
def admin_add_question(course_id):
    if not session.get("admin"):
        return redirect(url_for("index"))
    q = request.form.get("question","").strip()
    o1 = request.form.get("option1","").strip()
    o2 = request.form.get("option2","").strip()
    o3 = request.form.get("option3","").strip()
    o4 = request.form.get("option4","").strip()
    ans = int(request.form.get("answer","1"))
    if not q or not o1 or not o2 or not o3 or not o4 or ans not in (1,2,3,4):
        flash("Invalid question","danger")
        return redirect(url_for("admin_questions", course_id=course_id))
    conn = db()
    conn.execute("insert into questions(course_id,question,option1,option2,option3,option4,answer) values(?,?,?,?,?,?,?)",(course_id,q,o1,o2,o3,o4,ans))
    conn.commit()
    conn.close()
    flash("Question added","success")
    return redirect(url_for("admin_questions", course_id=course_id))

@app.route("/admin/question/<int:question_id>/edit", methods=["POST", "GET"])
def admin_edit_question(question_id):
    if not session.get("admin"):
        return redirect(url_for("index"))
    conn = db()
    q = conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        option1 = request.form.get("option1", "").strip()
        option2 = request.form.get("option2", "").strip()
        option3 = request.form.get("option3", "").strip()
        option4 = request.form.get("option4", "").strip()
        answer = int(request.form.get("answer", 1))
        conn.execute("""UPDATE questions
                        SET question=?, option1=?, option2=?, option3=?, option4=?, answer=?
                        WHERE id=?""",
                     (question, option1, option2, option3, option4, answer, question_id))
        conn.commit()
        conn.close()
        flash("Question updated", "success")
        return redirect(url_for("admin_questions", course_id=q["course_id"]))
    conn.close()
    return render_template("admin_edit_question.html", question=q)

@app.route("/admin/question/<int:question_id>/delete", methods=["POST"])
def admin_delete_question(question_id):
    if not session.get("admin"):
        return redirect(url_for("index"))
    
    conn = db()
    q = conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()
    if q:
        conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
        conn.commit()
        flash("Question deleted", "success")
        course_id = q["course_id"]
    else:
        flash("Question not found", "danger")
        course_id = 0
    conn.close()
    return redirect(url_for("admin_questions", course_id=course_id))


@app.route("/courses/enroll/<int:course_id>", methods=["POST"])
def enroll(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    course = conn.execute("select category from courses where id=?", (course_id,)).fetchone()
    conn.close()
    if course['category'] != 'Aptitude' and not is_aptitude_completed(u['id']):
        flash("Complete all Aptitude modules first to enroll in other courses.", "danger")
        return redirect(url_for("student_index"))
    conn = db()
    try:
        conn.execute("insert into enrollments(user_id,course_id,completed) values(?,?,0)", (u["id"],course_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect(url_for("course_detail", course_id=course_id))

@app.route("/courses/<int:course_id>")
def course_detail(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    c = conn.execute("select * from courses where id=?", (course_id,)).fetchone()
    e = conn.execute("select * from enrollments where user_id=? and course_id=?", (u["id"], course_id)).fetchone()
    conn.close()
    if not c:
        return redirect(url_for("student_index"))
    if c['category'] != 'Aptitude' and not is_aptitude_completed(u['id']):
        flash("Complete all Aptitude modules first.", "danger")
        return redirect(url_for("student_index"))
    return render_template("course_detail.html", user=u, course=c, enrollment=e)

@app.route("/courses/<int:course_id>/complete_course", methods=["POST"])
def complete_course(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    course = conn.execute("select category from courses where id=?", (course_id,)).fetchone()
    conn.close()
    if course['category'] != 'Aptitude' and not is_aptitude_completed(u['id']):
        flash("Complete all Aptitude modules first.", "danger")
        return redirect(url_for("student_index"))
    conn = db()
    conn.execute("update enrollments set completed=1 where user_id=? and course_id=?", (u["id"],course_id))
    conn.commit()
    conn.close()
    flash("Course marked as completed!", "success")
    return redirect(url_for("course_detail", course_id=course_id))

@app.route("/save_pdf_progress", methods=["POST"])
def save_pdf_progress():
    u = current_user()
    if not u:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data = request.get_json()
    course_id = data.get("course_id")
    page_num = data.get("page_num")
    if not course_id or not page_num:
        return jsonify({"success": False, "error": "Missing data"}), 400
    conn = db()
    conn.execute("UPDATE enrollments SET last_page=? WHERE user_id=? AND course_id=?", (page_num, u["id"], course_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/quiz/<int:course_id>")
def quiz(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    e = conn.execute("select * from enrollments where user_id=? and course_id=?", (u["id"],course_id)).fetchone()
    if not e:
        conn.close()
        return redirect(url_for("student_index"))
    qs = conn.execute("select * from questions where course_id=? order by id", (course_id,)).fetchall()
    course = conn.execute("select * from courses where id=?", (course_id,)).fetchone()
    last_mark = conn.execute("select * from marks where user_id=? and course_id=? order by id desc limit 1",(u["id"],course_id)).fetchone()
    
    # Check for separate coding problems
    coding_count = conn.execute("SELECT COUNT(*) FROM coding_problems WHERE course_id=?", (course_id,)).fetchone()[0]
    has_coding = coding_count > 0
    mcq_count = len(qs)
    
    conn.close()
    return render_template("quiz.html", user=u, course=course, questions=qs, last_mark=last_mark,
                           has_coding=has_coding, mcq_count=mcq_count, coding_count=coding_count)

@app.route("/quiz/<int:course_id>/submit", methods=["POST"])
def submit_quiz(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    
    # Ensure mcq_score and coding_score columns exist
    try:
        conn.execute("ALTER TABLE marks ADD COLUMN mcq_score INTEGER DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE marks ADD COLUMN coding_score INTEGER DEFAULT 0")
    except:
        pass
    
    qs = conn.execute("select id, answer, question_type from questions where course_id=? order by id", (course_id,)).fetchall()
    
    mcq_score = 0
    coding_score = 0
    total_score = 0
    
    for q in qs:
        key = f"q_{q['id']}"
        val = request.form.get(key)
        qtype = q['question_type'] if 'question_type' in q.keys() else 'mcq'
        if val and int(val) == q["answer"]:
            total_score += 1
            if qtype == 'coding':
                coding_score += 1
            else:
                mcq_score += 1
    
    conn.execute(
        "INSERT INTO marks(user_id, course_id, score, mcq_score, coding_score, created_at) VALUES(?,?,?,?,?,?)",
        (u["id"], course_id, total_score, mcq_score, coding_score, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return redirect(url_for("certificate", course_id=course_id))

@app.route("/certificate/<int:course_id>")
def certificate(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    course = conn.execute("select * from courses where id=?", (course_id,)).fetchone()
    mark = conn.execute("select * from marks where user_id=? and course_id=? order by id desc limit 1",(u["id"],course_id)).fetchone()
    conn.close()
    if not course or not mark:
        return redirect(url_for("student_index"))
    course = dict(course)
    mark = dict(mark)
    
    # Check if course has coding problems (separate LeetCode-style problems)
    conn2 = db()
    coding_problems_count = conn2.execute("SELECT COUNT(*) FROM coding_problems WHERE course_id=?", (course_id,)).fetchone()[0]
    has_coding = coding_problems_count > 0
    
    coding_solved = 0
    if has_coding:
        coding_solved = conn2.execute(
            "SELECT COUNT(DISTINCT problem_id) FROM coding_submissions WHERE user_id=? AND passed=1 AND problem_id IN (SELECT id FROM coding_problems WHERE course_id=?)",
            (u["id"], course_id)
        ).fetchone()[0]
    
    total_mcq = conn2.execute("SELECT COUNT(*) FROM questions WHERE course_id=?", (course_id,)).fetchone()[0]
    conn2.close()
    
    if has_coding:
        # Two-part pass: MCQ score >= 45 AND >= 3 coding problems solved
        mcq_passed = mark["score"] >= 45
        coding_passed = coding_solved >= 3
        eligible = mcq_passed and coding_passed
    else:
        # Standard pass mark for all courses (Aptitude and IT/Java)
        eligible = mark["score"] >= 45
    
    return render_template("certificate.html", user=u, course=course, mark=mark, eligible=eligible,
                           has_coding=has_coding, mcq_score=mark["score"], coding_score=coding_solved,
                           total_mcq=total_mcq, total_coding=coding_problems_count)

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm

@app.route("/certificate/<int:course_id>/download")
def download_certificate(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))

    conn = db()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    mark = conn.execute(
        "SELECT * FROM marks WHERE user_id=? AND course_id=? ORDER BY id DESC LIMIT 1",
        (u["id"], course_id)
    ).fetchone()
    
    # Check if course has coding problems
    has_coding = conn.execute("SELECT COUNT(*) FROM coding_problems WHERE course_id=?", (course_id,)).fetchone()[0] > 0
    
    coding_solved = 0
    if has_coding:
        coding_solved = conn.execute(
            "SELECT COUNT(DISTINCT problem_id) FROM coding_submissions WHERE user_id=? AND passed=1 AND problem_id IN (SELECT id FROM coding_problems WHERE course_id=?)",
            (u["id"], course_id)
        ).fetchone()[0]
    conn.close()

    if not course or not mark:
        return redirect(url_for("certificate", course_id=course_id))
    
    mark_dict = dict(mark)
    
    if has_coding:
        eligible = mark_dict["score"] >= 45 and coding_solved >= 3
    elif course["category"] == "Aptitude":
        eligible = mark_dict["score"] >= 45
    else:
        eligible = mark_dict["score"] >= 10
    
    if not eligible:
        return redirect(url_for("certificate", course_id=course_id))

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4


    c.setFillColor(HexColor("#fffdf6"))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    
    c.setFont("Helvetica-Bold", 80)
    c.setFillColor(HexColor("#f0e6d6"))
    for y in range(100, int(h), 200):
        for x in range(100, int(w), 200):
            c.drawCentredString(x, y, "★")

    
    margin = 2*cm
    c.setStrokeColor(HexColor("#d4af37"))
    c.setLineWidth(4)
    c.rect(margin, margin, w-2*margin, h-2*margin, stroke=1, fill=0)

    
    for i, color in enumerate(["#ffd700", "#ffc200", "#ffae00"]):
        c.setFillColor(HexColor(color))
        c.roundRect(w/2 - 130, h-150+i*5, 260, 15, 7, fill=1, stroke=0)

    
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(HexColor("#b8860b"))
    c.drawCentredString(w/2 + 2, h-142, "Certificate of Completion")
    c.setFillColor(HexColor("#ffffff"))
    c.drawCentredString(w/2, h-140, "Certificate of Completion")

    
    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(w/2, h-180, "This certifies that")

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(HexColor("#b8860b"))
    c.drawCentredString(w/2, h-220, u["name"])

    
    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(w/2, h-255, "has successfully completed the course")

    c.setFont("Helvetica-BoldOblique", 20)
    c.setFillColor(HexColor("#8b0000"))
    c.drawCentredString(w/2, h-285, course["title"])


    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(w/2, h-320, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")


    c.setLineWidth(1.5)
    c.line(80, 120, w/2-40, 120)
    c.line(w/2+40, 120, w-80, 120)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString((80 + w/2-40)/2, 110, "Instructor")
    c.drawCentredString((w/2+40 + w-80)/2, 110, "Authorized Signature")

    
    c.setStrokeColor(HexColor("#d4af37"))
    c.setLineWidth(2)
    seal_x, seal_y = w-80, h-180
    c.circle(seal_x, seal_y, 40, stroke=1, fill=0)
    for angle in range(0, 360, 36):
        rad = angle * 3.1416 / 180
        x2 = seal_x + 30 * cm * 0.01 * 3 * (0.5**0.5)
        y2 = seal_y
        c.line(seal_x, seal_y, x2, y2)

    c.showPage()
    c.save()
    buf.seek(0)

    return send_file(buf, as_attachment=True, download_name=f"certificate_{course_id}.pdf", mimetype="application/pdf")


def analyze_profile_match(user_dict, job_desc, req_skills_str):
    """
    Compares user's full profile (skills, education, experience, projects) against a job listing.
    Skills = primary factor (70%), Profile keywords = secondary (30%).
    Returns: match_percentage (int), missing_skills (list)
    """
    if not job_desc and not req_skills_str:
        return 100, []
        
    if hasattr(user_dict, 'keys'):
        user_dict = dict(user_dict)
        
    user_skills = {s.strip().lower() for s in user_dict.get('skills', '').split(',')} if user_dict.get('skills') else set()
    req_skills = {s.strip().lower() for s in (req_skills_str or "").split(',')} if req_skills_str else set()
    
    missing_skills = []
    if req_skills:
        matched_skills = user_skills.intersection(req_skills)
        missing_skills = list(req_skills.difference(user_skills))
        skill_score = (len(matched_skills) / len(req_skills)) * 70  # Skills = 70% weight
    else:
        skill_score = 70

    # Profile Keyword Matching in Job Description (30%)
    profile_text = (user_dict.get('education', '') + " " + user_dict.get('experience', '') + " " + user_dict.get('projects', '')).lower()
    profile_words = set(re.findall(r'\b[a-z]{3,}\b', profile_text))
    stop_words = {"and", "the", "for", "with", "from", "this", "that", "have", "has"}
    profile_words = profile_words - stop_words
    
    job_desc_lower = (job_desc or "").lower()
    
    matched_profile_words = 0
    total_important_profile_words = min(len(profile_words), 10)
    
    for word in profile_words:
        if word in job_desc_lower:
            matched_profile_words += 1
            
    if total_important_profile_words > 0:
        profile_score = (min(matched_profile_words, total_important_profile_words) / total_important_profile_words) * 30
    else:
        profile_score = 0
        
    total_match = int(skill_score + profile_score)
    return total_match, missing_skills


# Education eligibility mapping
EDUCATION_LEVELS = {
    'bca': ['entry-level it', 'junior developer', 'web developer', 'software developer', 'it support', 'data entry'],
    'bsc': ['entry-level it', 'junior developer', 'web developer', 'software developer', 'data analyst', 'qa tester'],
    'b.tech': ['software engineer', 'developer', 'data scientist', 'system engineer', 'devops', 'full stack', 'backend', 'frontend', 'core engineer'],
    'btech': ['software engineer', 'developer', 'data scientist', 'system engineer', 'devops', 'full stack', 'backend', 'frontend', 'core engineer'],
    'be': ['software engineer', 'developer', 'data scientist', 'system engineer', 'devops', 'full stack', 'backend', 'frontend', 'core engineer'],
    'mca': ['software engineer', 'developer', 'senior developer', 'technical lead', 'project manager'],
    'msc': ['data scientist', 'research analyst', 'senior developer', 'machine learning engineer'],
    'm.tech': ['senior engineer', 'research scientist', 'architect', 'technical lead', 'machine learning', 'ai engineer'],
    'mtech': ['senior engineer', 'research scientist', 'architect', 'technical lead', 'machine learning', 'ai engineer'],
    'mba': ['project manager', 'product manager', 'business analyst', 'management', 'consultant', 'marketing'],
    'diploma': ['technician', 'junior developer', 'it support', 'data entry', 'web developer'],
    'phd': ['research scientist', 'professor', 'principal engineer', 'ai researcher', 'senior architect'],
}

def check_education_eligibility(user_education, job_title, job_edu_required=''):
    """Check if user's education makes them eligible for a job. Returns True if eligible."""
    if not user_education:
        return True  # If no education info, don't filter out
    
    user_edu_lower = user_education.lower()
    job_title_lower = job_title.lower() if job_title else ''
    job_edu_lower = job_edu_required.lower() if job_edu_required else ''
    
    # If the job itself specifies education requirements, check directly
    if job_edu_lower:
        for edu_key in EDUCATION_LEVELS:
            if edu_key in user_edu_lower:
                if edu_key in job_edu_lower or any(alt in job_edu_lower for alt in [edu_key.replace('.', '')]):
                    return True
        # If job requires specific edu and user doesn't have it, check if higher education covers it
        higher_degrees = ['m.tech', 'mtech', 'mba', 'mca', 'msc', 'phd']
        for hd in higher_degrees:
            if hd in user_edu_lower:
                return True  # Higher degree is always eligible
        # Fallback: allow if no strict match (be lenient)
        return True
    
    # No specific edu requirement on the job; use general eligibility
    for edu_key, eligible_roles in EDUCATION_LEVELS.items():
        if edu_key in user_edu_lower:
            for role_keyword in eligible_roles:
                if role_keyword in job_title_lower:
                    return True
    
    # If no education patterns matched at all, allow (be lenient)
    return True


@app.route("/jobs")
def recommended_jobs():
    u = current_user()
    if not u:
        return redirect(url_for("index"))

    user_education = dict(u).get('education', '') if hasattr(u, 'keys') else ''

    # --- Try to fetch live jobs from JSearch API ---
    live_jobs = fetch_live_jobs(u)

    # Fallback: if live API returned nothing, use local SQLite jobs
    if not live_jobs:
        conn = db()
        db_jobs = conn.execute("SELECT * FROM jobs").fetchall()
        conn.close()
        live_jobs = [dict(j) for j in db_jobs]

    job_recommendations = []
    fetched_at = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

    for job in live_jobs:
        req_skills_str = job.get('required_skills', '') or ''
        job_desc = job.get('description', '')
        job_title = job.get('title', '')
        job_edu_req = job.get('education_required', '') or ''
        
        # Step 1: Education eligibility filter
        if not check_education_eligibility(user_education, job_title, job_edu_req):
            continue  # Skip jobs user is not eligible for
        
        # Step 2: Skills-based match ranking
        match_pct, missing = analyze_profile_match(u, job_desc, req_skills_str)

        if match_pct > 0:
            job_recommendations.append({
                'job': job,
                'match_percentage': match_pct,
                'missing_skills': [s.title() for s in missing],
                'req_skills_list': [s.strip().title() for s in req_skills_str.split(',') if s.strip()],
                'job_url': job.get('job_url') or f"https://www.linkedin.com/jobs/search/?keywords={urllib.parse.quote(job.get('title', ''))}",
                'source': job.get('source', 'Job Board'),
                'location': job.get('location', 'India'),
                'education_required': job_edu_req or 'Any',
            })

    # Sort by highest match percentage (skills = primary factor)
    job_recommendations.sort(key=lambda x: x['match_percentage'], reverse=True)

    return render_template("jobs.html", user=u, recommendations=job_recommendations, fetched_at=fetched_at)


@app.route("/chatbot", methods=["POST"])
def chatbot_response():
    try:
        data = request.get_json()
        message = (data.get("message", "") or "").strip().lower()

        if not message:
            return jsonify({"response": "Please type a message!"})

        # ── 1. Load intents (UTF-8 for emoji support) ─────────────────────────
        with open("web course/intents.json", encoding="utf-8") as f:
            intents_data = json.load(f)

        # ── 2. Smart keyword matching ──────────────────────────────────────────
        import random as _random

        def get_keyword_response(msg, intents_list):
            msg_words = set(re.sub(r"[^\w\s]", "", msg).split())
            best_tag = None
            best_score = 0

            for intent in intents_list:
                tag = intent.get("tag", "")
                if tag == "fallback":
                    continue
                for pattern in intent.get("patterns", []):
                    pat_words = set(re.sub(r"[^\w\s]", "", pattern.lower()).split())
                    if not pat_words:
                        continue
                    # Exact subset match (highest priority)
                    if pat_words.issubset(msg_words):
                        score = len(pat_words)
                        if score > best_score:
                            best_score = score
                            best_tag = tag
                    # Partial overlap match (≥60%)
                    else:
                        overlap = len(msg_words & pat_words)
                        if overlap > 0 and overlap / len(pat_words) >= 0.6:
                            score = overlap
                            if score > best_score:
                                best_score = score
                                best_tag = tag

            if best_tag:
                for intent in intents_list:
                    if intent.get("tag") == best_tag:
                        return _random.choice(intent["responses"])
            return None

        keyword_response = get_keyword_response(message, intents_data["intents"])

        # ── 3. Context-aware personalized responses ───────────────────────────
        u = current_user()
        context_response = None

        if u:
            u_dict = dict(u)
            user_skills = u_dict.get("skills", "") or ""
            user_name = u_dict.get("name", "there")

            # Skills query
            if any(w in message for w in ["my skill", "my skills", "what skill", "i have"]):
                if user_skills:
                    context_response = (
                        f"👤 Based on your profile, **{user_name}**, your current skills are:\n"
                        f"**{user_skills}**\n\n"
                        f"🔍 Visit the **Jobs** page to see how well these match real job listings from LinkedIn and Naukri!"
                    )
                else:
                    context_response = (
                        f"🤔 Hi **{user_name}**! No skills in your profile yet.\n\n"
                        f"📄 **Upload your resume** on the Profile page to auto-extract skills, or add them manually."
                    )

            # Recommendation query
            elif any(w in message for w in ["recommend", "suggest", "what should i", "what course", "best course for me"]):
                if user_skills:
                    skill_list = [s.strip() for s in user_skills.split(",") if s.strip()]
                    top_skills = ", ".join(skill_list[:4]) if skill_list else "general tech skills"
                    context_response = (
                        f"🎯 **Personalized Recommendations for {user_name}:**\n\n"
                        f"Based on your skills ({top_skills}):\n\n"
                        f"1. 📊 Check **Dashboard** → 'Recommended for You' section shows courses for your skill gaps!\n"
                        f"2. 💼 Visit **Jobs** page → Live LinkedIn/Naukri listings with match %\n"
                        f"3. 🎓 Complete gap-closing courses to jump from 60% → 90% job match!"
                    )
                else:
                    context_response = (
                        "📋 **Getting Personalized Recommendations:**\n\n"
                        "1. 📄 Upload your **resume** on the Profile page\n"
                        "2. ✏️ Add your **skills** manually (Python, SQL, etc.)\n"
                        "3. Then I'll give you tailored course & job recommendations!\n\n"
                        "Go to **Profile** to get started! 🚀"
                    )

            # Job query
            elif any(w in message for w in ["job", "jobs", "apply", "vacancy", "opening", "hiring"]):
                if user_skills:
                    context_response = (
                        f"💼 **Jobs for {user_name}:**\n\n"
                        f"Your Skills: **{user_skills[:80]}**\n\n"
                        f"🔗 Go to the **Jobs page** in navbar!\n"
                        f"You'll see live LinkedIn & Naukri openings with:\n"
                        f"✅ Match percentage | ❌ Missing skills | 🔗 Apply Now links\n\n"
                        f"Jobs update every 30 minutes! 🚀"
                    )
                else:
                    context_response = (
                        "💼 Add your skills in **Profile** to get personalized job matches!\n\n"
                        "Then visit the **Jobs** tab to see real LinkedIn & Naukri listings. 🎯"
                    )

        # ── 4. Keras model fallback (probability stored as str, cast to float) ─
        keras_response = None
        try:
            ints = predict_class(message)
            if ints and float(ints[0].get("probability", 0)) > 0.85:
                keras_response = get_response(ints)
        except Exception:
            pass

        # ── 5. Priority: context > keyword > keras > fallback ─────────────────
        final_response = (
            context_response
            or keyword_response
            or keras_response
            or (
                "🤔 I'm not quite sure about that. Try asking:\n\n"
                "• 'career in data science'\n"
                "• 'how to get a certificate'\n"
                "• 'interview tips'\n"
                "• 'my skills'\n"
                "• 'recommend courses for me'"
            )
        )

        return jsonify({"response": final_response})

    except Exception as e:
        print(f"[Chatbot Error] {e}")
        return jsonify({"response": "Sorry, something went wrong. Please try again!"})


# ════════════════════════════════════════════════════════════════════════════
# CODING PROBLEMS (LeetCode-style)
# ════════════════════════════════════════════════════════════════════════════

@app.route("/coding/<int:course_id>/problems")
def coding_problems_list(course_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    problems = conn.execute("SELECT * FROM coding_problems WHERE course_id=? ORDER BY id", (course_id,)).fetchall()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    
    # Get solved problem IDs
    solved = conn.execute(
        "SELECT DISTINCT problem_id FROM coding_submissions WHERE user_id=? AND passed=1",
        (u["id"],)
    ).fetchall()
    solved_ids = [s["problem_id"] for s in solved]
    
    conn.close()
    return render_template("coding_list.html", user=u, course=course, problems=problems, solved_ids=solved_ids)

@app.route("/coding/problem/<int:problem_id>")
def coding_problem(problem_id):
    u = current_user()
    if not u:
        return redirect(url_for("index"))
    conn = db()
    problem = conn.execute("SELECT * FROM coding_problems WHERE id=?", (problem_id,)).fetchone()
    if not problem:
        conn.close()
        return redirect(url_for("student_index"))
    
    all_problems = conn.execute("SELECT id, title, difficulty FROM coding_problems WHERE course_id=? ORDER BY id", (problem["course_id"],)).fetchall()
    
    # Get solved problem IDs
    solved = conn.execute(
        "SELECT DISTINCT problem_id FROM coding_submissions WHERE user_id=? AND passed=1",
        (u["id"],)
    ).fetchall()
    solved_ids = [s["problem_id"] for s in solved]
    
    already_passed = problem_id in solved_ids
    
    conn.close()
    
    import json as json_mod
    examples = json_mod.loads(problem["examples"])
    
    return render_template("coding.html", user=u, problem=problem, examples=examples,
                           all_problems=all_problems, solved_ids=solved_ids, already_passed=already_passed)

@app.route("/run_code", methods=["POST"])
def run_code():
    u = current_user()
    if not u:
        return jsonify({"error": "Not logged in"}), 401
    
    import json as json_mod
    data = request.get_json()
    problem_id = data.get("problem_id")
    code = data.get("code", "")
    
    conn = db()
    problem = conn.execute("SELECT * FROM coding_problems WHERE id=?", (problem_id,)).fetchone()
    conn.close()
    
    if not problem:
        return jsonify({"error": "Problem not found"})
    
    test_cases = json_mod.loads(problem["test_cases"])
    
    # Run only first 3 test cases for "Run" (not full submit)
    test_subset = test_cases[:3]
    results = []
    language = data.get("language", "python")
    
    for tc in test_subset:
        result = execute_code(code, tc["input"], tc["expected"], language)
        results.append(result)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    all_passed = passed == total
    
    return jsonify({
        "results": results,
        "summary": f"{passed}/{total} test cases passed",
        "all_passed": all_passed
    })

@app.route("/submit_code", methods=["POST"])
def submit_code():
    u = current_user()
    if not u:
        return jsonify({"error": "Not logged in"}), 401
    
    import json as json_mod
    data = request.get_json()
    problem_id = data.get("problem_id")
    code = data.get("code", "")
    
    conn = db()
    problem = conn.execute("SELECT * FROM coding_problems WHERE id=?", (problem_id,)).fetchone()
    
    if not problem:
        conn.close()
        return jsonify({"error": "Problem not found"})
    
    test_cases = json_mod.loads(problem["test_cases"])
    results = []
    language = data.get("language", "python")
    
    for tc in test_cases:
        result = execute_code(code, tc["input"], tc["expected"], language)
        results.append(result)
    
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    all_passed = passed_count == total
    
    # Save submission
    conn.execute(
        "INSERT INTO coding_submissions (user_id, problem_id, code, passed, total_tests, passed_tests, created_at) VALUES (?,?,?,?,?,?,?)",
        (u["id"], problem_id, code, 1 if all_passed else 0, total, passed_count, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        "results": results,
        "summary": f"{'✅ Accepted!' if all_passed else '❌ Failed'} — {passed_count}/{total} test cases passed",
        "all_passed": all_passed
    })
def execute_code(code, input_data, expected, language="python"):
    """Execute code in any language using local compilers/runtimes."""
    import json as json_mod
    
    if language == "python":
        return _execute_local_python(code, input_data, expected)
    elif language == "sql":
        return _execute_sql(code, input_data, expected)
    else:
        return _execute_via_piston(code, input_data, expected, language)

def _execute_sql(query, input_data, expected):
    """Execute SQL query in an in-memory SQLite database and compare results."""
    import sqlite3 as sqlite_mod
    try:
        # Use a fresh in-memory database for each test
        conn = sqlite_mod.connect(":memory:")
        conn.row_factory = sqlite_mod.Row
        cursor = conn.cursor()
        
        # 1. Create Mock Schema (Basic tables likely needed for problems)
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, age INTEGER)")
        cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com', 25)")
        cursor.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com', 30)")
        cursor.execute("INSERT INTO users VALUES (3, 'Charlie', 'charlie@example.com', 35)")
        
        cursor.execute("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary INTEGER)")
        cursor.execute("INSERT INTO employees VALUES (101, 'John', 'HR', 50000)")
        cursor.execute("INSERT INTO employees VALUES (102, 'Jane', 'IT', 75000)")
        cursor.execute("INSERT INTO employees VALUES (103, 'Mike', 'IT', 80000)")
        cursor.execute("INSERT INTO employees VALUES (104, 'Sarah', 'Finance', 70000)")
        
        # 2. Execute user query
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 3. Convert rows to list of dicts for comparison
        actual = [dict(r) for r in rows]
        conn.close()
        
        # 4. Compare with expected (expected is usually a list of dicts in test cases)
        # Note: input_data is ignored for SQL but might contain setup SQL in future
        return {"input": "SQL Query", "expected": expected, "actual": actual, "passed": actual == expected}
        
    except Exception as e:
        return {"input": "SQL Query", "expected": expected, "actual": None, "passed": False, "error": str(e)}

def _get_exec_env():
    """Get environment with JDK and MinGW paths prepended."""
    import glob
    env = os.environ.copy()
    extra_paths = []
    # JDK
    jdk_dirs = glob.glob(r"C:\Program Files\Microsoft\jdk-*\bin")
    if jdk_dirs:
        extra_paths.append(jdk_dirs[0])
    # MinGW (MSYS2)
    mingw_bin = r"C:\msys64\mingw64\bin"
    if os.path.isdir(mingw_bin):
        extra_paths.append(mingw_bin)
    if extra_paths:
        env["PATH"] = ";".join(extra_paths) + ";" + env.get("PATH", "")
    return env

def _execute_local_python(code, input_data, expected):
    """Execute Python code locally via subprocess."""
    import json as json_mod
    import subprocess
    import tempfile
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_path = f.name
        
        input_json = json_mod.dumps(input_data)
        
        result = subprocess.run(
            ['python', temp_path],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(temp_path)
        )
        
        try:
            os.unlink(temp_path)
        except:
            pass
        
        if result.returncode != 0:
            lines = result.stderr.strip().split('\n')
            short_error = lines[-1] if lines else result.stderr.strip()
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": short_error}
        
        output = result.stdout.strip()
        try:
            actual = json_mod.loads(output)
        except:
            actual = output
        
        return {"input": input_data, "expected": expected, "actual": actual, "passed": actual == expected}
    
    except subprocess.TimeoutExpired:
        try:
            os.unlink(temp_path)
        except:
            pass
        return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "Time Limit Exceeded (5s)"}
    except Exception as e:
        return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": str(e)}

def _execute_via_piston(code, input_data, expected, language):
    """Execute code locally using available compilers/runtimes."""
    import json as json_mod
    import subprocess
    import tempfile
    import shutil
    
    input_json = json_mod.dumps(input_data)
    env = _get_exec_env()
    exec_path = env.get("PATH", "")
    
    # ─── JavaScript (Node.js) ───
    if language == "javascript":
        if not shutil.which("node", path=exec_path):
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "Node.js is not installed on this system"}
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                # For Windows: replace /dev/stdin with process.stdin reading
                patched_code = code.replace("require('fs').readFileSync('/dev/stdin', 'utf8')", 
                    "require('fs').readFileSync(0, 'utf8')")
                f.write(patched_code)
                temp_path = f.name
            result = subprocess.run(['node', temp_path], input=input_json, capture_output=True, text=True, timeout=5, env=env)
            try: os.unlink(temp_path)
            except: pass
            if result.returncode != 0:
                lines = result.stderr.strip().split('\n')
                return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": lines[-1] if lines else "Runtime Error"}
            output = result.stdout.strip()
            try: actual = json_mod.loads(output)
            except: actual = output
            return {"input": input_data, "expected": expected, "actual": actual, "passed": actual == expected}
        except subprocess.TimeoutExpired:
            try: os.unlink(temp_path)
            except: pass
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "Time Limit Exceeded (5s)"}
        except Exception as e:
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": str(e)}
    
    # ─── Java ───
    if language == "java":
        if not shutil.which("javac", path=exec_path):
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "Java JDK is not installed. Install JDK to use Java, or try Python/JavaScript."}
        try:
            tmpdir = tempfile.mkdtemp()
            java_file = os.path.join(tmpdir, "Main.java")
            with open(java_file, 'w', encoding='utf-8') as f:
                f.write(code)
            # Compile
            comp = subprocess.run(['javac', java_file], capture_output=True, text=True, timeout=10, cwd=tmpdir, env=env)
            if comp.returncode != 0:
                lines = comp.stderr.strip().split('\n')
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": lines[0] if lines else "Compilation Error"}
            # Run
            result = subprocess.run(['java', 'Main'], input=input_json, capture_output=True, text=True, timeout=5, cwd=tmpdir, env=env)
            shutil.rmtree(tmpdir, ignore_errors=True)
            if result.returncode != 0:
                lines = result.stderr.strip().split('\n')
                return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": lines[-1] if lines else "Runtime Error"}
            output = result.stdout.strip()
            try: actual = json_mod.loads(output)
            except: actual = output
            return {"input": input_data, "expected": expected, "actual": actual, "passed": actual == expected}
        except subprocess.TimeoutExpired:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "Time Limit Exceeded"}
        except Exception as e:
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": str(e)}
    
    # ─── C++ ───
    if language == "cpp":
        compiler = shutil.which("g++", path=exec_path) or shutil.which("cl", path=exec_path)
        if not compiler:
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "C++ compiler (g++) is not installed. Install MinGW or MSVC, or try Python/JavaScript."}
        try:
            tmpdir = tempfile.mkdtemp()
            src = os.path.join(tmpdir, "solution.cpp")
            exe = os.path.join(tmpdir, "solution.exe")
            with open(src, 'w', encoding='utf-8') as f:
                f.write(code)
            comp = subprocess.run([compiler, src, '-o', exe, '-std=c++17'], capture_output=True, text=True, timeout=10, cwd=tmpdir, env=env)
            if comp.returncode != 0:
                lines = comp.stderr.strip().split('\n')
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": lines[0] if lines else "Compilation Error"}
            result = subprocess.run([exe], input=input_json, capture_output=True, text=True, timeout=5, cwd=tmpdir, env=env)
            shutil.rmtree(tmpdir, ignore_errors=True)
            if result.returncode != 0:
                lines = result.stderr.strip().split('\n')
                return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": lines[-1] if lines else "Runtime Error"}
            output = result.stdout.strip()
            try: actual = json_mod.loads(output)
            except: actual = output
            return {"input": input_data, "expected": expected, "actual": actual, "passed": actual == expected}
        except subprocess.TimeoutExpired:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "Time Limit Exceeded"}
        except Exception as e:
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": str(e)}
    
    # ─── C ───
    if language == "c":
        compiler = shutil.which("gcc", path=exec_path) or shutil.which("cl", path=exec_path)
        if not compiler:
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "C compiler (gcc) is not installed. Install MinGW or MSVC, or try Python/JavaScript."}
        try:
            tmpdir = tempfile.mkdtemp()
            src = os.path.join(tmpdir, "solution.c")
            exe = os.path.join(tmpdir, "solution.exe")
            with open(src, 'w', encoding='utf-8') as f:
                f.write(code)
            comp = subprocess.run([compiler, src, '-o', exe], capture_output=True, text=True, timeout=10, cwd=tmpdir, env=env)
            if comp.returncode != 0:
                lines = comp.stderr.strip().split('\n')
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": lines[0] if lines else "Compilation Error"}
            result = subprocess.run([exe], input=input_json, capture_output=True, text=True, timeout=5, cwd=tmpdir, env=env)
            shutil.rmtree(tmpdir, ignore_errors=True)
            if result.returncode != 0:
                lines = result.stderr.strip().split('\n')
                return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": lines[-1] if lines else "Runtime Error"}
            output = result.stdout.strip()
            try: actual = json_mod.loads(output)
            except: actual = output
            return {"input": input_data, "expected": expected, "actual": actual, "passed": actual == expected}
        except subprocess.TimeoutExpired:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": "Time Limit Exceeded"}
        except Exception as e:
            return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": str(e)}
    
    return {"input": input_data, "expected": expected, "actual": None, "passed": False, "error": f"Unsupported language: {language}"}


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
