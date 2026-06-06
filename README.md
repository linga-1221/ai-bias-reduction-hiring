<div align="center">

# 🤖 FairHire AI — Bias Detection in Hiring

### Making recruitment fair, transparent, and skill-based — powered by AI & Gemini LLM

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-View_App-6366f1?style=for-the-badge)](https://ai-for-reducing-bias-in-hiring.vercel.app)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com)
[![Gemini](https://img.shields.io/badge/Gemini_AI-1.5_Flash-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[![Deploy](https://img.shields.io/badge/Deploy-Vercel-black?style=flat&logo=vercel)](https://vercel.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite)](https://sqlite.org)
[![PDF](https://img.shields.io/badge/PDF-PyPDF2-red?style=flat)](https://pypdf2.readthedocs.io)
[![Chart.js](https://img.shields.io/badge/Charts-Chart.js-FF6384?style=flat&logo=chartdotjs)](https://chartjs.org)

*Unconscious bias costs companies top talent. This app removes it from the equation.*

</div>

---

## 📌 The Problem

Traditional hiring processes are riddled with unconscious bias — from gendered language in job descriptions that discourages qualified candidates, to resume screening that prioritizes names and backgrounds over skills.

This project tackles that at the source, using AI to make hiring decisions based on **what candidates can do**, not who they are.

> **Research shows** biased job descriptions reduce applications from women by 40%, older workers by 35%, and underrepresented groups significantly — costing companies their best talent.

---

## ✨ Features

### 🔍 Advanced Bias Detection
- Detects bias across **4 categories**: Gender, Age, Personality, Exclusionary
- **Severity scoring system** — LOW / MEDIUM / HIGH with weighted keyword scores
- **30+ bias keywords** with research-backed rationale
- Context-aware detection (skips "not aggressive", "avoid dominant" etc.)
- **Neutral language suggestions** for every flagged word

### 🤖 Gemini AI Integration
- **Explains WHY** each flagged word creates bias (not just flags it)
- **Rewrites the entire job description** in inclusive, neutral language automatically
- **AI career recommendations** — personalized tips for each candidate to close skill gaps
- Powered by Google Gemini 1.5 Flash

### 🔒 Resume Anonymization
- Strips names, emails, phone numbers, pronouns, profile URLs (LinkedIn/GitHub)
- Removes gender indicators and honorifics (Mr./Mrs./Dr.)
- Retains skills, experience, and qualifications intact
- Enables true **blind screening**

### 📄 Batch Resume Processing
- Upload **1–20 PDF resumes** simultaneously
- Automatic text extraction via PyPDF2
- Skill-based matching with **50+ technical skills**
- Candidates auto-ranked by match percentage
- Match score includes bonus for extra relevant skills

### 📊 Real-Time Analytics Dashboard
- All data from **actual uploads** — no fake/sample numbers
- 4 live Chart.js visualizations:
  - Bias categories breakdown (doughnut)
  - Match score distribution (bar)
  - Top skill gaps across all candidates (horizontal bar)
  - Bias vs Clean job descriptions (pie)
- Processing history table with timestamps
- Recent bias alerts feed

### 📈 Model Performance (Confusion Matrix)
- Evaluated on **15 labeled ground-truth test cases**
- Real metrics: Accuracy, Precision, Recall, F1 Score
- Color-coded results table showing correct/incorrect predictions
- Honest transparency about model limitations

### 💾 Data Persistence & Export
- **SQLite database** — all sessions, candidates, bias events persist permanently
- **Export to CSV** — full candidate report downloadable as spreadsheet
- Includes: Job Role, Match %, Skills, Recommendation, Bias Level, Severity

---

## 🛠️ Tech Stack

```
Backend           → Python 3.9+, Flask 3.1.1
LLM / AI          → Google Gemini 1.5 Flash API
NLP               → Keyword classification, severity scoring, regex
PDF Processing    → PyPDF2
Database          → SQLite (persistent storage)
Frontend          → HTML5, CSS3, Vanilla JavaScript
Charts            → Chart.js 4.4
Security          → Werkzeug secure_filename, XSS prevention
Deployment        → Vercel (serverless) + GitHub CI/CD
```

---

## 🗂️ Project Structure

```
ai-bias-reduction-hiring/
├── app.py                        # Main Flask app — all routes & logic
├── api/
│   └── index.py                  # Vercel WSGI entry point
├── templates/
│   ├── index.html                # Main UI — upload & analyze
│   ├── analytics.html            # Analytics dashboard
│   └── confusion_matrix.html     # Model performance page
├── static/
│   ├── css/style.css             # Modern dark UI stylesheet
│   └── js/main.js                # Frontend JavaScript (XSS-safe DOM)
├── sample_pdfs/                  # Sample resumes for testing
├── requirements.txt              # Python dependencies
├── vercel.json                   # Vercel deployment config
└── README.md
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.9+
- pip
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone the repository
```bash
git clone https://github.com/linga-1221/ai-bias-reduction-hiring.git
cd ai-bias-reduction-hiring
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables (optional — for Gemini AI)
```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Mac/Linux
export GEMINI_API_KEY=your_api_key_here
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
User selects job role + uploads 1–20 PDF resumes
                    ↓
         PyPDF2 extracts raw resume text
                    ↓
    ┌───────────────────────────────────────┐
    │  For each resume (processed one by one)│
    │                                        │
    │  1. Anonymizer                         │
    │     Regex strips name, email, phone,   │
    │     pronouns, profile URLs             │
    │                                        │
    │  2. Skill Extractor                    │
    │     50+ skills matched against text    │
    │                                        │
    │  3. Job Matcher                        │
    │     Match % = matching/required skills │
    │     + bonus for extra skills (max 5%)  │
    │                                        │
    │  4. Gemini AI (if configured)          │
    │     Generates 3 career tips for        │
    │     candidate's missing skills         │
    └───────────────────────────────────────┘
                    ↓
    Job Description analyzed for bias (once)
    → 4 categories, severity weights
    → Gemini explains bias + rewrites JD
                    ↓
    Results saved to SQLite database
                    ↓
    Response sent to frontend:
      ✅ Candidate rankings by match %
      ⚠️  Bias flags with severity score
      🤖 AI-rewritten job description
      📄 Anonymized resumes
      💡 AI career recommendations
```

---

## 🖥️ Usage

1. **Select a job role** from 10 predefined options
2. **Upload PDF resumes** (1–20 files) using drag & drop or file picker
3. **Click "Analyze Resumes"** to get:
   - Batch processing summary
   - Top candidates ranked by match %
   - Bias analysis with severity score
   - AI-powered bias explanation and rewritten JD (if Gemini configured)
   - Per-candidate: matching/missing skills, AI career tips, anonymized resume
4. **Real-time bias checker** — paste any job description and see bias instantly
5. **Analytics Dashboard** — view persistent stats, charts, and history
6. **Export CSV** — download full candidate report as spreadsheet

---

## 📊 Sample Output

```
Job Role: Data Scientist
Resumes Processed: 5  |  Avg Match: 64%

🏆 Top Candidate: resume_alex.pdf — 87.5%
   ✅ Matched: Python, Machine Learning, SQL, Pandas, NumPy
   ❌ Missing: TensorFlow, Tableau
   💡 AI Tip: "Complete the TensorFlow Developer Certificate on Coursera"

⚠️ Bias Detected — MEDIUM severity (Score: 6)
   Age Bias: energetic, fresh
   Personality Bias: rockstar

🤖 Gemini AI Rewrite:
   "We are seeking a Data Scientist to analyze complex datasets.
    The ideal candidate brings innovative perspectives on machine
    learning and statistical analysis..."
```

---

## 🎯 Use Cases

| User | How They Use It |
|------|----------------|
| **HR Teams** | Screen 10–20 resumes fairly in one session |
| **Recruiters** | Audit job descriptions before publishing |
| **Companies** | Ensure DEI compliance in hiring pipelines |
| **Startups** | Fast, unbiased candidate shortlisting |
| **Researchers** | Study algorithmic fairness in recruitment |

---

## 🔒 Security Features

- **XSS Prevention** — all DOM updates use `textContent` / `createElement`, never `innerHTML` with user data
- **Path Traversal Protection** — all filenames sanitized via `secure_filename()`
- **Input Validation** — file type, count, and size validated on both client and server
- **Error Handling** — structured logging, no raw errors exposed to users
- **Localhost Default** — server binds to `127.0.0.1` by default, configurable via `HOST` env var

---

## 🔮 Roadmap

- [x] LLM-powered bias explanation (Gemini integration) ✅
- [x] Severity scoring system ✅
- [x] SQLite persistent database ✅
- [x] CSV export ✅
- [x] Batch resume processing (20 files) ✅
- [ ] Multi-language support (Spanish, French, German)
- [ ] ATS integrations (Workday, Greenhouse, Lever)
- [ ] REST API for third-party HR tool integrations
- [ ] Browser extension for real-time JD scanning
- [ ] GPT-4 / Claude integration option

---

## 🤝 Contributing

Contributions are welcome — especially around expanding bias detection categories and improving model accuracy.

```bash
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
