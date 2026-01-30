"""
SmartHire - Resume Matching System (Week 8)
Compare candidates against job descriptions with scoring (0-100) and reasoning.
"""
from pathlib import Path
import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# ===========================================
# PATHS
# ===========================================
JSON_PATH = PROJECT_ROOT / "data" / "processed" / "resumes_sectioned_json"

# ===========================================
# LLM SETUP (OpenRouter - same as query_resumes)
# ===========================================
llm_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

LLM_MODEL = "deepseek/deepseek-chat"

# ===========================================
# SCORING PROMPT
# ===========================================
SCORING_PROMPT = """You are an expert HR recruiter AI. Compare a candidate's resume against a job description and provide a match score.

SCORING CRITERIA (0-100):
- 90-100: Perfect match - has all required skills and experience
- 75-89: Strong match - has most required skills, minor gaps
- 60-74: Good match - has core skills but missing some requirements  
- 40-59: Partial match - has some relevant skills but significant gaps
- 20-39: Weak match - limited relevant experience
- 0-19: Poor match - does not meet basic requirements

RESPOND IN THIS EXACT JSON FORMAT:
{
    "score": <number 0-100>,
    "summary": "<one sentence overall assessment>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "gaps": ["<missing skill/requirement 1>", "<missing skill/requirement 2>"],
    "reasoning": "<2-3 sentences explaining the score>"
}

RULES:
1. Be objective - base score ONLY on actual skills/experience mentioned
2. Don't assume skills that aren't explicitly stated
3. Penalize missing REQUIRED skills more heavily than nice-to-haves
4. Consider years of experience if mentioned in job description
5. Return ONLY the JSON - no markdown, no extra text"""


# ===========================================
# HELPER: Build resume text
# ===========================================
def build_resume_text(sections: dict) -> str:
    """Build a text representation of a resume for matching."""
    parts = []
    
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
                    exp_text += ": " + "; ".join(responsibilities[:5])
                exp_texts.append(exp_text)
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


# ===========================================
# CORE: Score a single resume against job
# ===========================================
def score_resume(resume_text: str, job_description: str, retries: int = 2) -> dict:
    """
    Score a single resume against a job description.
    Returns dict with score, strengths, gaps, reasoning.
    """
    user_prompt = f"""JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

Analyze how well this candidate matches the job requirements and provide a score (0-100) with detailed reasoning."""

    for attempt in range(retries):
        try:
            response = llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SCORING_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            
            # Validate required fields
            if "score" not in result:
                result["score"] = 50
            if "reasoning" not in result:
                result["reasoning"] = "Unable to generate detailed reasoning."
            if "strengths" not in result:
                result["strengths"] = []
            if "gaps" not in result:
                result["gaps"] = []
            if "summary" not in result:
                result["summary"] = f"Match score: {result['score']}/100"
            
            return result
            
        except json.JSONDecodeError as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return {
                "score": 0,
                "summary": "Error parsing AI response",
                "strengths": [],
                "gaps": ["Could not analyze resume"],
                "reasoning": f"JSON parsing error: {str(e)[:50]}"
            }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return {
                "score": 0,
                "summary": "Error during analysis",
                "strengths": [],
                "gaps": ["Analysis failed"],
                "reasoning": f"Error: {str(e)[:100]}"
            }


# ===========================================
# MAIN: Match all resumes against job
# ===========================================
def match_all_resumes(job_description: str, limit: int = 20, progress_callback=None) -> list[dict]:
    """
    Match all resumes against a job description.
    Returns list of results sorted by score (highest first).
    
    Args:
        job_description: The job description to match against
        limit: Maximum number of resumes to process
        progress_callback: Optional function(current, total) for progress updates
    """
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"No resumes found at {JSON_PATH}")
    
    json_files = sorted(JSON_PATH.glob("*.json"))[:limit]
    
    if not json_files:
        raise ValueError("No resume JSON files found. Run the pipeline first.")
    
    results = []
    total = len(json_files)
    
    for i, json_file in enumerate(json_files):
        try:
            # Load resume
            data = json.loads(json_file.read_text(encoding="utf-8"))
            sections = data.get("sections", {})
            resume_text = build_resume_text(sections)
            
            if not resume_text.strip():
                continue
            
            # Score against job description
            score_result = score_resume(resume_text, job_description)
            
            results.append({
                "candidate_id": json_file.stem,
                "score": score_result.get("score", 0),
                "summary": score_result.get("summary", ""),
                "strengths": score_result.get("strengths", []),
                "gaps": score_result.get("gaps", []),
                "reasoning": score_result.get("reasoning", ""),
                "skills": sections.get("skills", [])
            })
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total)
            
            # Small delay to avoid rate limits
            if i < total - 1:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
            continue
    
    # Sort by score (highest first)
    results.sort(key=lambda x: -x["score"])
    
    return results


def match_top_candidates(job_description: str, n_candidates: int = 10, progress_callback=None) -> list[dict]:
    """
    Smart matching: First use semantic search to find likely matches,
    then score only those candidates (faster than scoring all).
    """
    # Try to use semantic search first for efficiency
    try:
        from query_resumes import search_resumes
        
        # Get top candidates from semantic search (only request what we need)
        search_results = search_resumes(job_description, n_results=n_candidates)
        candidate_ids = [r["id"] for r in search_results]
        
    except Exception:
        # Fallback to processing all
        candidate_ids = None
    
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"No resumes found at {JSON_PATH}")
    
    # Get files to process - exactly n_candidates
    if candidate_ids:
        json_files = [JSON_PATH / f"{cid}.json" for cid in candidate_ids if (JSON_PATH / f"{cid}.json").exists()][:n_candidates]
    else:
        json_files = sorted(JSON_PATH.glob("*.json"))[:n_candidates]
    
    results = []
    total = len(json_files)
    
    for i, json_file in enumerate(json_files):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            sections = data.get("sections", {})
            resume_text = build_resume_text(sections)
            
            if not resume_text.strip():
                continue
            
            score_result = score_resume(resume_text, job_description)
            
            results.append({
                "candidate_id": json_file.stem,
                "score": score_result.get("score", 0),
                "summary": score_result.get("summary", ""),
                "strengths": score_result.get("strengths", []),
                "gaps": score_result.get("gaps", []),
                "reasoning": score_result.get("reasoning", ""),
                "skills": sections.get("skills", [])
            })
            
            if progress_callback:
                progress_callback(i + 1, total)
            
            if i < total - 1:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    results.sort(key=lambda x: -x["score"])
    return results


# ===========================================
# CLI for testing
# ===========================================
if __name__ == "__main__":
    # Example job description for testing
    test_job = """
    Senior Python Developer
    
    Requirements:
    - 5+ years of Python experience
    - Experience with Django or FastAPI
    - Strong SQL and database skills
    - Experience with REST APIs
    - Good communication skills
    
    Nice to have:
    - Machine learning experience
    - Docker/Kubernetes
    - AWS or cloud experience
    """
    
    print("=" * 50)
    print("SmartHire - Resume Matcher")
    print("=" * 50)
    print(f"\nMatching against job description...\n")
    
    results = match_top_candidates(test_job, n_candidates=5)
    
    print(f"\nTop {len(results)} Candidates:\n")
    print("-" * 50)
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Candidate {r['candidate_id']}")
        print(f"   Score: {r['score']}/100")
        print(f"   Summary: {r['summary']}")
        if r['strengths']:
            print(f"   Strengths: {', '.join(r['strengths'][:3])}")
        if r['gaps']:
            print(f"   Gaps: {', '.join(r['gaps'][:3])}")
        print(f"   Reasoning: {r['reasoning'][:200]}...")
