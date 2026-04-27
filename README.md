<div align="center">

# 🤖 AI Bias Reduction in Hiring

### Making recruitment fair, transparent, and skill-based — powered by AI

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-View_App-6366f1?style=for-the-badge)](https://ai-for-reducing-bias-in-hiring.vercel.app)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[![NLP](https://img.shields.io/badge/NLP-NLTK-blue?style=flat)](https://nltk.org)
[![ML](https://img.shields.io/badge/ML-scikit--learn-F7931E?style=flat&logo=scikitlearn)](https://scikit-learn.org)
[![PDF](https://img.shields.io/badge/PDF-PyMuPDF-red?style=flat)](https://pymupdf.readthedocs.io)
[![Deploy](https://img.shields.io/badge/Deploy-Vercel-black?style=flat&logo=vercel)](https://vercel.com)

*Unconscious bias costs companies top talent. This app removes it from the equation.*

</div>

---

## 📌 The Problem

Traditional hiring processes are riddled with unconscious bias — from gendered language in job descriptions that discourages qualified candidates, to resume screening that prioritizes names and backgrounds over skills. This project tackles that at the source, using AI to make hiring decisions based on **what candidates can do**, not who they are.

---

## ✨ Features

### 🔍 Bias Detection in Job Descriptions
- Identifies **gender bias** (e.g., masculine-coded words like "aggressive," "dominant")
- Flags **age bias** (e.g., "young and energetic," "recent graduate")
- Catches **personality bias** (e.g., "culture fit" language)
- Detects **ethnicity-coded** language patterns
- Provides a **bias score** with line-by-line flagging

### 🔒 Resume Anonymization
- Strips personally identifiable information (name, gender markers, age indicators)
- Removes school/college names that could trigger prestige bias
- Retains skills, experience, and qualifications intact
- Outputs a **clean, anonymized version** for fair screening

### 🎯 Skill-Based Candidate Matching
- Computes **job-candidate compatibility %** based purely on skills
- Supports **20+ predefined job roles** with curated skill requirements
- Upload PDF resumes — extraction is automatic

### 📊 Performance Analytics
- Confusion matrix showing system accuracy on bias classification
- Precision, recall, and F1 metrics for model transparency

---

## 🛠️ Tech Stack

```
Backend           → Python 3.9+, Flask
NLP / AI          → NLTK, scikit-learn
PDF Processing    → PyPDF2, PyMuPDF
Data Layer        → Pandas, NumPy
Frontend          → HTML5, CSS3, Vanilla JavaScript
Deployment        → Vercel (Frontend), Heroku (Backend via Procfile)
```

---

## 🗂️ Project Structure

```
ai-bias-reduction-hiring/
├── app.py                      # Main Flask application & route handlers
├── templates/
│   ├── index.html              # Main UI — upload + analyze interface
│   └── confusion_matrix.html  # Model performance analytics page
├── static/
│   ├── css/                    # Stylesheets
│   └── js/                     # Client-side JavaScript
├── sample_pdfs/                # Sample resumes for testing
├── requirements.txt            # Python dependencies (development)
├── requirements_deploy.txt     # Python dependencies (production)
├── Procfile                    # Heroku deployment config
└── README.md
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.9 or higher
- pip

### 1. Clone the repository
```bash
git clone https://github.com/linga-1221/ai-bias-reduction-hiring.git
cd ai-bias-reduction-hiring
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download NLTK data (first run only)
```python
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
```

### 4. Run the application
```bash
python app.py
```

### 5. Open in browser
```
http://127.0.0.1:5003
```

---

## 🧠 How It Works

```
User selects a job role + uploads PDF resume
              ↓
PyPDF2 / PyMuPDF extract raw resume text
              ↓
┌─────────────────────────────────────────┐
│  Two parallel pipelines run:            │
│                                         │
│  1. Bias Detector                       │
│     NLTK tokenizes job description      │
│     → scikit-learn classifier scores    │
│       bias type + severity              │
│                                         │
│  2. Anonymizer + Skill Matcher          │
│     PII stripped from resume            │
│     → Skills extracted via keyword NLP  │
│     → Match % computed vs. job role     │
└─────────────────────────────────────────┘
              ↓
Flask renders results:
  ✅ Compatibility score
  🔴 Missing skills
  ⚠️  Bias flags in JD
  📄 Anonymized resume output
```

---

## 🖥️ Usage

1. **Select a job role** from 20+ predefined options (Software Engineer, Data Analyst, Product Manager, etc.)
2. **Upload a PDF resume** using the file picker
3. **Click "Analyze"** to instantly get:
   - Job match percentage
   - Matching vs. missing skills breakdown
   - Bias flags found in the job description
   - Anonymized resume for blind screening
4. **View system performance** on the Analytics page (confusion matrix)

---

## 📊 Sample Output

```
Job Role: Data Scientist
Match Score: 78%

✅ Matched Skills: Python, Machine Learning, SQL, Pandas, NumPy
❌ Missing Skills: TensorFlow, Tableau, Spark

⚠️ Bias Detected in Job Description:
  → "young and dynamic team" — Age bias (line 3)
  → "aggressive go-getter" — Gender bias (line 7)

📄 Anonymized Resume: [Available for download]
```

---

## 🎯 Use Cases

- **HR teams** screening high-volume candidates fairly
- **Recruitment agencies** auditing their job description language
- **Companies** ensuring DEI compliance in hiring pipelines
- **Researchers** studying algorithmic fairness in recruitment

---

## 🔮 Roadmap

- [ ] LLM-powered bias explanation (GPT / Gemini integration)
- [ ] Multi-language job description support (Spanish, French, German)
- [ ] ATS integrations (Workday, Greenhouse, Lever)
- [ ] Real-time browser extension for JD scanning
- [ ] REST API for third-party HR tool integrations
- [ ] Bias trend dashboard across multiple job postings

---

## 🤝 Contributing

Contributions are welcome — especially around expanding bias detection categories and improving model accuracy.

```bash
# Fork → Branch → Commit → PR
git checkout -b feature/your-feature
git commit -m "Add: describe your change"
git push origin feature/your-feature
```

Please open an issue first to discuss major changes.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📬 Contact

**Nagalinga K.**
- 💼 LinkedIn: [linkedin.com/in/nagalinga-k](https://linkedin.com/in/nagalinga-k)
- 📧 Email: nagakuchivaripalli@gmail.com
- 🐙 GitHub: [@linga-1221](https://github.com/linga-1221)

---

<div align="center">

⭐ **Star this repo if you believe hiring should be fair.**

*Built with 🤖 and a commitment to inclusive recruitment.*

*by [Nagalinga K.](https://github.com/linga-1221)*

</div>
