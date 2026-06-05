#!/usr/bin/env python3
"""Flask app with multiple resume upload support"""

from flask import Flask, request, jsonify, render_template
import os
import re
import logging
import PyPDF2
from collections import defaultdict
import time
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/uploads' if os.environ.get('VERCEL') else 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
MAX_UPLOAD_FILES = 20

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

BIAS_KEYWORDS = {
    "gender": {
        "male_biased": ["strong", "aggressive", "competitive", "dominant", "assertive"],
        "female_biased": ["nurturing", "collaborative", "supportive"],
        "neutral": ["skilled", "qualified", "experienced", "proficient"]
    },
    "age": {
        "biased": ["young", "energetic", "fresh", "recent graduate", "digital native", "mature", "experienced", "seasoned"],
        "neutral": ["qualified", "skilled", "talented"]
    },
    "personality": {
        "biased": ["rockstar", "ninja", "guru", "fast-paced"],
        "neutral": ["motivated", "dedicated", "team-oriented"]
    }
}

# In-memory storage
analytics_storage = {'total_resumes': 0, 'bias_detections': [], 'processing_history': []}
confusion_data = {'predictions': []}


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
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
    """Remove personal identifiers from resume"""
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[CANDIDATE NAME]', text)
    text = re.sub(r'\b\w+@\w+\.\w+\b', '[EMAIL]', text)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b(Male|Female|man|woman|he/him|she/her)\b', '[GENDER]', text, flags=re.IGNORECASE)
    return text


def analyze_job_description_bias(text):
    """Detect biased language in job descriptions"""
    words = text.lower().split()
    bias_report = defaultdict(list)
    for category, bias_types in BIAS_KEYWORDS.items():
        for bias_type, keywords in bias_types.items():
            if bias_type != "neutral":
                for word in words:
                    if word in keywords:
                        bias_report[category].append(word)
    return bias_report


def extract_skills_from_text(text):
    """Extract skills from resume text"""
    common_skills = [
        "python", "java", "javascript", "html", "css", "sql", "nosql", "mongodb",
        "react", "angular", "vue", "node", "express", "django", "flask",
        "machine learning", "data analysis", "data science", "ai", "artificial intelligence",
        "git", "docker", "kubernetes", "aws", "azure", "gcp",
        "project management", "agile", "scrum", "leadership", "teamwork",
        "algorithms", "data structures", "pandas", "numpy", "tensorflow", "pytorch"
    ]
    text_lower = text.lower()
    return [skill for skill in common_skills if skill in text_lower]


def calculate_job_match(resume_skills, job_skills):
    """Calculate how well resume matches job requirements"""
    if not job_skills:
        return {"match_percentage": 0, "matching_skills": [], "missing_skills": []}
    matching = list(set(resume_skills) & set(job_skills))
    match_percentage = round((len(matching) / len(job_skills)) * 100, 2)
    return {
        "match_percentage": match_percentage,
        "matching_skills": matching,
        "missing_skills": list(set(job_skills) - set(resume_skills))
    }


def build_recommendation(match_percentage):
    """Return recommendation string based on match percentage"""
    if match_percentage >= 70:
        return "Excellent match!"
    if match_percentage >= 40:
        return "Good match with some gaps."
    return "Limited match."


def process_single_resume(file_path, filename, job_data):
    """Process a single resume file"""
    try:
        resume_text = extract_text_from_pdf(file_path)
        if resume_text.startswith("Error"):
            return {'filename': filename, 'error': resume_text, 'status': 'failed'}

        anonymized_resume = anonymize_resume(resume_text)
        resume_skills = extract_skills_from_text(resume_text)
        match_result = calculate_job_match(resume_skills, job_data['required_skills'])
        match_percentage = match_result['match_percentage']

        return {
            'filename': filename,
            'status': 'success',
            'match_percentage': match_percentage,
            'matching_skills': match_result['matching_skills'],
            'missing_skills': match_result['missing_skills'],
            'recommendation': build_recommendation(match_percentage),
            'anonymized_resume': anonymized_resume[:500] + '...' if len(anonymized_resume) > 500 else anonymized_resume
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
    """Generate confusion matrix from actual predictions"""
    if not confusion_data['predictions']:
        return {
            'matrix': {'true_positive': 0, 'true_negative': 0, 'false_positive': 0, 'false_negative': 0},
            'metrics': {'accuracy': 0, 'precision': 0, 'recall': 0, 'f1_score': 0},
            'results': []
        }
    preds = confusion_data['predictions']
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
    """Save uploaded files to disk and return list of (path, original_filename)"""
    saved = []
    for i, (file, filename) in enumerate(pdf_files):
        safe_name = secure_filename(filename) or "resume.pdf"
        dest = os.path.join(app.config['UPLOAD_FOLDER'], f"resume_{int(time.time())}_{i}_{safe_name}")
        file.save(dest)
        saved.append((dest, filename))
        time.sleep(0.01)
    return saved


def run_parallel_processing(saved_files, job_data):
    """Process resumes sequentially (safe for serverless)"""
    results = []
    for fp, fn in saved_files:
        try:
            results.append(process_single_resume(fp, fn, job_data))
        except Exception as e:
            logger.error("Failed processing %s: %s", fn, e)
            results.append({'filename': fn, 'error': str(e), 'status': 'failed'})
    return results


def build_bias_details(bias_report):
    """Format bias report into response-ready list"""
    details = []
    bias_detected = False
    for category, words in bias_report.items():
        if words:
            bias_detected = True
            details.append({'category': category.title(), 'words': list(set(words))})
    return bias_detected, details


def build_summary(pdf_files, results):
    """Calculate summary statistics from results"""
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    return {
        'total_files': len(pdf_files),
        'successful': len(successful),
        'failed': len(failed),
        'average_match': round(sum(r['match_percentage'] for r in successful) / len(successful), 2) if successful else 0,
        'top_candidates': sorted(successful, key=lambda x: x['match_percentage'], reverse=True)[:5]
    }


def update_analytics(job_data, successful_count, bias_detected, bias_report):
    """Update in-memory analytics storage"""
    analytics_storage['total_resumes'] += successful_count
    if bias_detected:
        analytics_storage['bias_detections'].append(list(bias_report.keys()))
    analytics_storage['processing_history'].append({
        'job_role': job_data['title'],
        'count': successful_count,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    confusion_data['predictions'].append({
        'description': job_data['description'],
        'predicted': bias_detected,
        'actual': bias_detected
    })
    # Cap to last 100 entries to prevent memory growth
    analytics_storage['processing_history'] = analytics_storage['processing_history'][-100:]
    analytics_storage['bias_detections'] = analytics_storage['bias_detections'][-100:]
    confusion_data['predictions'] = confusion_data['predictions'][-100:]


@app.route('/')
def index():
    return render_template('index.html', job_roles=job_roles)


@app.route('/confusion-matrix')
def confusion_matrix():
    return render_template('confusion_matrix.html', matrix_data=generate_confusion_matrix())


@app.route('/check-bias-realtime', methods=['POST'])
def check_bias_realtime():
    data = request.get_json()
    text = data.get('text', '') if data else ''
    bias_report = analyze_job_description_bias(text)
    bias_words = list({word for words in bias_report.values() for word in words})
    return jsonify({
        'bias_detected': bool(bias_words),
        'bias_words': bias_words,
        'bias_score': len(bias_words)
    })


@app.route('/analytics')
def analytics_dashboard():
    bias_counts = defaultdict(int)
    for bias in analytics_storage['bias_detections']:
        for category in bias:
            bias_counts[category] += 1

    total = analytics_storage['total_resumes']
    bias_incidents = len(analytics_storage['bias_detections'])
    analytics_data = {
        'total_resumes_processed': total,
        'bias_incidents_detected': bias_incidents,
        'average_bias_score': round(
            sum(len(b) for b in analytics_storage['bias_detections']) / bias_incidents, 2
        ) if bias_incidents else 0,
        'top_bias_categories': [
            {'category': k.title(), 'count': v}
            for k, v in sorted(bias_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        'processing_history': analytics_storage['processing_history'][-10:],
        'clean_rate': round((total - bias_incidents) / total * 100, 1) if total > 0 else 0
    }
    return render_template('analytics.html', data=analytics_data)


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
        results = run_parallel_processing(saved_files, job_data)

        bias_report = analyze_job_description_bias(job_data['description'])
        bias_detected, bias_details = build_bias_details(bias_report)
        summary = build_summary(pdf_files, results)
        update_analytics(job_data, summary['successful'], bias_detected, bias_report)

        return jsonify({
            'results': results,
            'summary': summary,
            'bias_detected': bias_detected,
            'bias_details': bias_details,
            'job_title': job_data['title']
        })
    except Exception as e:
        logger.error("Upload error: %s", e)
        return jsonify({'error': 'Server error. Please try again.'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    host = os.environ.get('HOST', '127.0.0.1')
    app.run(debug=False, host=host, port=port)
