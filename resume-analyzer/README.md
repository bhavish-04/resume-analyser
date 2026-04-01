# 📄 Smart Resume Analyzer v2.0

An advanced, production-quality **ATS-style resume evaluation system** that scores a candidate's resume against a job description across **six weighted dimensions** — delivering a comprehensive match score, skill-gap analysis, per-dimension feedback, and actionable improvement suggestions.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40-FF4B4B?logo=streamlit&logoColor=white)
![spaCy](https://img.shields.io/badge/spaCy-3.7-09A3D5?logo=spacy&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 Project Overview

Most resume review tools only check keyword overlap. **Smart Resume Analyzer** goes far beyond that — it evaluates resumes the way a real ATS (Applicant Tracking System) would, scoring across six distinct dimensions:

| # | Dimension | Weight | What It Measures |
|---|-----------|--------|------------------|
| 1 | **Keyword Relevance** | 30% | TF-IDF cosine similarity between resume and job description |
| 2 | **Skills Match** | 20% | Percentage of JD-required skills found in the resume |
| 3 | **Project Quality** | 20% | Technologies, action verbs, and complexity indicators in projects |
| 4 | **Experience** | 15% | Section presence, action verbs, JD relevance, dates/durations |
| 5 | **Impact** | 10% | Quantified achievements (percentages, metrics, dollar amounts) |
| 6 | **Structure** | 5% | Presence of key sections (Education, Skills, Projects, Experience, Summary) |

The final weighted score gives candidates a realistic picture of how their resume stacks up — along with specific, actionable feedback on every dimension.

---

## ✨ Features

### 📑 Resume Parsing
- Upload any text-based PDF resume
- Robust extraction using PyPDF2 with error handling for encrypted or corrupt files
- Automatic text cleanup (whitespace normalization, garbage removal)

### 🔧 Skills Match Analysis
- Curated database of **150+ industry skills** spanning programming languages, frameworks, cloud platforms, data science tools, and soft skills
- **Word-boundary regex matching** for single-word skills to prevent false positives (e.g., "R" won't match inside "React")
- **Substring matching** for multi-word skills (e.g., "machine learning", "ci/cd")
- Reports matched skills, missing skills, and a coverage percentage

### 🎯 Keyword Relevance (TF-IDF)
- **TF-IDF Vectorization** converts both documents into numerical feature vectors
- **Cosine Similarity** measures the angle between vectors — a proven, interpretable metric
- Score is presented as a percentage (0–100%) with color-coded tiers

### 📂 Project Quality Analysis
- Detects the "Projects" section via regex section-header matching
- Evaluates four sub-dimensions (each worth 25 points):
  - **Section presence** — Does a Projects section exist?
  - **Technologies mentioned** — Are specific tech stacks listed per project?
  - **Action verbs** — Do descriptions start with strong verbs (built, developed, implemented)?
  - **Complexity indicators** — Are terms like API, scalable, ML, distributed present?

### 💼 Experience Analysis
- Detects Experience / Internship sections
- Evaluates:
  - **Action verb usage** — Varied, impactful language in bullet points
  - **Role relevance** — Keyword overlap between experience section and job description
  - **Dates & durations** — Presence of start/end dates showing career progression

### 📊 Impact Analysis
- Detects quantified achievements using 8 regex patterns:
  - Percentage improvements ("improved latency by 40%")
  - Dollar amounts ("saved $500K annually")
  - User/traffic counts ("handled 10K+ concurrent users")
  - Team sizes ("managed a team of 8")
  - Multiplier claims ("3x faster response time")
- Scoring: 0 metrics → 10%, 1–2 → 40%, 3–4 → 70%, 5+ → 100%

### 📄 Resume Structure Analysis
- Checks for five essential sections with individual weights:
  - Education (20), Skills (25), Projects (20), Experience (25), Summary (10)
- Reports found and missing sections with per-section feedback

### 🧮 Weighted Final Scoring
```
final_score = 0.30 × keyword_score
            + 0.20 × skills_score
            + 0.20 × project_score
            + 0.15 × experience_score
            + 0.10 × impact_score
            + 0.05 × structure_score
```
Tier classification: **Strong** (≥75%), **Moderate** (50–74%), **Low** (<50%)

### 💡 Intelligent Suggestions Engine
- Aggregates feedback from all six dimensions
- Filters for actionable items (⚠️ warnings, ❌ gaps, 💡 tips)
- Identifies the two weakest dimensions as priority improvement areas
- De-duplicates suggestions while preserving priority order

### 🎨 Professional Dashboard
- **Gradient hero header** with ATS branding
- **Overall score card** color-coded by tier (green / yellow / red)
- **Six progress bars** with per-dimension scores, color coding, and weight labels
- **Skill pills** — green for matched, red for missing
- **Four feedback panels** for Projects, Experience, Impact, and Structure
- **Expandable sections** for detected metrics, full skills breakdown, and raw text preview

---

## 🏗️ Architecture

```
resume-analyzer/
│
├── app.py                  # Streamlit web application (UI + orchestration)
├── requirements.txt        # Pinned Python dependencies
├── README.md               # This documentation
│
├── utils/
│   ├── __init__.py         # Python package marker
│   ├── parser.py           # PDF text extraction (PyPDF2)
│   ├── analyzer.py         # Text preprocessing, TF-IDF similarity, skill gaps
│   ├── evaluator.py        # ATS evaluation engine (projects, experience, impact, structure, scoring)
│   └── skills.py           # Skills database loading and extraction
│
└── data/
    └── skills_list.txt     # Curated list of 150+ industry skills
```

### File-by-File Breakdown

#### `app.py` — UI & Orchestration Layer

**What it does:** Renders the Streamlit dashboard, handles user input (PDF upload + JD text area), runs the 6-dimension analysis pipeline, and displays the results with progress bars, skill pills, feedback panels, and suggestions.

**Why it exists:** Separates presentation from business logic. The UI calls utility functions — it never performs NLP or scoring directly. This makes the analysis engine independently testable and reusable (e.g., as a CLI or API).

**Data flow:**
1. User uploads PDF → `parser.extract_text_from_pdf()`
2. Loads skills database → `skills.load_skills()`
3. Extracts skills from both texts → `skills.extract_skills()` (×2)
4. Computes keyword similarity → `analyzer.compute_similarity()`
5. Analyzes projects → `evaluator.analyze_projects()`
6. Analyzes experience → `evaluator.analyze_experience()`
7. Analyzes impact → `evaluator.analyze_impact()`
8. Analyzes structure → `evaluator.analyze_structure()`
9. Computes weighted final score → `evaluator.calculate_final_score()`
10. Renders the results dashboard

---

#### `utils/parser.py` — PDF Text Extraction

**What it does:** Takes a file-like object (Streamlit's `UploadedFile`), reads it through PyPDF2, iterates over all pages, and returns cleaned text.

**Why it exists:** Isolates PDF-specific logic and error handling (encrypted files, corrupt PDFs, empty pages) from the rest of the application.

---

#### `utils/analyzer.py` — Core NLP Engine

**What it does:** Provides text preprocessing (lowercasing, URL/email removal, spaCy lemmatization), TF-IDF vectorization, cosine similarity computation, and skill-gap detection.

**Why it exists:** Houses the NLP intelligence. Can be unit-tested independently or reused in a CLI tool.

**Key functions:**
- `preprocess_text(text)` — Clean → tokenize → lemmatize
- `compute_similarity(resume_text, jd_text)` — TF-IDF + cosine similarity → 0.0–1.0
- `get_missing_skills(resume_skills, jd_skills)` — Set difference

---

#### `utils/evaluator.py` — ATS Evaluation Engine *(NEW in v2.0)*

**What it does:** Evaluates resumes across four qualitative dimensions (projects, experience, impact, structure) and computes a weighted final score. Every function returns an explainable score with human-readable feedback.

**Why it exists:** Extends the analyzer beyond simple keyword matching into a multi-dimensional ATS simulation. All analysis is rule-based (regex + lexicon matching) — no heavy ML dependencies.

**Key functions:**
| Function | Input | Output |
|----------|-------|--------|
| `analyze_projects(resume_text)` | Resume text | `{score, feedback[]}` |
| `analyze_experience(resume_text, jd_text)` | Resume + JD | `{score, feedback[]}` |
| `analyze_impact(resume_text)` | Resume text | `{score, feedback[], metrics_found[]}` |
| `analyze_structure(resume_text)` | Resume text | `{score, feedback[], found_sections[], missing_sections[]}` |
| `calculate_final_score(...)` | 6 sub-scores | `{final_score, breakdown{}, tier, feedback[]}` |

**Supporting infrastructure:**
- `_extract_section_text()` — Extracts text between two section headers
- `ACTION_VERBS` — 45 strong action verbs
- `COMPLEXITY_INDICATORS` — 30 complexity/architecture terms
- `TECH_KEYWORDS` — 40 technology terms
- `SECTION_PATTERNS` — 6 regex patterns for section detection

---

#### `utils/skills.py` — Skill Management

**What it does:** Loads the skills database from `data/skills_list.txt` and matches skills against text using regex word-boundary detection.

**Why it exists:** Centralizes skill definitions so they can be updated in one place (the text file) without touching code.

---

#### `data/skills_list.txt` — Skills Database

**What it does:** A plain-text file with one skill per line, covering programming languages, frameworks, cloud services, data science tools, soft skills, and more (150+ entries).

**Why it exists:** Externalizes the skills list so non-developers (e.g., recruiters, HR) can update it without modifying Python code.

---

## 🔧 Tech Stack — Why Each Library?

| Library | Purpose | Why This Choice? |
|---------|---------|------------------|
| **Streamlit** | Web UI framework | Fastest way to build data apps in Python. No HTML/JS plumbing required. Built-in widgets, layout primitives, and hot-reload. |
| **spaCy** | NLP processing | Industrial-strength NLP with pre-trained pipelines. Used for tokenization, stopword removal, and lemmatization. Faster than NLTK for production use. |
| **scikit-learn** | TF-IDF + similarity | Gold-standard ML library. `TfidfVectorizer` and `cosine_similarity` provide a reliable, interpretable matching algorithm without needing deep learning. |
| **PyPDF2** | PDF parsing | Lightweight, pure-Python PDF reader. No system dependencies (unlike `pdfminer` or `tika`), making deployment simple. |
| **pandas** | Data handling | Industry-standard data manipulation library. Used for structured data operations and available for future analytics features. |

---

## 🚀 Installation

### Prerequisites
- **Python 3.10+** installed
- **pip** package manager

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/resume-analyzer.git
cd resume-analyzer

# 2. (Recommended) Create a virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the spaCy English model
python -m spacy download en_core_web_sm

# 5. Run the application
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📖 Usage Guide

### Step 1: Upload Your Resume
Click the **"Choose your resume"** button and select a PDF file. The app extracts text from all pages automatically.

### Step 2: Paste the Job Description
Copy the full job description from the job posting and paste it into the text area on the right.

### Step 3: Click "Analyze Resume"
Hit the **"🔍 Analyze Resume"** button. The system runs all six analysis dimensions:

1. TF-IDF keyword similarity
2. Skill matching against predefined database
3. Project section quality evaluation
4. Experience section analysis with JD relevance
5. Quantified impact detection
6. Resume structure completeness check

### Step 4: Review the ATS Dashboard

The results dashboard displays:

- **Overall ATS Score** — Large, color-coded card with tier label (Strong / Moderate / Low)
- **Six Progress Bars** — Each dimension with score, color coding (green ≥75, yellow ≥50, red <50), and weight label
- **Skills Analysis** — Matched vs. missing skills as color-coded pills
- **Dimension Feedback** — Four detailed panels with per-dimension feedback items
- **Detected Metrics** — Expandable section showing the quantified achievements found
- **Improvement Suggestions** — Aggregated, prioritized list from all dimensions

### Step 5: Iterate
Update your resume based on the suggestions, re-upload, and re-analyze to track improvement.

---

## 📋 Example Output

For a Python developer resume analyzed against a Machine Learning Engineer job description:

```
┌──────────────────────────────────────────┐
│         Overall ATS Score: 62.4%         │
│           Moderate Match                 │
├──────────────────────────────────────────┤
│ 🎯 Keyword Relevance    68.2%  [███░░]  │
│ 🔧 Skills Match         72.5%  [████░]  │
│ 📂 Project Quality      55.0%  [███░░]  │
│ 💼 Experience            75.0%  [████░]  │
│ 📊 Impact               40.0%  [██░░░]  │
│ 📄 Structure             90.0%  [█████]  │
├──────────────────────────────────────────┤
│ ✅ Matched Skills (8 / 11)               │
│ Python · Pandas · NumPy · Scikit-Learn   │
│ Git · Docker · SQL · Flask               │
├──────────────────────────────────────────┤
│ ❌ Missing Skills (3)                    │
│ TensorFlow · PyTorch · Kubernetes        │
├──────────────────────────────────────────┤
│ 💡 Suggestions                           │
│ • Moderate match — targeted improvements │
│   in weakest areas will boost your score │
│ • Priority: Impact (40%) — add           │
│   quantified achievements                │
│ • Add metrics to project descriptions    │
│ • Mention technologies used in projects  │
│ • Add missing skills: Kubernetes,        │
│   PyTorch, TensorFlow                    │
└──────────────────────────────────────────┘
```

---

## 🧪 Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Resume without a Projects section | Project score = 0, feedback suggests adding one |
| Resume without an Experience section | Experience score = 0, feedback explains the impact |
| No quantified metrics found | Impact score = 10, feedback with XYZ formula tip |
| Empty or image-based PDF | Error message prompting text-based PDF |
| Encrypted PDF | Error message explaining the issue |
| No JD skills detected | Skills score computation safely handles division by zero |
| Missing sections | Structure score reduces proportionally, each missing section listed |

---

## 🔮 Future Improvements

| Feature | Description |
|---------|-------------|
| **ML-Based Scoring** | Train a supervised model on labeled resume-JD pairs for more accurate matching beyond TF-IDF |
| **Multi-Resume Comparison** | Upload multiple resumes and rank candidates against a single JD |
| **ATS Platform Simulation** | Simulate how major ATS platforms (Workday, Greenhouse, Lever) would score the resume |
| **Cover Letter Generator** | Auto-generate a tailored cover letter based on the gap analysis |
| **Skill Recommendations** | Suggest online courses (Coursera, Udemy) for each missing skill |
| **Export to PDF** | Download the analysis report as a formatted PDF |
| **API Endpoint** | Expose the analysis engine as a REST API for integration with other tools |
| **Multi-Language Support** | Analyze resumes in languages beyond English using multilingual spaCy models |

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<p align="center">
  Smart Resume Analyzer v2.0 — Built with Python · Streamlit · spaCy · scikit-learn · PyPDF2
</p>
