"""
app.py — Smart Resume Analyzer v2.0 (ATS-Style Evaluation Dashboard)

A production-quality web application that evaluates a candidate's resume
against a job description across six dimensions:
    1. Keyword Relevance (TF-IDF cosine similarity)
    2. Skills Match     (predefined skills database)
    3. Project Quality  (tech stack, action verbs, complexity)
    4. Experience       (relevance, verbs, dates)
    5. Impact           (quantified achievements)
    6. Structure        (section completeness)

Run with:  streamlit run app.py
"""

import streamlit as st

from utils.parser import extract_text_from_pdf
from utils.skills import load_skills, extract_skills
from utils.analyzer import compute_similarity, get_missing_skills
from utils.evaluator import (
    analyze_projects,
    analyze_experience,
    analyze_impact,
    analyze_structure,
    calculate_final_score,
)


# ══════════════════════════════════════════════════════════════════════════════
# Page configuration
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Smart Resume Analyzer — ATS Evaluation",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# Custom CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    /* ── Typography ──────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Hero ────────────────────────────────────────────────────────────── */
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.2rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.30);
    }
    .hero h1 { color:#fff; font-size:2.5rem; font-weight:800; margin:0; letter-spacing:-0.5px; }
    .hero p  { color:rgba(255,255,255,0.88); font-size:1.1rem; margin-top:0.4rem; }

    /* ── Overall score ring ──────────────────────────────────────────────── */
    .overall-card {
        border-radius: 18px;
        padding: 2rem 1.5rem;
        text-align: center;
        box-shadow: 0 6px 28px rgba(0,0,0,0.10);
        margin-bottom: 1.2rem;
    }
    .overall-card.tier-strong   { background: linear-gradient(135deg,#11998e,#38ef7d); }
    .overall-card.tier-moderate { background: linear-gradient(135deg,#f2994a,#f2c94c); }
    .overall-card.tier-low      { background: linear-gradient(135deg,#eb3349,#f45c43); }
    .overall-val { font-size:4.2rem; font-weight:800; color:#fff; line-height:1; }
    .overall-lbl { font-size:1.1rem; font-weight:600; color:rgba(255,255,255,0.92); margin-top:0.4rem; }

    /* ── Dimension card ──────────────────────────────────────────────────── */
    .dim-card {
        background: #ffffff;
        border: 1px solid #e8ecf1;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 0.9rem;
    }
    .dim-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: #3d3d56;
        margin-bottom: 0.5rem;
    }
    .dim-score {
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }

    /* ── Progress bar ────────────────────────────────────────────────────── */
    .pbar-track {
        background: #edf0f7;
        border-radius: 8px;
        height: 12px;
        overflow: hidden;
    }
    .pbar-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.5s ease;
    }
    .pbar-green  { background: linear-gradient(90deg,#11998e,#38ef7d); }
    .pbar-yellow { background: linear-gradient(90deg,#f2994a,#f2c94c); }
    .pbar-red    { background: linear-gradient(90deg,#eb3349,#f45c43); }

    /* ── Skill pills ─────────────────────────────────────────────────────── */
    .pill { display:inline-block; padding:5px 13px; border-radius:20px; font-size:0.82rem; font-weight:500; margin:3px; }
    .pill-ok   { background:#e6f9f0; color:#0d7a3e; border:1px solid #b8f0d5; }
    .pill-miss { background:#fde8e8; color:#b91c1c; border:1px solid #fbc4c4; }

    /* ── Suggestion item ─────────────────────────────────────────────────── */
    .sug-item {
        background: #f8f9fd;
        border-left: 4px solid #667eea;
        padding: 10px 14px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 8px;
        font-size: 0.92rem;
        color: #2d2d3f;
    }

    /* ── Feedback item ───────────────────────────────────────────────────── */
    .fb-item {
        padding: 6px 0;
        font-size: 0.9rem;
        color: #3d3d56;
        border-bottom: 1px solid #f0f0f5;
    }
    .fb-item:last-child { border-bottom: none; }

    /* ── Sidebar ─────────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] * { color: #e0e0e0 !important; }

    /* ── Footer ──────────────────────────────────────────────────────────── */
    .footer {
        text-align:center; color:#9ca3af; font-size:0.82rem;
        margin-top:3rem; padding:1rem 0; border-top:1px solid #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# Helper: colour-coded progress bar HTML
# ══════════════════════════════════════════════════════════════════════════════
def _pbar(score: float) -> str:
    """Return an HTML progress bar colour-coded by score tier."""
    if score >= 75:
        cls = "pbar-green"
    elif score >= 50:
        cls = "pbar-yellow"
    else:
        cls = "pbar-red"
    return (
        f'<div class="pbar-track">'
        f'<div class="pbar-fill {cls}" style="width:{score}%"></div>'
        f'</div>'
    )


def _score_color(score: float) -> str:
    """Return a hex colour string for a score value."""
    if score >= 75:
        return "#0d7a3e"
    elif score >= 50:
        return "#c27a00"
    else:
        return "#b91c1c"


# ══════════════════════════════════════════════════════════════════════════════
# Hero
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="hero">
        <h1>📄 Smart Resume Analyzer</h1>
        <p>ATS-Style Evaluation · 6-Dimension Scoring · Actionable Insights</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚀 How It Works")
    st.markdown(
        """
        1. **Upload** your resume as a PDF.
        2. **Paste** the target job description.
        3. Click **Analyze Resume**.
        4. Review your **6-dimension ATS score**.
        """
    )
    st.markdown("---")
    st.markdown("## 📊 Scoring Weights")
    st.markdown(
        """
        | Dimension | Weight |
        |-----------|--------|
        | Keyword Relevance | 30 % |
        | Skills Match | 20 % |
        | Project Quality | 20 % |
        | Experience | 15 % |
        | Impact | 10 % |
        | Structure | 5 % |
        """
    )
    st.markdown("---")
    st.markdown("## 🛠️ Powered By")
    st.markdown(
        """
        - **spaCy** — NLP processing
        - **scikit-learn** — TF-IDF similarity
        - **PyPDF2** — PDF extraction
        """
    )
    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.8rem; opacity:0.6;">Smart Resume Analyzer v2.0</p>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Input section
# ══════════════════════════════════════════════════════════════════════════════
col_upload, col_jd = st.columns(2, gap="large")

with col_upload:
    st.markdown("### 📎 Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose your resume (PDF only)", type=["pdf"],
        help="Upload the resume you want to analyze.",
    )

with col_jd:
    st.markdown("### 📝 Job Description")
    job_description = st.text_area(
        "Paste the job description here", height=250,
        placeholder="Copy and paste the full job description…",
    )

st.markdown("")

analyze_clicked = st.button("🔍  Analyze Resume", use_container_width=True, type="primary")


# ══════════════════════════════════════════════════════════════════════════════
# Analysis pipeline
# ══════════════════════════════════════════════════════════════════════════════
if analyze_clicked:
    if uploaded_file is None:
        st.error("⚡ Please upload a PDF resume.")
        st.stop()
    if not job_description.strip():
        st.error("⚡ Please paste a job description.")
        st.stop()

    with st.spinner("Running 6-dimension ATS analysis — this may take a moment…"):

        # 1 — Extract resume text
        try:
            resume_text = extract_text_from_pdf(uploaded_file)
        except (ValueError, RuntimeError) as e:
            st.error(f"❌ {e}")
            st.stop()

        if not resume_text.strip():
            st.error(
                "❌ Could not extract text from the PDF. "
                "The file may be image-based."
            )
            st.stop()

        # 2 — Skills analysis
        try:
            skills_list = load_skills()
        except FileNotFoundError as e:
            st.error(f"❌ {e}")
            st.stop()

        resume_skills = extract_skills(resume_text, skills_list)
        jd_skills = extract_skills(job_description, skills_list)
        matched_skills = resume_skills & jd_skills
        missing_skills = get_missing_skills(resume_skills, jd_skills)

        # Skills score = % of JD skills covered (0–100)
        skills_score = round(
            (len(matched_skills) / max(len(jd_skills), 1)) * 100, 1
        )

        # 3 — Keyword relevance (TF-IDF cosine similarity → 0–100)
        similarity_raw = compute_similarity(resume_text, job_description)
        keyword_score = round(similarity_raw * 100, 1)

        # 4 — Project analysis
        project_result = analyze_projects(resume_text)
        project_score = project_result["score"]

        # 5 — Experience analysis
        experience_result = analyze_experience(resume_text, job_description)
        experience_score = experience_result["score"]

        # 6 — Impact analysis
        impact_result = analyze_impact(resume_text)
        impact_score = impact_result["score"]

        # 7 — Structure analysis
        structure_result = analyze_structure(resume_text)
        structure_score = structure_result["score"]

        # 8 — Weighted final score
        final_result = calculate_final_score(
            similarity_score=keyword_score,
            skills_score=skills_score,
            project_score=project_score,
            experience_score=experience_score,
            impact_score=impact_score,
            structure_score=structure_score,
        )
        final_score = final_result["final_score"]
        tier = final_result["tier"]

    # ══════════════════════════════════════════════════════════════════════
    # RESULTS DASHBOARD
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## 📊 ATS Evaluation Results")

    # ── Row 1: Overall score + breakdown bars ────────────────────────────
    r1_left, r1_right = st.columns([1, 2], gap="large")

    tier_cls = {
        "Strong": "tier-strong", "Moderate": "tier-moderate", "Low": "tier-low"
    }[tier]

    with r1_left:
        st.markdown(
            f"""
            <div class="overall-card {tier_cls}">
                <div class="overall-val">{final_score}%</div>
                <div class="overall-lbl">Overall ATS Score — {tier} Match</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Dimension data for the bar chart column
    dimensions = [
        ("🎯 Keyword Relevance", keyword_score,   "30%"),
        ("🔧 Skills Match",      skills_score,     "20%"),
        ("📂 Project Quality",   project_score,    "20%"),
        ("💼 Experience",        experience_score, "15%"),
        ("📊 Impact",            impact_score,     "10%"),
        ("📄 Structure",         structure_score,  "5%"),
    ]

    with r1_right:
        for label, sc, wt in dimensions:
            st.markdown(
                f"""
                <div class="dim-card">
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span class="dim-title">{label}</span>
                        <span style="font-size:0.78rem; color:#9ca3af;">weight {wt}</span>
                    </div>
                    <div class="dim-score" style="color:{_score_color(sc)};">{sc}%</div>
                    {_pbar(sc)}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Row 2: Skills pills ──────────────────────────────────────────────
    st.markdown("### 🔧 Skills Analysis")
    sk_col1, sk_col2 = st.columns(2, gap="large")

    with sk_col1:
        st.markdown(
            '<div class="dim-card"><div class="dim-title">'
            f'✅ Matched Skills ({len(matched_skills)} / {len(jd_skills)})</div>',
            unsafe_allow_html=True,
        )
        if matched_skills:
            pills = "".join(
                f'<span class="pill pill-ok">{s.title()}</span>'
                for s in sorted(matched_skills)
            )
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.info("No overlapping skills detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    with sk_col2:
        st.markdown(
            '<div class="dim-card"><div class="dim-title">'
            f'❌ Missing Skills ({len(missing_skills)})</div>',
            unsafe_allow_html=True,
        )
        if missing_skills:
            pills = "".join(
                f'<span class="pill pill-miss">{s.title()}</span>'
                for s in sorted(missing_skills)
            )
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.success("🎉 Your resume covers all JD skills!")
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Row 3: Dimension feedback panels ─────────────────────────────────
    st.markdown("### 📋 Detailed Dimension Feedback")

    fb_panels = [
        ("📂 Project Quality",   project_result["feedback"]),
        ("💼 Experience",        experience_result["feedback"]),
        ("📊 Impact Analysis",   impact_result["feedback"]),
        ("📄 Resume Structure",  structure_result["feedback"]),
    ]

    fb_col1, fb_col2 = st.columns(2, gap="large")

    for idx, (title, items) in enumerate(fb_panels):
        col = fb_col1 if idx % 2 == 0 else fb_col2
        with col:
            st.markdown(f'<div class="dim-card"><div class="dim-title">{title}</div>', unsafe_allow_html=True)
            for item in items:
                st.markdown(f'<div class="fb-item">{item}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Row 4: Impact metrics found ──────────────────────────────────────
    if impact_result.get("metrics_found"):
        with st.expander("📊 Quantified Metrics Detected"):
            for m in impact_result["metrics_found"]:
                st.markdown(f"- `{m.strip()}`")

    # ── Row 5: Aggregated suggestions ────────────────────────────────────
    st.markdown("### 💡 Improvement Suggestions")

    # Collect all suggestions from every dimension
    all_suggestions: list[str] = []
    all_suggestions.extend(final_result["feedback"])

    # Pull top actionable items from dimension feedback
    for fb_list in [
        project_result["feedback"],
        experience_result["feedback"],
        impact_result["feedback"],
        structure_result["feedback"],
    ]:
        for fb in fb_list:
            # Only add warning / error items to the suggestions panel
            if fb.startswith(("⚠️", "❌", "💡", "🔑")):
                all_suggestions.append(fb)

    # Add skill-related suggestions
    if missing_skills:
        top_missing = sorted(missing_skills)[:8]
        all_suggestions.append(
            f"🔧 Add these missing skills if applicable: {', '.join(t.title() for t in top_missing)}."
        )

    # De-duplicate while preserving order
    seen = set()
    unique_suggestions = []
    for s in all_suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)

    for sug in unique_suggestions:
        st.markdown(f'<div class="sug-item">{sug}</div>', unsafe_allow_html=True)

    # ── Row 6: Detailed skill breakdown ──────────────────────────────────
    with st.expander("📋 Full Skills Breakdown"):
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.markdown("**All Resume Skills**")
            for s in sorted(resume_skills):
                marker = "✅" if s in jd_skills else "➖"
                st.markdown(f"- {marker} {s.title()}")
            st.markdown(f"**Total:** {len(resume_skills)} ({len(matched_skills)} match JD)")
        with d_col2:
            st.markdown("**JD Required Skills**")
            for s in sorted(jd_skills):
                marker = "✅" if s in resume_skills else "❌"
                st.markdown(f"- {marker} {s.title()}")
            st.markdown(
                f"**Total:** {len(jd_skills)} required "
                f"({len(matched_skills)} matched, {len(missing_skills)} missing)"
            )

    # ── Extracted text preview ───────────────────────────────────────────
    with st.expander("📄 Preview Extracted Resume Text"):
        st.text(resume_text[:3000] + ("…" if len(resume_text) > 3000 else ""))


# ══════════════════════════════════════════════════════════════════════════════
# Footer
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="footer">'
    "Smart Resume Analyzer v2.0 — Built with Streamlit · spaCy · scikit-learn · PyPDF2"
    "</div>",
    unsafe_allow_html=True,
)
