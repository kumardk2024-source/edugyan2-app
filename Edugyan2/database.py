
import sqlite3
import random

# NCERT Database (Class 6-12 subjects and sample questions for quizzes)
NCERT_DATABASE = {
    "Indian History": [
        {"question": "Harappan civilization belonged to which age?", "options": ["Bronze Age", "Iron Age", "Stone Age", "Copper Age"], "correct": 0},
        {"question": "Who was the founder of the Maurya Empire?", "options": ["Ashoka", "Chandragupta Maurya", "Bindusara", "Samudragupta"], "correct": 1},
        {"question": "The Battle of Plassey was fought in which year?", "options": ["1757", "1764", "1857", "1761"], "correct": 0}
    ],
    "Physics": [
        {"question": "What is the SI unit of force?", "options": ["Joule", "Newton", "Watt", "Pascal"], "correct": 1},
        {"question": "Light year is a unit of?", "options": ["Time", "Distance", "Speed", "Intensity of light"], "correct": 1},
        {"question": "Who propounded the theory of relativity?", "options": ["Isaac Newton", "Albert Einstein", "Galileo Galilei", "Niels Bohr"], "correct": 1}
    ],
    "Geography": [
        {"question": "Which is the longest river in the world?", "options": ["Amazon", "Nile", "Yangtze", "Mississippi"], "correct": 1},
        {"question": "Which planet is known as the Red Planet?", "options": ["Venus", "Mars", "Jupiter", "Saturn"], "correct": 1},
        {"question": "The Suez Canal connects which two seas?", "options": ["Mediterranean and Red Sea", "Pacific and Atlantic", "Arabian Sea and Bay of Bengal", "Baltic and North Sea"], "correct": 0}
    ]
}

def init_db():
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    # users टेबल
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            mobile TEXT,
            district TEXT,
            state TEXT,
            country TEXT,
            is_verified INTEGER DEFAULT 0,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # quizzes टेबल
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            question TEXT,
            options TEXT,
            correct INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def check_user_exists(user_id):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, is_verified FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row  # Returns (user_id, is_verified) or None

def register_user_details(user_id, name, mobile, district, state, country):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, full_name, mobile, district, state, country, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (user_id, name, mobile, district, state, country))
    conn.commit()
    conn.close()

def save_question(user_id, title, question, options, correct=0):
    import json
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    options_json = json.dumps(options)
    cursor.execute('''
        INSERT INTO quizzes (user_id, title, question, options, correct)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, question, options_json, correct))
    conn.commit()
    conn.close()

def get_user_quiz(user_id):
    import json
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT question, options, correct FROM quizzes WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    questions_list = []
    for row in rows:
        questions_list.append({
            "question": row[0],
            "options": json.loads(row[1]),
            "correct": row[2]
        })
    return questions_list

def get_random_ncert_questions(subject_name, num_q):
    sub_questions = NCERT_DATABASE.get(subject_name, [])
    if not sub_questions:
        return []
    # अगर डेटाबेस में कम सवाल हैं तो उन्हें रिपीट करके संख्या पूरी कर लें, वरना रैंडम चुन लें
    selected = []
    while len(selected) < num_q:
        selected.extend(random.sample(sub_questions, min(len(sub_questions), num_q - len(selected))))
    return selected