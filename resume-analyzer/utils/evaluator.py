"""
evaluator.py — Advanced ATS-Style Resume Evaluation Engine

Provides rule-based analysis across five dimensions:
    1. Project quality
    2. Experience relevance
    3. Impact (quantified achievements)
    4. Resume structure & completeness
    5. Weighted final scoring

Every analyser returns a 0–100 integer score and a list of human-readable
feedback strings so every score is fully explainable.
"""

import re
from typing import Dict, List, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Shared lexicons — kept small and deterministic (no heavy ML)
# ═══════════════════════════════════════════════════════════════════════════════

ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "created", "deployed",
    "engineered", "architected", "optimized", "automated", "integrated",
    "refactored", "configured", "maintained", "managed", "led", "coordinated",
    "launched", "delivered", "established", "improved", "enhanced", "reduced",
    "increased", "scaled", "migrated", "modernized", "streamlined",
    "spearheaded", "pioneered", "contributed", "collaborated", "mentored",
    "analyzed", "tested", "debugged", "resolved", "monitored", "published",
    "trained", "presented", "researched", "proposed", "executed",
}

COMPLEXITY_INDICATORS = {
    "api", "rest", "graphql", "microservice", "microservices", "distributed",
    "scalable", "cloud", "ml", "machine learning", "deep learning", "ai",
    "real-time", "realtime", "pipeline", "etl", "database", "concurrent",
    "multi-threaded", "kubernetes", "docker", "ci/cd", "devops", "system",
    "architecture", "full-stack", "fullstack", "end-to-end", "production",
    "high-availability", "load balancing", "caching", "optimization",
}

TECH_KEYWORDS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "react", "angular", "vue", "node", "django", "flask", "fastapi", "spring",
    "tensorflow", "pytorch", "pandas", "numpy", "docker", "kubernetes", "aws",
    "azure", "gcp", "sql", "mongodb", "redis", "postgresql", "mysql",
    "html", "css", "git", "linux", "firebase", "graphql", "kafka", "spark",
}

# Section header patterns — case-insensitivity is applied via re.IGNORECASE
# at every call site.  Do NOT embed (?i) here; Python 3.11+ rejects inline
# global flags when patterns are joined with |.
SECTION_PATTERNS = {
    "education":  r"\b(education|academic|qualification|degree)\b",
    "skills":     r"\b(skills|technical\s+skills|core\s+competenc|proficienc)\b",
    "projects":   r"\b(projects?|personal\s+projects?|academic\s+projects?)\b",
    "experience": r"\b(experience|work\s+experience|employment|professional\s+experience|internship)\b",
    "summary":    r"\b(summary|objective|profile|about\s+me)\b",
    "certifications": r"\b(certification|certifications|licenses?)\b",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PROJECT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_projects(resume_text: str) -> Dict:
    """
    Evaluate the quality of the Projects section in a resume.

    Scoring rubric (0–100):
        +25  Projects section detected at all
        +25  Technologies/tools mentioned in project descriptions
        +25  Action verbs used (built, developed, implemented …)
        +25  Complexity indicators present (API, scalable, ML …)

    Each component is graded on a sub-scale and combined.

    Returns:
        {
            "score":    int (0–100),
            "feedback": list[str]
        }
    """
    text_lower = resume_text.lower()
    feedback: List[str] = []
    score = 0

    # ── Detect the Projects section ──────────────────────────────────────
    projects_match = re.search(SECTION_PATTERNS["projects"], resume_text, re.IGNORECASE)
    if not projects_match:
        return {
            "score": 0,
            "feedback": [
                "❌ No 'Projects' section detected. Adding a projects section "
                "with 2–3 well-described projects can significantly boost your score."
            ],
        }

    # Extract the text from the Projects heading to the next section heading
    project_text = _extract_section_text(resume_text, "projects")
    project_lower = project_text.lower()
    score += 25  # Section exists
    feedback.append("✅ Projects section detected.")

    # ── Technologies mentioned ───────────────────────────────────────────
    found_techs = {t for t in TECH_KEYWORDS if re.search(rf"\b{re.escape(t)}\b", project_lower)}
    if len(found_techs) >= 4:
        score += 25
        feedback.append(f"✅ Strong tech presence ({len(found_techs)} technologies mentioned).")
    elif len(found_techs) >= 2:
        score += 15
        feedback.append(
            f"⚠️ Moderate tech presence ({len(found_techs)} found). "
            f"List specific technologies for each project."
        )
    elif len(found_techs) >= 1:
        score += 8
        feedback.append("⚠️ Only 1 technology mentioned. Add tech stacks to every project.")
    else:
        feedback.append("❌ No technologies mentioned in projects. Always list the tech stack used.")

    # ── Action verbs ─────────────────────────────────────────────────────
    found_verbs = {v for v in ACTION_VERBS if re.search(rf"\b{re.escape(v)}\b", project_lower)}
    if len(found_verbs) >= 4:
        score += 25
        feedback.append("✅ Excellent use of action verbs in project descriptions.")
    elif len(found_verbs) >= 2:
        score += 15
        feedback.append("⚠️ Use more action verbs (built, developed, implemented) to describe projects.")
    else:
        score += 5
        feedback.append("❌ Very few action verbs. Start project bullets with strong verbs.")

    # ── Complexity indicators ────────────────────────────────────────────
    found_complex = set()
    for indicator in COMPLEXITY_INDICATORS:
        if " " in indicator or "/" in indicator or "-" in indicator:
            if indicator in project_lower:
                found_complex.add(indicator)
        else:
            if re.search(rf"\b{re.escape(indicator)}\b", project_lower):
                found_complex.add(indicator)

    if len(found_complex) >= 3:
        score += 25
        feedback.append("✅ Projects demonstrate strong technical complexity.")
    elif len(found_complex) >= 1:
        score += 12
        feedback.append(
            "⚠️ Add complexity indicators (API, scalable, ML, distributed) "
            "to show real-world impact."
        )
    else:
        feedback.append("❌ No complexity indicators found. Describe the scale and architecture.")

    return {"score": min(score, 100), "feedback": feedback}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. EXPERIENCE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_experience(resume_text: str, jd_text: str = "") -> Dict:
    """
    Evaluate the Experience / Internship section.

    Scoring rubric (0–100):
        +30  Experience section detected
        +25  Action verbs used in descriptions
        +25  Role relevance to job description (keyword overlap)
        +20  Multiple positions / duration indicators

    Returns:
        {
            "score":    int (0–100),
            "feedback": list[str]
        }
    """
    text_lower = resume_text.lower()
    feedback: List[str] = []
    score = 0

    # ── Detect Experience section ────────────────────────────────────────
    if not re.search(SECTION_PATTERNS["experience"], resume_text, re.IGNORECASE):
        return {
            "score": 0,
            "feedback": [
                "❌ No 'Experience' or 'Internship' section detected. "
                "Professional experience is critical for ATS scoring."
            ],
        }

    experience_text = _extract_section_text(resume_text, "experience")
    exp_lower = experience_text.lower()
    score += 30
    feedback.append("✅ Experience section detected.")

    # ── Action verbs ─────────────────────────────────────────────────────
    found_verbs = {v for v in ACTION_VERBS if re.search(rf"\b{re.escape(v)}\b", exp_lower)}
    if len(found_verbs) >= 5:
        score += 25
        feedback.append("✅ Excellent use of action verbs in experience descriptions.")
    elif len(found_verbs) >= 2:
        score += 15
        feedback.append("⚠️ Use more varied action verbs to describe your responsibilities.")
    else:
        score += 5
        feedback.append("❌ Weak action verbs. Start each bullet with a strong verb.")

    # ── Role relevance to JD ─────────────────────────────────────────────
    if jd_text.strip():
        jd_lower = jd_text.lower()
        jd_words = set(re.findall(r"\b[a-z]{3,}\b", jd_lower))
        exp_words = set(re.findall(r"\b[a-z]{3,}\b", exp_lower))
        # Remove ultra-common words
        stopwords = {"the", "and", "for", "with", "you", "are", "will", "have",
                      "that", "this", "from", "our", "about", "your", "their",
                      "has", "been", "not", "but", "can", "all", "was", "were"}
        jd_words -= stopwords
        exp_words -= stopwords
        overlap = jd_words & exp_words
        relevance = len(overlap) / max(len(jd_words), 1)

        if relevance >= 0.25:
            score += 25
            feedback.append("✅ Experience is highly relevant to the job description.")
        elif relevance >= 0.12:
            score += 15
            feedback.append("⚠️ Experience is moderately relevant. Tailor bullet points to the JD.")
        else:
            score += 5
            feedback.append("❌ Experience section has low keyword overlap with the JD.")
    else:
        score += 12  # Neutral when no JD provided
        feedback.append("ℹ️ Provide a JD for experience-relevance scoring.")

    # ── Multiple roles / duration ────────────────────────────────────────
    date_patterns = re.findall(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
        r"january|february|march|april|june|july|august|september|"
        r"october|november|december)\b.{0,10}\b\d{4}\b",
        exp_lower,
    )
    year_ranges = re.findall(r"\b20\d{2}\s*[-–—]\s*(?:20\d{2}|present|current)\b", exp_lower)
    has_duration = len(date_patterns) >= 2 or len(year_ranges) >= 1

    if has_duration:
        score += 20
        feedback.append("✅ Dates and durations are present for roles.")
    else:
        score += 5
        feedback.append("⚠️ Add start/end dates for each role to show career progression.")

    return {"score": min(score, 100), "feedback": feedback}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. IMPACT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_impact(resume_text: str) -> Dict:
    """
    Detect and score quantified achievements and measurable impact.

    Looks for patterns like:
        • "improved performance by 30%"
        • "handled 10k+ users"
        • "reduced costs by $500K"
        • "managed a team of 8"
        • "3x faster"

    Scoring rubric (0–100):
        0 metrics   →  10
        1–2 metrics →  40
        3–4 metrics →  70
        5+ metrics  → 100

    Returns:
        {
            "score":    int (0–100),
            "feedback": list[str],
            "metrics_found": list[str]  — the actual matched phrases
        }
    """
    feedback: List[str] = []
    metrics_found: List[str] = []

    # Patterns that indicate quantified impact
    metric_patterns = [
        # Percentage increases / decreases
        r"(?:improv|increas|reduc|decreas|boost|grew|lower|rais|sav|cut|achiev)\w*\s+"
        r"(?:[\w\s]{0,30}?)\b\d+[\d,]*\.?\d*\s*%",
        # Standalone percentages with context
        r"\b\d{1,3}\.?\d*\s*%\s*(?:improvement|increase|decrease|reduction|growth|accuracy|efficiency)",
        # Dollar / currency amounts
        r"\$\s*\d[\d,]*\.?\d*\s*[kKmMbB]?",
        # Large user / request counts
        r"\b\d[\d,]*\.?\d*\s*[kKmM]?\+?\s*(?:users?|customers?|clients?|requests?|transactions?|downloads?|visits?)",
        # "team of N" patterns
        r"(?:team|group)\s+of\s+\d+",
        # Multiplier patterns (3x, 10x)
        r"\b\d+[xX]\s+(?:faster|slower|improvement|increase|growth|reduction)",
        # General "by N%" or "by N"
        r"by\s+\d[\d,]*\.?\d*\s*%",
        # Numbers with context words
        r"\b\d{2,}[\d,]*\+?\s*(?:projects?|applications?|endpoints?|servers?|databases?|repositories|microservices?)",
    ]

    for pattern in metric_patterns:
        matches = re.findall(pattern, resume_text, re.IGNORECASE)
        for m in matches:
            cleaned = m.strip()
            if cleaned and cleaned not in metrics_found:
                metrics_found.append(cleaned)

    count = len(metrics_found)

    if count == 0:
        score = 10
        feedback.append(
            "❌ No quantified achievements found. Add measurable impact "
            "(e.g., 'Improved API response time by 40%')."
        )
        feedback.append(
            "💡 Tip: Use the XYZ formula — 'Accomplished [X] as measured by [Y] "
            "by doing [Z]'."
        )
    elif count <= 2:
        score = 40
        feedback.append(
            f"⚠️ Found {count} quantified metric(s) — aim for at least 4–5 "
            "across your resume."
        )
        feedback.append("💡 Add metrics to your top 2–3 achievements in each role.")
    elif count <= 4:
        score = 70
        feedback.append(f"👍 Good — {count} quantified metrics found.")
        feedback.append("💡 Consider adding metrics to remaining bullet points for a perfect score.")
    else:
        score = 100
        feedback.append(f"🌟 Excellent — {count} quantified achievements detected!")

    return {"score": score, "feedback": feedback, "metrics_found": metrics_found}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. STRUCTURE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_structure(resume_text: str) -> Dict:
    """
    Evaluate resume completeness by checking for expected sections.

    Required sections and their weights:
        Education       — 20
        Skills          — 25
        Projects        — 20
        Experience      — 25
        Summary         — 10

    Returns:
        {
            "score":            int (0–100),
            "feedback":         list[str],
            "found_sections":   list[str],
            "missing_sections": list[str]
        }
    """
    section_weights = {
        "education":  20,
        "skills":     25,
        "projects":   20,
        "experience": 25,
        "summary":    10,
    }

    found_sections: List[str] = []
    missing_sections: List[str] = []
    feedback: List[str] = []
    score = 0

    for section, weight in section_weights.items():
        pattern = SECTION_PATTERNS.get(section, "")
        if re.search(pattern, resume_text, re.IGNORECASE):
            found_sections.append(section)
            score += weight
        else:
            missing_sections.append(section)

    if score == 100:
        feedback.append("🌟 Resume has all key sections — excellent structure!")
    elif score >= 70:
        feedback.append("👍 Good structure — most key sections are present.")
    else:
        feedback.append("⚠️ Resume is missing important sections.")

    for ms in missing_sections:
        label = ms.replace("_", " ").title()
        feedback.append(f"❌ Missing section: {label}")

    for fs in found_sections:
        label = fs.replace("_", " ").title()
        feedback.append(f"✅ Found: {label}")

    return {
        "score": score,
        "feedback": feedback,
        "found_sections": found_sections,
        "missing_sections": missing_sections,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FINAL WEIGHTED SCORE
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_final_score(
    similarity_score: float,
    skills_score: float,
    project_score: float,
    experience_score: float,
    impact_score: float,
    structure_score: float,
) -> Dict:
    """
    Compute the weighted ATS final score.

    Weights:
        Keyword Similarity  — 30 %
        Skills Match        — 20 %
        Project Quality     — 20 %
        Experience          — 15 %
        Impact              — 10 %
        Structure           — 5 %

    All input scores are expected on a 0–100 scale.

    Returns:
        {
            "final_score": float (0–100, 1 decimal),
            "breakdown": dict[str, float],
            "tier": str ("Strong" / "Moderate" / "Low"),
            "feedback": list[str]
        }
    """
    weights = {
        "Keyword Relevance":  0.30,
        "Skills Match":       0.20,
        "Project Quality":    0.20,
        "Experience":         0.15,
        "Impact":             0.10,
        "Structure":          0.05,
    }

    raw_scores = {
        "Keyword Relevance":  similarity_score,
        "Skills Match":       skills_score,
        "Project Quality":    project_score,
        "Experience":         experience_score,
        "Impact":             impact_score,
        "Structure":          structure_score,
    }

    weighted_total = sum(
        raw_scores[k] * weights[k] for k in weights
    )

    final = round(weighted_total, 1)

    breakdown = {
        k: round(raw_scores[k], 1) for k in weights
    }

    if final >= 75:
        tier = "Strong"
    elif final >= 50:
        tier = "Moderate"
    else:
        tier = "Low"

    feedback: List[str] = []
    if final >= 75:
        feedback.append(
            "🌟 Your resume is a strong match. Focus on fine-tuning and "
            "crafting a compelling cover letter."
        )
    elif final >= 50:
        feedback.append(
            "👍 Moderate match — targeted improvements in your weakest "
            "categories can push you into the strong tier."
        )
    else:
        feedback.append(
            "⚠️ Low overall match. Significant tailoring is needed "
            "before submitting this resume."
        )

    # Identify weakest areas
    sorted_scores = sorted(raw_scores.items(), key=lambda x: x[1])
    for name, val in sorted_scores[:2]:
        if val < 50:
            feedback.append(f"🔑 Priority improvement area: {name} ({val:.0f}%)")

    return {
        "final_score": final,
        "breakdown": breakdown,
        "tier": tier,
        "feedback": feedback,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: extract the text belonging to a specific section
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_section_text(resume_text: str, section_key: str) -> str:
    """
    Extract the text between a section header and the next section header.

    Uses the SECTION_PATTERNS dict to locate the start of `section_key`,
    then scans forward until it hits another known section header or the end
    of the document.

    Args:
        resume_text: Full resume text.
        section_key: Key from SECTION_PATTERNS (e.g. "projects").

    Returns:
        The body text of that section (may be empty).
    """
    pattern = SECTION_PATTERNS.get(section_key)
    if not pattern:
        return ""

    match = re.search(pattern, resume_text, re.IGNORECASE)
    if not match:
        return ""

    start = match.end()

    # Build a combined pattern of ALL other section headers
    other_patterns = [
        p for k, p in SECTION_PATTERNS.items() if k != section_key
    ]
    combined = "|".join(other_patterns)

    next_section = re.search(combined, resume_text[start:], re.IGNORECASE)
    if next_section:
        end = start + next_section.start()
    else:
        end = len(resume_text)

    return resume_text[start:end].strip()
