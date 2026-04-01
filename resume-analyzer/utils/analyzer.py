"""
analyzer.py — Core Analysis Engine

Provides text preprocessing, TF-IDF-based similarity computation,
missing-skill identification, and context-aware improvement suggestions.
"""

import re
from typing import List, Set, Tuple

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# spaCy model loading — use the small English model for speed.
# If the model is missing, provide a helpful install command.
# ---------------------------------------------------------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise OSError(
        "spaCy model 'en_core_web_sm' is not installed.\n"
        "Run:  python -m spacy download en_core_web_sm"
    )


def preprocess_text(text: str) -> str:
    """
    Clean and normalize raw text for analysis.

    Pipeline:
        1. Convert to lowercase.
        2. Remove URLs, email addresses, and phone numbers.
        3. Remove special characters but keep hyphens in compound words.
        4. Tokenize with spaCy, removing stopwords and punctuation.
        5. Lemmatize remaining tokens for better matching.

    Args:
        text: Raw text string.

    Returns:
        A cleaned, lemmatized string with tokens separated by spaces.
    """
    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove email addresses
    text = re.sub(r"\S+@\S+\.\S+", " ", text)

    # Remove phone numbers (various formats)
    text = re.sub(r"[\+]?[\d\s\-\(\)]{7,15}", " ", text)

    # Remove special characters but keep letters, digits, spaces, and hyphens
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # spaCy tokenization → remove stopwords & punctuation → lemmatize
    doc = nlp(text)
    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop and not token.is_punct and len(token.text) > 1
    ]

    return " ".join(tokens)


def compute_similarity(resume_text: str, jd_text: str) -> float:
    """
    Compute the cosine similarity between a resume and a job description
    using TF-IDF vectorization.

    Both texts are preprocessed before vectorization. The resulting score
    is a float between 0 and 1, where 1 means identical content.

    Args:
        resume_text: Raw (unprocessed) resume text.
        jd_text:     Raw (unprocessed) job description text.

    Returns:
        A similarity score between 0.0 and 1.0.
    """
    # Preprocess both documents
    processed_resume = preprocess_text(resume_text)
    processed_jd = preprocess_text(jd_text)

    # Guard: if either document is empty after preprocessing, similarity is 0
    if not processed_resume.strip() or not processed_jd.strip():
        return 0.0

    # TF-IDF vectorization on the two-document corpus
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([processed_resume, processed_jd])

    # Cosine similarity returns a 2×2 matrix; we want [0][1]
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

    return float(similarity[0][0])


def get_missing_skills(
    resume_skills: Set[str], jd_skills: Set[str]
) -> Set[str]:
    """
    Determine which skills are required by the job description but absent
    from the candidate's resume.

    Args:
        resume_skills: Skills extracted from the resume.
        jd_skills:     Skills extracted from the job description.

    Returns:
        A set of skill strings present in the JD but missing from the resume.
    """
    return jd_skills - resume_skills


def generate_suggestions(
    match_score: float,
    missing_skills: Set[str],
    resume_skills: Set[str],
    jd_skills: Set[str],
) -> List[str]:
    """
    Generate actionable improvement suggestions based on the match score
    and the gap between resume and JD skills.

    Suggestion tiers:
        • < 60%  — Strong suggestions (significant gaps)
        • 60–80% — Moderate suggestions (competitive but improvable)
        • > 80%  — Optimization tips (already strong)

    Args:
        match_score:    Similarity score (0.0–1.0).
        missing_skills: Skills in the JD but not in the resume.
        resume_skills:  Skills found in the resume.
        jd_skills:      Skills found in the JD.

    Returns:
        A list of suggestion strings.
    """
    suggestions: List[str] = []
    pct = match_score * 100

    # ── Strong suggestions (match < 60%) ──────────────────────────────────
    if pct < 60:
        suggestions.append(
            "⚠️ Your resume has a LOW match with this job description. "
            "Consider tailoring it significantly before applying."
        )
        if missing_skills:
            top_missing = sorted(missing_skills)[:10]
            suggestions.append(
                f"🔑 High-priority missing skills to add: "
                f"{', '.join(top_missing)}."
            )
        suggestions.append(
            "📝 Rewrite your summary/objective to mirror the language "
            "used in the job description."
        )
        suggestions.append(
            "📄 Add relevant projects or certifications that demonstrate "
            "the missing skills."
        )
        suggestions.append(
            "🎯 Use keywords from the job description throughout your "
            "experience section."
        )

    # ── Moderate suggestions (60% ≤ match ≤ 80%) ─────────────────────────
    elif pct <= 80:
        suggestions.append(
            "👍 Your resume is a MODERATE match. With some adjustments, "
            "you can significantly improve your chances."
        )
        if missing_skills:
            top_missing = sorted(missing_skills)[:7]
            suggestions.append(
                f"🔧 Consider adding these skills if you have them: "
                f"{', '.join(top_missing)}."
            )
        suggestions.append(
            "💡 Quantify your achievements (e.g., 'Increased efficiency "
            "by 30%') to strengthen your experience section."
        )
        suggestions.append(
            "🔗 Ensure your resume format is ATS-friendly — avoid "
            "tables, images, and unusual fonts."
        )

    # ── Optimization tips (match > 80%) ───────────────────────────────────
    else:
        suggestions.append(
            "🌟 Excellent! Your resume is a STRONG match for this role."
        )
        if missing_skills:
            top_missing = sorted(missing_skills)[:5]
            suggestions.append(
                f"✨ Optional polish — you could mention: "
                f"{', '.join(top_missing)}."
            )
        suggestions.append(
            "🚀 Focus on tailoring your cover letter to stand out "
            "even further."
        )
        suggestions.append(
            "📈 Highlight leadership, impact metrics, and unique "
            "contributions in your most recent role."
        )

    return suggestions
