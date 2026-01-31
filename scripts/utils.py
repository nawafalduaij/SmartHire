"""
SmartHire - Shared Utilities
Common functions used across scripts
"""


def build_resume_text(sections: dict, max_responsibilities: int = 5) -> str:
    """
    Build a text representation of a resume from structured sections.
    Used by query_resumes, match_resumes, and build_vector_store.
    
    Args:
        sections: Dict with summary, experience, education, skills, certifications
        max_responsibilities: Max responsibilities to include per job
    
    Returns:
        Formatted text representation of the resume
    """
    parts = []
    
    # Summary
    if sections.get("summary"):
        parts.append(f"SUMMARY: {sections['summary']}")
    
    # Experience
    experience = sections.get("experience", [])
    if experience:
        exp_texts = []
        for exp in experience:
            if isinstance(exp, dict):
                exp_text = f"- {exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get('dates'):
                    exp_text += f" ({exp.get('dates')})"
                responsibilities = exp.get('responsibilities', [])
                if responsibilities:
                    exp_text += ": " + "; ".join(responsibilities[:max_responsibilities])
                exp_texts.append(exp_text)
            else:
                exp_texts.append(f"- {exp}")
        if exp_texts:
            parts.append("EXPERIENCE:\n" + "\n".join(exp_texts))
    
    # Education
    education = sections.get("education", [])
    if education:
        edu_texts = []
        for edu in education:
            if isinstance(edu, dict):
                edu_text = f"- {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}"
                edu_texts.append(edu_text)
            else:
                edu_texts.append(f"- {edu}")
        if edu_texts:
            parts.append("EDUCATION:\n" + "\n".join(edu_texts))
    
    # Skills
    skills = sections.get("skills", [])
    if skills:
        parts.append(f"SKILLS: {', '.join(skills)}")
    
    # Certifications
    certs = sections.get("certifications", [])
    if certs:
        parts.append(f"CERTIFICATIONS: {', '.join(certs)}")
    
    return "\n\n".join(parts)
