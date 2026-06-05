#!/usr/bin/env python3
"""Flask app - AI Bias Detection in Hiring"""

from flask import Flask, request, jsonify, render_template, Response
import os
import re
import logging
import csv
import io
import sqlite3
import json
import PyPDF2
from collections import defaultdict
import time
from werkzeug.utils import secure_filename

# Gemini LLM
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        LLM_AVAILABLE = True
    else:
        LLM_AVAILABLE = False
except Exception:
    LLM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/uploads' if os.environ.get('VERCEL') else 'uploads'
DB_PATH = '/tmp/bias_hiring.db' if os.environ.get('VERCEL') else 'bias_hiring.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
MAX_UPLOAD_FILES = 20

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_role TEXT,
                total_files INTEGER,
                successful INTEGER,
                average_match REAL,
                bias_detected INTEGER,
                bias_level TEXT,
                severity_score INTEGER,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                filename TEXT,
                match_percentage REAL,
                matching_skills TEXT,
                missing_skills TEXT,
                recommendation TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            );
            CREATE TABLE IF NOT EXISTS bias_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                category TEXT,
                words TEXT,
                severity INTEGER,
                timestamp TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            );
        ''')

init_db()

# ── Job Roles ─────────────────────────────────────────────────────────────────

job_roles = {
    "software_engineer": {
        "title": "Software Engineer",
        "description": "We are looking for a strong, ambitious developer to join our team. The ideal candidate should be a rockstar programmer with competitive spirit and aggressive problem-solving skills.",
        "required_skills": ["python", "java", "javascript", "software development", "problem solving", "git", "algorithms", "data structures"]
    },
    "senior_software_engineer": {
        "title": "Senior Software Engineer",
        "description": "Seeking a seasoned software engineer with mature leadership skills. The candidate should be experienced in mentoring young developers and have strong technical expertise.",
        "required_skills": ["python", "java", "javascript", "system design", "leadership", "mentoring", "architecture", "code review"]
    },
    "data_scientist": {
        "title": "Data Scientist",
        "description": "Seeking a Data Scientist to analyze complex datasets. The candidate should be energetic and have fresh perspectives on machine learning and statistical analysis.",
        "required_skills": ["python", "machine learning", "data analysis", "statistics", "sql", "data visualization", "pandas", "numpy"]
    },
    "ml_engineer": {
        "title": "Machine Learning Engineer",
        "description": "Looking for an ML Engineer to build and deploy machine learning models. The ideal candidate should be a guru in deep learning and AI technologies.",
        "required_skills": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "mlops", "docker", "kubernetes"]
    },
    "frontend_developer": {
        "title": "Frontend Developer",
        "description": "Looking for a Frontend Developer with expertise in modern frameworks. The candidate should be a ninja with JavaScript and have strong design skills.",
        "required_skills": ["javascript", "html", "css", "react", "angular", "responsive design", "ui/ux"]
    },
    "backend_developer": {
        "title": "Backend Developer",
        "description": "We need a Backend Developer to build robust server-side applications. The ideal candidate should be experienced and mature in handling complex systems.",
        "required_skills": ["python", "java", "node", "express", "sql", "nosql", "api development", "microservices"]
    },
    "full_stack_developer": {
        "title": "Full Stack Developer",
        "description": "Seeking a versatile full-stack developer who can handle both frontend and backend. The candidate should be aggressive in learning new technologies.",
        "required_skills": ["javascript", "html", "css", "python", "node", "react", "sql", "git", "api development"]
    },
    "devops_engineer": {
        "title": "DevOps Engineer",
        "description": "Looking for a DevOps Engineer to streamline our development processes. The ideal candidate should be a rockstar in automation and cloud technologies.",
        "required_skills": ["docker", "kubernetes", "aws", "ci/cd", "linux", "automation", "terraform", "monitoring"]
    },
    "cloud_architect": {
        "title": "Cloud Architect",
        "description": "We need a Cloud Architect to design our cloud infrastructure. The candidate should be experienced and have strong knowledge of cloud platforms.",
        "required_skills": ["aws", "azure", "gcp", "terraform", "cloud security", "microservices", "system design", "cost optimization"]
    },
    "product_manager": {
        "title": "Product Manager",
        "description": "Seeking a Product Manager to lead our product development. The ideal candidate should be aggressive in market research and competitive in strategy.",
        "required_skills": ["product management", "agile", "user stories", "market research", "roadmapping", "stakeholder management"]
    }
}

# ── Bias Keywords ─────────────────────────────────────────────────────────────

BIAS_KEYWORDS = {
    "gender": {
        "words": {
            "aggressive": 3, "dominant": 3, "assertive": 2, "competitive": 2,
            "strong": 1, "ambitious": 1, "driven": 1, "fearless": 2,
            "nurturing": 2, "supportive": 1, "collaborative": 1, "empathetic": 1,
            "guys": 3, "manpower": 3, "mankind": 2, "chairman": 2,
            "rockstar": 2, "ninja": 2, "hero": 2, "warrior": 2
        },
        "neutral_alternatives": {
            "aggressive": "goal-oriented", "dominant": "influential",
            "rockstar": "high-performing", "ninja": "expert",
            "guys": "team", "manpower": "workforce"
        }
    },
    "age": {
        "words": {
            "young": 3, "energetic": 2, "fresh": 2, "recent graduate": 3,
            "digital native": 3, "youthful": 3, "dynamic": 1,
            "mature": 2, "seasoned": 2, "veteran": 1, "experienced": 1,
            "old-school": 3, "traditional": 1, "established": 1
        },
        "neutral_alternatives": {
            "young": "skilled", "energetic": "motivated",
            "fresh": "innovative", "recent graduate": "entry-level candidate",
            "digital native": "tech-savvy", "mature": "accomplished"
        }
    },
    "personality": {
        "words": {
            "guru": 2, "wizard": 2, "genius": 2, "superstar": 2,
            "fast-paced": 2, "hustle": 3, "grind": 3, "intensity": 2,
            "cultural fit": 2, "culture fit": 2, "beer test": 3,
            "work hard play hard": 2, "passionate": 1, "obsessed": 2
        },
        "neutral_alternatives": {
            "guru": "subject matter expert", "wizard": "specialist",
            "hustle": "high-impact work", "cultural fit": "values alignment",
            "obsessed": "deeply focused"
        }
    },
    "exclusionary": {
        "words": {
            "native speaker": 3, "fluent english": 2, "perfect english": 3,
            "ivy league": 3, "top university": 2, "elite school": 3,
            "physically fit": 3, "able-bodied": 3, "no disabilities": 3,
            "clean background": 2, "all american": 3
        },
        "neutral_alternatives": {
            "native speaker": "strong communication skills",
            "ivy league": "accredited university",
            "physically fit": "able to perform job duties"
        }
    }
}

LABELED_TEST_DATA = [
    ("We need a strong aggressive rockstar programmer with competitive spirit", True),
    ("Looking for a young energetic digital native recent graduate", True),
    ("Seeking a ninja guru wizard who is dominant and assertive", True),
    ("Must be a cultural fit who works hard plays hard in our hustle culture", True),
    ("Ivy league degree required native english speaker only", True),
    ("We need a skilled developer with problem-solving abilities", False),
    ("Looking for a qualified engineer with technical expertise", False),
    ("Seeking a proficient candidate with relevant experience", False),
    ("We want a talented professional with good communication skills", False),
    ("Join our team as a dedicated software engineer", False),
    ("The candidate should be experienced mature and seasoned", True),
    ("Looking for a passionate obsessed fast-paced team member", True),
    ("Collaborative team player with proven track record", False),
    ("Energetic fresh perspective dynamic young professional", True),
    ("Results-driven professional with strong analytical skills", False),
]

# ── LLM Functions ─────────────────────────────────────────────────────────────

def get_llm_bias_explanation(job_description, bias_details):
    """Use Gemini to explain bias and rewrite the job description"""
    if not LLM_AVAILABLE:
        return None

    biased_words = []
    for b in bias_details:
        biased_words.extend(b['words'])

    prompt = f"""You are an expert in inclusive hiring practices and diversity & inclusion.

A job description has been flagged for containing biased language. Your task:

1. Briefly explain WHY each biased word/phrase is problematic (2-3 sentences total)
2. Rewrite the ENTIRE job description using inclusive, neutral language

ORIGINAL JOB DESCRIPTION:
{job_description}

FLAGGED BIASED WORDS: {', '.join(biased_words)}

Respond in this exact JSON format:
{{
  "explanation": "Brief explanation of why these words create bias and who they might exclude...",
  "rewritten_jd": "The full rewritten job description using inclusive language..."
}}

Keep the rewritten JD professional and retain all the technical requirements."""

    try:
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        # Clean markdown code blocks if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        result = json.loads(text)
        return result
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return None


def get_llm_candidate_feedback(resume_skills, missing_skills, job_title):
    """Use Gemini to give personalized candidate improvement feedback"""
    if not LLM_AVAILABLE or not missing_skills:
        return None

    prompt = f"""You are a career coach helping a candidate improve their profile for a {job_title} role.

The candidate HAS these skills: {', '.join(resume_skills) if resume_skills else 'Not specified'}
The candidate is MISSING these skills: {', '.join(missing_skills)}

Give 3 specific, actionable recommendations to help them close the skill gap.
Be concise and practical. Format as a JSON array:
[
  "Recommendation 1...",
  "Recommendation 2...",
  "Recommendation 3..."
]"""

    try:
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        logger.error("Gemini candidate feedback error: %s", e)
        return None

# ── Core Functions ────────────────────────────────────────────────────────────

def analyze_job_description_bias(text):
    text_lower = text.lower()
    bias_report = defaultdict(list)
    severity_total = 0
    for category, data in BIAS_KEYWORDS.items():
        for keyword, severity in data['words'].items():
            if keyword in text_lower:
                pattern = r'(?<!\bnot\s)(?<!\bavoid\s)' + re.escape(keyword)
                if re.search(pattern, text_lower):
                    bias_report[category].append({
                        'word': keyword,
                        'severity': severity,
                        'suggestion': data['neutral_alternatives'].get(keyword, 'Use neutral language')
                    })
                    severity_total += severity
    return bias_report, severity_total


def get_bias_level(severity_score):
    if severity_score == 0:
        return 'none', '#28a745'
    if severity_score <= 3:
        return 'low', '#ffc107'
    if severity_score <= 7:
        return 'medium', '#fd7e14'
    return 'high', '#dc3545'


def extract_text_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_err:
                    logger.warning("Failed to extract page: %s", page_err)
            if not text.strip():
                return "Error: Could not extract text from PDF."
            return text
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        return f"Error extracting PDF: {str(e)}"


def anonymize_resume(text):
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    text = re.sub(r'(\+?\d[\d\s\-().]{7,}\d)', '[PHONE]', text)
    text = re.sub(r'\b(Male|Female|He|She|Him|Her|His|Hers|he/him|she/her|they/them)\b', '[PRONOUN]', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Mr\.|Mrs\.|Ms\.|Miss|Dr\.)\s+\w+', '[NAME]', text)
    text = re.sub(r'\b(linkedin\.com/in/|github\.com/)\S+', '[PROFILE_URL]', text, flags=re.IGNORECASE)
    return text


def extract_skills_from_text(text):
    common_skills = [
        "python", "java", "javascript", "typescript", "html", "css", "sql", "nosql",
        "mongodb", "postgresql", "mysql", "react", "angular", "vue", "node", "express",
        "django", "flask", "fastapi", "spring", "machine learning", "deep learning",
        "data analysis", "data science", "artificial intelligence", "nlp",
        "git", "github", "docker", "kubernetes", "aws", "azure", "gcp", "linux",
        "ci/cd", "devops", "terraform", "ansible", "jenkins",
        "project management", "agile", "scrum", "kanban", "jira",
        "leadership", "teamwork", "communication", "problem solving",
        "algorithms", "data structures", "system design", "microservices",
        "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "keras",
        "tableau", "power bi", "excel", "r", "scala", "go", "rust", "c++", "c#",
        "rest api", "graphql", "redis", "elasticsearch", "spark", "hadoop",
        "blockchain", "cybersecurity", "networking", "cloud computing"
    ]
    text_lower = text.lower()
    return [skill for skill in common_skills if skill in text_lower]


def calculate_job_match(resume_skills, job_skills):
    if not job_skills:
        return {"match_percentage": 0, "matching_skills": [], "missing_skills": []}
    matching = list(set(resume_skills) & set(job_skills))
    base_pct = round((len(matching) / len(job_skills)) * 100, 2)
    extra = len(set(resume_skills) - set(job_skills))
    bonus = min(extra * 0.5, 5.0)
    match_percentage = min(round(base_pct + bonus, 2), 100.0)
    return {
        "match_percentage": match_percentage,
        "matching_skills": matching,
        "missing_skills": list(set(job_skills) - set(resume_skills))
    }


def build_recommendation(match_percentage):
    if match_percentage >= 80:
        return "Strong match — highly recommended for interview."
    if match_percentage >= 60:
        return "Good match — recommend for interview with minor skill gaps."
    if match_percentage >= 40:
        return "Partial match — consider if candidate shows strong growth potential."
    return "Low match — significant skill gaps identified."


def process_single_resume(file_path, filename, job_data):
    try:
        resume_text = extract_text_from_pdf(file_path)
        if resume_text.startswith("Error"):
            return {'filename': filename, 'error': resume_text, 'status': 'failed'}

        anonymized_resume = anonymize_resume(resume_text)
        resume_skills = extract_skills_from_text(resume_text)
        match_result = calculate_job_match(resume_skills, job_data['required_skills'])
        match_percentage = match_result['match_percentage']

        # LLM candidate feedback
        llm_feedback = get_llm_candidate_feedback(
            resume_skills,
            match_result['missing_skills'],
            job_data['title']
        )

        return {
            'filename': filename,
            'status': 'success',
            'match_percentage': match_percentage,
            'matching_skills': match_result['matching_skills'],
            'missing_skills': match_result['missing_skills'],
            'recommendation': build_recommendation(match_percentage),
            'llm_feedback': llm_feedback,
            'anonymized_resume': anonymized_resume[:600] + '...' if len(anonymized_resume) > 600 else anonymized_resume
        }
    except Exception as e:
        logger.error("Error processing resume %s: %s", filename, e)
        return {'filename': filename, 'error': str(e), 'status': 'failed'}
    finally:
        try:
            os.remove(file_path)
        except OSError as e:
            logger.warning("Could not delete temp file %s: %s", file_path, e)


def generate_confusion_matrix():
    preds = []
    for description, actual_label in LABELED_TEST_DATA:
        bias_report, severity = analyze_job_description_bias(description)
        predicted = severity > 0
        preds.append({'description': description, 'predicted': predicted, 'actual': actual_label})

    tp = sum(1 for p in preds if p['predicted'] and p['actual'])
    tn = sum(1 for p in preds if not p['predicted'] and not p['actual'])
    fp = sum(1 for p in preds if p['predicted'] and not p['actual'])
    fn = sum(1 for p in preds if not p['predicted'] and p['actual'])
    total = len(preds)

    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'matrix': {'true_positive': tp, 'true_negative': tn, 'false_positive': fp, 'false_negative': fn},
        'metrics': {
            'accuracy': round(accuracy, 3),
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1, 3)
        },
        'results': [{
            'description': p['description'],
            'predicted': 'Biased' if p['predicted'] else 'Clean',
            'actual': 'Biased' if p['actual'] else 'Clean',
            'status': 'correct' if p['predicted'] == p['actual'] else 'incorrect'
        } for p in preds]
    }


def save_uploaded_files(pdf_files):
    saved = []
    for i, (file, filename) in enumerate(pdf_files):
        safe_name = secure_filename(filename) or "resume.pdf"
        dest = os.path.join(app.config['UPLOAD_FOLDER'], f"resume_{int(time.time())}_{i}_{safe_name}")
        file.save(dest)
        saved.append((dest, filename))
        time.sleep(0.01)
    return saved


def build_bias_details(bias_report, severity_total):
    details = []
    bias_detected = False
    for category, items in bias_report.items():
        if items:
            bias_detected = True
            details.append({
                'category': category.replace('_', ' ').title(),
                'words': [i['word'] for i in items],
                'suggestions': {i['word']: i['suggestion'] for i in items},
                'severity': sum(i['severity'] for i in items)
            })
    bias_level, bias_color = get_bias_level(severity_total)
    return bias_detected, details, bias_level, bias_color


def build_summary(pdf_files, results):
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    return {
        'total_files': len(pdf_files),
        'successful': len(successful),
        'failed': len(failed),
        'average_match': round(sum(r['match_percentage'] for r in successful) / len(successful), 2) if successful else 0,
        'top_candidates': sorted(successful, key=lambda x: x['match_percentage'], reverse=True)[:5]
    }


def save_to_db(job_data, results, summary, bias_detected, bias_details, bias_level, severity_total):
    """Save session and results to SQLite"""
    try:
        with get_db() as conn:
            cur = conn.execute(
                '''INSERT INTO sessions (job_role, total_files, successful, average_match,
                   bias_detected, bias_level, severity_score, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (job_data['title'], summary['total_files'], summary['successful'],
                 summary['average_match'], int(bias_detected), bias_level,
                 severity_total, time.strftime('%Y-%m-%d %H:%M:%S'))
            )
            session_id = cur.lastrowid

            for r in results:
                if r['status'] == 'success':
                    conn.execute(
                        '''INSERT INTO candidates (session_id, filename, match_percentage,
                           matching_skills, missing_skills, recommendation)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        (session_id, r['filename'], r['match_percentage'],
                         json.dumps(r['matching_skills']), json.dumps(r['missing_skills']),
                         r['recommendation'])
                    )

            for b in bias_details:
                conn.execute(
                    '''INSERT INTO bias_events (session_id, category, words, severity, timestamp)
                       VALUES (?, ?, ?, ?, ?)''',
                    (session_id, b['category'], json.dumps(b['words']),
                     b['severity'], time.strftime('%Y-%m-%d %H:%M:%S'))
                )
    except Exception as e:
        logger.error("DB save error: %s", e)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', job_roles=job_roles, llm_available=LLM_AVAILABLE)


@app.route('/confusion-matrix')
def confusion_matrix():
    return render_template('confusion_matrix.html', matrix_data=generate_confusion_matrix())


@app.route('/check-bias-realtime', methods=['POST'])
def check_bias_realtime():
    data = request.get_json()
    text = data.get('text', '') if data else ''
    bias_report, severity = analyze_job_description_bias(text)
    bias_words = [item['word'] for items in bias_report.values() for item in items]
    bias_level, bias_color = get_bias_level(severity)
    return jsonify({
        'bias_detected': bool(bias_words),
        'bias_words': list(set(bias_words)),
        'bias_score': severity,
        'bias_level': bias_level,
        'bias_color': bias_color
    })


@app.route('/analytics')
def analytics_dashboard():
    try:
        with get_db() as conn:
            total = conn.execute('SELECT COALESCE(SUM(successful),0) FROM sessions').fetchone()[0]
            bias_incidents = conn.execute('SELECT COUNT(*) FROM sessions WHERE bias_detected=1').fetchone()[0]
            avg_match = conn.execute('SELECT COALESCE(AVG(average_match),0) FROM sessions').fetchone()[0]
            avg_severity = conn.execute('SELECT COALESCE(AVG(severity_score),0) FROM sessions WHERE bias_detected=1').fetchone()[0]

            bias_cats = conn.execute('SELECT category, COUNT(*) as cnt FROM bias_events GROUP BY category ORDER BY cnt DESC').fetchall()
            history = conn.execute('SELECT * FROM sessions ORDER BY id DESC LIMIT 10').fetchall()

            scores_raw = conn.execute('SELECT match_percentage FROM candidates').fetchall()
            scores = [r[0] for r in scores_raw]

            skill_gaps_raw = conn.execute(
                'SELECT missing_skills FROM candidates'
            ).fetchall()
            skill_counts = defaultdict(int)
            for row in skill_gaps_raw:
                for skill in json.loads(row[0] or '[]'):
                    skill_counts[skill] += 1
            top_gaps = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:8]

            recent_bias = conn.execute(
                'SELECT be.category, be.words, be.severity, be.timestamp, s.job_role '
                'FROM bias_events be JOIN sessions s ON be.session_id=s.id '
                'ORDER BY be.id DESC LIMIT 5'
            ).fetchall()

        score_dist = {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0}
        for s in scores:
            if s <= 25:
                score_dist['0-25'] += 1
            elif s <= 50:
                score_dist['26-50'] += 1
            elif s <= 75:
                score_dist['51-75'] += 1
            else:
                score_dist['76-100'] += 1

        analytics_data = {
            'total_resumes_processed': total,
            'bias_incidents_detected': bias_incidents,
            'average_bias_severity': round(avg_severity, 1),
            'average_match_score': round(avg_match, 1),
            'clean_rate': round((total - bias_incidents) / total * 100, 1) if total > 0 else 0,
            'top_bias_categories': [{'category': r[0], 'count': r[1]} for r in bias_cats],
            'processing_history': [dict(r) for r in history],
            'top_skill_gaps': [{'skill': k, 'count': v} for k, v in top_gaps],
            'score_distribution': score_dist,
            'recent_bias': [dict(r) for r in recent_bias]
        }
    except Exception as e:
        logger.error("Analytics error: %s", e)
        analytics_data = {
            'total_resumes_processed': 0, 'bias_incidents_detected': 0,
            'average_bias_severity': 0, 'average_match_score': 0, 'clean_rate': 0,
            'top_bias_categories': [], 'processing_history': [],
            'top_skill_gaps': [], 'score_distribution': {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0},
            'recent_bias': []
        }

    return render_template('analytics.html', data=analytics_data)


@app.route('/export-csv')
def export_csv():
    """Export all candidate results as CSV"""
    try:
        with get_db() as conn:
            rows = conn.execute('''
                SELECT s.job_role, s.timestamp, c.filename, c.match_percentage,
                       c.matching_skills, c.missing_skills, c.recommendation,
                       s.bias_detected, s.bias_level, s.severity_score
                FROM candidates c
                JOIN sessions s ON c.session_id = s.id
                ORDER BY s.id DESC, c.match_percentage DESC
            ''').fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Job Role', 'Session Date', 'Resume File', 'Match %',
                         'Matching Skills', 'Missing Skills', 'Recommendation',
                         'Bias Detected', 'Bias Level', 'Severity Score'])

        for row in rows:
            matching = ', '.join(json.loads(row[4] or '[]'))
            missing = ', '.join(json.loads(row[5] or '[]'))
            writer.writerow([
                row[0], row[1], row[2], row[3],
                matching, missing, row[6],
                'Yes' if row[7] else 'No', row[8], row[9]
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=bias_report_{time.strftime("%Y%m%d_%H%M%S")}.csv'}
        )
    except Exception as e:
        logger.error("CSV export error: %s", e)
        return jsonify({'error': 'Export failed'}), 500


@app.route('/upload', methods=['POST'])
def upload_resume():
    try:
        job_role = request.form.get('job_role', '').strip()
        if not job_role or job_role not in job_roles:
            return jsonify({'error': 'Invalid job role selected'})

        files = request.files.getlist('resume')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'})

        pdf_files = [(f, f.filename) for f in files if f.filename.lower().endswith('.pdf')]
        if not pdf_files:
            return jsonify({'error': 'Please upload PDF files only'})
        if len(pdf_files) > MAX_UPLOAD_FILES:
            return jsonify({'error': f'Maximum {MAX_UPLOAD_FILES} files allowed'})

        job_data = job_roles[job_role]
        saved_files = save_uploaded_files(pdf_files)

        results = []
        for fp, fn in saved_files:
            try:
                results.append(process_single_resume(fp, fn, job_data))
            except Exception as e:
                logger.error("Failed processing %s: %s", fn, e)
                results.append({'filename': fn, 'error': str(e), 'status': 'failed'})

        bias_report, severity_total = analyze_job_description_bias(job_data['description'])
        bias_detected, bias_details, bias_level, bias_color = build_bias_details(bias_report, severity_total)
        summary = build_summary(pdf_files, results)

        # LLM bias explanation + rewrite
        llm_bias = None
        if bias_detected:
            llm_bias = get_llm_bias_explanation(job_data['description'], bias_details)

        # Save to database
        save_to_db(job_data, results, summary, bias_detected, bias_details, bias_level, severity_total)

        return jsonify({
            'results': results,
            'summary': summary,
            'bias_detected': bias_detected,
            'bias_details': bias_details,
            'bias_level': bias_level,
            'bias_color': bias_color,
            'severity_score': severity_total,
            'job_title': job_data['title'],
            'llm_bias': llm_bias,
            'llm_available': LLM_AVAILABLE
        })
    except Exception as e:
        logger.error("Upload error: %s", e)
        return jsonify({'error': 'Server error. Please try again.'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    host = os.environ.get('HOST', '127.0.0.1')
    app.run(debug=False, host=host, port=port)
