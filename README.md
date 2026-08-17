# 🚀 NextStep – Learning & Career Guidance Platform with AI Chatbot

> An AI-powered learning and career guidance platform designed to help students explore career opportunities, improve their skills, follow structured learning paths, and interact with an intelligent chatbot.

## 📌 About the Project

**NextStep** is a web-based Learning and Career Guidance Platform with an AI chatbot developed to support students in making better learning and career decisions.

The platform provides a centralized environment where users can access learning resources, follow career roadmaps, complete skill assessments, track their learning progress, and interact with an AI chatbot for course and career-related assistance.

The project uses **Natural Language Processing (NLP)** and a **deep learning-based neural network** for chatbot intent classification and response generation.

---

## 🎯 Objectives

* Provide personalized career and learning guidance.
* Help users identify suitable skills and learning paths.
* Provide an interactive AI chatbot for career and course-related queries.
* Allow users to access and complete structured courses.
* Track learning progress and assessment performance.
* Generate certificates after successful course completion.
* Provide administrators with tools to manage courses, videos, and quizzes.
* Improve student employability and career decision-making.

---

## ✨ Key Features

### 👨‍🎓 User Features

* User registration and login
* Personalized learning roadmap
* Course browsing and enrollment
* Aptitude learning modules
* Video-based learning
* Assignment and quiz assessments
* Learning progress tracking
* Automatic certificate generation
* AI chatbot assistance
* Career and skill guidance

### 🤖 AI Chatbot

The chatbot allows users to ask questions related to:

* Career guidance
* Resume help
* Skill recommendations
* Course guidance
* Interview preparation
* Learning-related queries

The chatbot processes user input using **NLP preprocessing, tokenization, lemmatization, Bag of Words feature extraction, and a neural network-based intent classifier**.

### 🛠️ Admin Features

* Admin authentication
* Course management
* Add/update/delete courses
* Manage course videos
* Manage quizzes and assessments
* Organize courses by categories
* Maintain learning content

---

## 🧠 AI Chatbot Architecture

The chatbot follows this general pipeline:

```text
User Query
    ↓
Text Preprocessing
    ↓
Tokenization
    ↓
Lemmatization
    ↓
Bag of Words
    ↓
Neural Network
    ↓
Intent Classification
    ↓
Response Generation
    ↓
Chatbot Response
```

The neural network uses:

```text
Input Layer
     ↓
Dense Layer - 128 neurons
     ↓
Dropout - 50%
     ↓
Dense Layer - 64 neurons
     ↓
Dropout - 50%
     ↓
Output Layer - Softmax
```

The model is trained using TensorFlow/Keras with categorical cross-entropy and SGD optimization.

---

## 🛠️ Tech Stack

### Backend & AI

* Python 3.10
* Flask
* TensorFlow
* Keras
* NLTK
* NumPy
* Pickle

### Frontend

* HTML5
* CSS3
* JavaScript (ES6+)
* CodeMirror
* Split.js

### Database

* SQLite3

### Other Technologies

* JSON
* ReportLab
* PyPDF2
* python-docx

The technology stack and system components are documented in the project report.

---

## 📂 Project Structure

```text
NextStep/
│
├── app.py
├── intents.json
├── chatbot.py
├── train.py
│
├── models/
│   └── chatbot_model.h5
│
├── data/
│   ├── words.pkl
│   └── classes.pkl
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── courses.html
│   └── chatbot.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── database/
│   └── database.db
│
├── requirements.txt
└── README.md
```

> **Note:** Update the structure above to exactly match your actual GitHub project folders/files before pushing.

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/NextStep.git
```

### 2. Navigate to the Project

```bash
cd NextStep
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Download NLTK Resources

```python
import nltk

nltk.download("punkt")
nltk.download("wordnet")
nltk.download("omw-1.4")
nltk.download("punkt_tab")
```

These NLTK resources are used for tokenization and lemmatization in the chatbot preprocessing pipeline.

### 7. Train the Chatbot

If the trained model is not included in the repository:

```bash
python train.py
```

The training process creates the chatbot model using the prepared intent dataset.

### 8. Run the Application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

---

## 📊 Chatbot Dataset

The chatbot uses an `intents.json` dataset containing:

* User query patterns
* Intent tags
* Predefined responses

Example intent categories include:

```text
resume_help
career_advice
course_guidance
skill_recommendation
```

The dataset is converted into training data using tokenization, lemmatization, and Bag of Words representation.

---

## 📈 Results

During testing, the chatbot achieved:

* **90%+ intent classification accuracy**
* **1–2 seconds response time**
* **85%+ positive user feedback**

The chatbot was tested with common career-related queries such as resume help, skill recommendations, course guidance, and general career advice.

---

## 🔐 System Modules

```text
                 NEXTSTEP
                    │
        ┌───────────┼───────────┐
        │           │           │
      User        Admin       Chatbot
      Module      Module       Module
        │           │           │
        ↓           ↓           ↓
   Learning      Course      NLP + AI
   Roadmap       Management   Processing
        │           │           │
        ↓           ↓           ↓
   Assessment     Quiz       Intent
        │         Management Classification
        ↓                       │
   Certificate                  ↓
                          Response
```

The architecture includes user interface, chatbot/NLP, user profile and skill management, skill-gap analysis, recommendation, feedback, and database components.

---

## 🧪 Testing

The project includes testing for:

* User registration and login
* Profile completion
* Job/career recommendations
* Resume upload
* Admin functionality
* Invalid login attempts
* Incomplete profile submission
* Unsupported file uploads
* Concurrent users
* Search edge cases
* Database integration
* Web interface functionality

---

## 🔮 Future Enhancements

Future improvements planned for NextStep include:

* AI-powered career recommendations
* Integration with live job-market data
* Interactive mentor-student system
* Gamification with badges and leaderboards
* Mobile application
* Advanced analytics and reporting
* Real-time industry skill trends

These enhancements are identified in the project report's future scope.

---

## 👨‍💻 Team

### Yuvaraj S

**B.Tech – Information Technology**

### Abishek Raj S V

### Pugazhendhi V

**Panimalar Engineering College, Chennai**

---

## 🎓 Academic Project

This project was developed as part of the **Bachelor of Technology in Information Technology** program at **Panimalar Engineering College**.

---

## 📜 License

This project is developed for academic and educational purposes.

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

---

**NextStep – Learn Better. Choose Better. Grow Better. 🚀**
