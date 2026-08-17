import sqlite3

def seed_jobs():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Ensure education_required column exists
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN education_required TEXT DEFAULT ''")
    except:
        pass
    
    # Check if jobs already exist
    c.execute("SELECT count(*) FROM jobs")
    count = c.fetchone()[0]
    
    if count == 0:
        print("Seeding sample jobs into the database...")
        # (title, company, description, required_skills, education_required)
        sample_jobs = [
            ("Python Backend Developer", "TechCorp Inc.", "We are looking for an experienced Python developer to build robust APIs.", "Python, Flask, SQL, Docker", "B.Tech, BCA, MCA"),
            ("Data Scientist", "DataViz Solutions", "Analyze large datasets and build predictive models using machine learning.", "Python, SQL, Machine Learning, TensorFlow", "B.Tech, M.Tech, MSc"),
            ("Frontend React Engineer", "WebTech Agency", "Create stunning user interfaces for our clients using modern web technologies.", "JavaScript, React, HTML, CSS", "BCA, B.Tech, Diploma"),
            ("Full Stack Developer", "StartupX", "Join our fast-paced startup to work on both frontend and backend systems.", "JavaScript, React, Node.js, SQL, AWS", "B.Tech, BCA, MCA"),
            ("AI Engineer", "NextGen AI", "Develop and deploy deep learning models for natural language processing.", "Python, Deep Learning, NLP, TensorFlow, Keras", "B.Tech, M.Tech"),
            ("Java Software Engineer", "Enterprise Solutions Ltd.", "Maintain and develop enterprise-level Java applications.", "Java, SQL, AWS", "B.Tech, BE, MCA"),
            ("Cloud Architect", "CloudScale", "Design and deploy scalable cloud infrastructure using AWS and Kubernetes.", "AWS, Docker, Kubernetes, Linux", "B.Tech, M.Tech"),
            ("Database Administrator", "DataGuard", "Manage and optimize large-scale SQL databases for our core products.", "SQL, Database Design, Optimization", "BCA, B.Tech, MCA"),
            ("Web Developer", "DigitalWEB", "Build responsive websites and web applications for small businesses.", "HTML, CSS, JavaScript, Flask", "BCA, Diploma, BSc"),
            ("Project Manager", "ManageIT", "Lead cross-functional teams and manage software delivery projects.", "Leadership, Agile, Communication", "MBA, M.Tech"),
        ]
        
        c.executemany("INSERT INTO jobs (title, company, description, required_skills, education_required) VALUES (?, ?, ?, ?, ?)", sample_jobs)
        conn.commit()
        print(f"Successfully seeded {len(sample_jobs)} sample jobs with education requirements.")
    else:
        print(f"Database already contains {count} jobs. Skipping seed.")
        
    conn.close()

if __name__ == "__main__":
    seed_jobs()
