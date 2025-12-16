#!/usr/bin/env python3
"""Flask app with multiple resume upload support"""

from flask import Flask, request, jsonify, render_template
import os
import re
import PyPDF2
from collections import defaultdict
import time
from concurrent.futures import ThreadPoolExecutor
import threading

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max for multiple files

# Job roles with detailed descriptions and required skills
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

# Bias detection keywords
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
                except Exception:
                    continue
            
            if not text.strip():
                return "Error: Could not extract text from PDF."
            
            return text
            
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def anonymize_resume(text):
    """Remove personal identifiers from resume"""
    # Replace names
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[CANDIDATE NAME]', text)
    # Replace emails
    text = re.sub(r'\b\w+@\w+\.\w+\b', '[EMAIL]', text)
    # Replace phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    # Replace gender indicators
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
    found_skills = []
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills

def calculate_job_match(resume_skills, job_skills):
    """Calculate how well resume matches job requirements"""
    if not job_skills:
        return 0
    
    matching_skills = list(set(resume_skills) & set(job_skills))
    match_percentage = (len(matching_skills) / len(job_skills)) * 100
    
    return {
        "match_percentage": round(match_percentage, 2),
        "matching_skills": matching_skills,
        "missing_skills": list(set(job_skills) - set(resume_skills))
    }

def process_single_resume(file_path, filename, job_data):
    """Process a single resume file"""
    try:
        
        # Extract and process
        resume_text = extract_text_from_pdf(file_path)
        
        if "Error" in resume_text:
            os.remove(file_path)
            return {
                'filename': filename,
                'error': resume_text,
                'status': 'failed'
            }
        
        # Process resume
        anonymized_resume = anonymize_resume(resume_text)
        resume_skills = extract_skills_from_text(resume_text)
        match_result = calculate_job_match(resume_skills, job_data['required_skills'])
        
        # Generate recommendation
        match_percentage = match_result['match_percentage']
        if match_percentage >= 70:
            recommendation = "Excellent match!"
        elif match_percentage >= 40:
            recommendation = "Good match with some gaps."
        else:
            recommendation = "Limited match."
        
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            'filename': filename,
            'status': 'success',
            'match_percentage': match_percentage,
            'matching_skills': match_result['matching_skills'],
            'missing_skills': match_result['missing_skills'],
            'recommendation': recommendation,
            'anonymized_resume': anonymized_resume[:500] + '...' if len(anonymized_resume) > 500 else anonymized_resume
        }
        
    except Exception as e:
        return {
            'filename': filename,
            'error': str(e),
            'status': 'failed'
        }

def get_bias_improvement_suggestions(bias_report):
    """Get specific suggestions for bias improvement"""
    suggestions = []
    
    for category, words in bias_report.items():
        if words:
            if category == 'gender':
                suggestions.append({
                    'type': 'Gender Bias',
                    'words': words,
                    'suggestion': 'Use gender-neutral terms like "team member" instead of "guys"'
                })
            elif category == 'age':
                suggestions.append({
                    'type': 'Age Bias', 
                    'words': words,
                    'suggestion': 'Focus on skills rather than experience level or energy'
                })
            elif category == 'personality':
                suggestions.append({
                    'type': 'Personality Bias',
                    'words': words, 
                    'suggestion': 'Use professional terms instead of casual descriptors'
                })
    
    return suggestions

# Confusion matrix storage
confusion_data = {
    'predictions': []
}

def generate_confusion_matrix():
    """Generate confusion matrix from actual predictions"""
    if not confusion_data['predictions']:
        return {
            'matrix': {'true_positive': 0, 'true_negative': 0, 'false_positive': 0, 'false_negative': 0},
            'metrics': {'accuracy': 0, 'precision': 0, 'recall': 0, 'f1_score': 0},
            'results': []
        }
    
    true_positive = sum(1 for p in confusion_data['predictions'] if p['predicted'] and p['actual'])
    true_negative = sum(1 for p in confusion_data['predictions'] if not p['predicted'] and not p['actual'])
    false_positive = sum(1 for p in confusion_data['predictions'] if p['predicted'] and not p['actual'])
    false_negative = sum(1 for p in confusion_data['predictions'] if not p['predicted'] and p['actual'])
    
    total = len(confusion_data['predictions'])
    accuracy = (true_positive + true_negative) / total if total > 0 else 0
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'matrix': {
            'true_positive': true_positive,
            'true_negative': true_negative,
            'false_positive': false_positive,
            'false_negative': false_negative
        },
        'metrics': {
            'accuracy': round(accuracy, 3),
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1_score, 3)
        },
        'results': [{
            'description': p['description'],
            'predicted': 'Biased' if p['predicted'] else 'Clean',
            'actual': 'Biased' if p['actual'] else 'Clean',
            'status': 'correct' if p['predicted'] == p['actual'] else 'incorrect'
        } for p in confusion_data['predictions']]
    }

@app.route('/')
def index():
    return render_template('index.html', job_roles=job_roles)

@app.route('/confusion-matrix')
def confusion_matrix():
    """Display confusion matrix page"""
    matrix_data = generate_confusion_matrix()
    return render_template('confusion_matrix.html', matrix_data=matrix_data)

@app.route('/check-bias-realtime', methods=['POST'])
def check_bias_realtime():
    """Real-time bias checking API"""
    data = request.get_json()
    text = data.get('text', '')
    
    bias_report = analyze_job_description_bias(text)
    bias_words = []
    bias_detected = False
    
    for category, words in bias_report.items():
        if words:
            bias_detected = True
            bias_words.extend(words)
    
    return jsonify({
        'bias_detected': bias_detected,
        'bias_words': list(set(bias_words)),
        'bias_score': len(set(bias_words))
    })

# Global storage for analytics
analytics_storage = {
    'total_resumes': 0,
    'bias_detections': [],
    'processing_history': []
}

@app.route('/analytics')
def analytics_dashboard():
    """Analytics dashboard with real data"""
    bias_counts = defaultdict(int)
    for bias in analytics_storage['bias_detections']:
        for category in bias:
            bias_counts[category] += 1
    
    analytics_data = {
        'total_resumes_processed': analytics_storage['total_resumes'],
        'bias_incidents_detected': len(analytics_storage['bias_detections']),
        'average_bias_score': round(sum(len(b) for b in analytics_storage['bias_detections']) / len(analytics_storage['bias_detections']), 2) if analytics_storage['bias_detections'] else 0,
        'top_bias_categories': [{'category': k.title(), 'count': v} for k, v in sorted(bias_counts.items(), key=lambda x: x[1], reverse=True)],
        'processing_history': analytics_storage['processing_history'][-10:]
    }
    return render_template('analytics.html', data=analytics_data)

@app.route('/upload', methods=['POST'])
def upload_resume():
    try:
        job_role = request.form.get('job_role')
        
        if not job_role or job_role not in job_roles:
            return jsonify({'error': 'Invalid job role selected'})
        
        # Handle multiple files
        files = request.files.getlist('resume')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'})
        
        # Filter PDF files
        pdf_files = [(f, f.filename) for f in files if f.filename.lower().endswith('.pdf')]
        
        if not pdf_files:
            return jsonify({'error': 'Please upload PDF files only'})
        
        if len(pdf_files) > 20:
            return jsonify({'error': 'Maximum 20 files allowed'})
        
        # Create uploads directory
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        job_data = job_roles[job_role]
        
        # Save all files first
        saved_files = []
        for file, filename in pdf_files:
            safe_filename = f"resume_{int(time.time())}_{len(saved_files)}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(file_path)
            saved_files.append((file_path, filename))
            time.sleep(0.01)  # Ensure unique timestamps
        
        # Process files in parallel
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_single_resume, file_path, filename, job_data) for file_path, filename in saved_files]
            
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'filename': 'unknown',
                        'error': str(e),
                        'status': 'failed'
                    })
        
        # Analyze job description for bias (once)
        bias_report = analyze_job_description_bias(job_data['description'])
        bias_details = []
        bias_detected = False
        
        for category, words in bias_report.items():
            if words:
                bias_detected = True
                bias_details.append({
                    'category': category.title(),
                    'words': list(set(words))
                })
        
        # Calculate summary statistics
        successful_results = [r for r in results if r['status'] == 'success']
        failed_results = [r for r in results if r['status'] == 'failed']
        
        summary = {
            'total_files': len(pdf_files),
            'successful': len(successful_results),
            'failed': len(failed_results),
            'average_match': round(sum(r['match_percentage'] for r in successful_results) / len(successful_results), 2) if successful_results else 0,
            'top_candidates': sorted(successful_results, key=lambda x: x['match_percentage'], reverse=True)[:5]
        }
        
        # Update analytics
        analytics_storage['total_resumes'] += len(successful_results)
        if bias_detected:
            analytics_storage['bias_detections'].append(list(bias_report.keys()))
        analytics_storage['processing_history'].append({
            'job_role': job_data['title'],
            'count': len(successful_results),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Update confusion matrix
        confusion_data['predictions'].append({
            'description': job_data['description'],
            'predicted': bias_detected,
            'actual': bias_detected  # In real scenario, this would be manually labeled
        })
        
        return jsonify({
            'results': results,
            'summary': summary,
            'bias_detected': bias_detected,
            'bias_details': bias_details,
            'job_title': job_data['title']
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5003))
    app.run(debug=False, host='0.0.0.0', port=port)
