"""
SmartHire - Resume Query System
Query ChromaDB and answer questions about candidates using RAG
Works for any industry - not just IT
"""
from pathlib import Path
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# ===========================================
# PATHS
# ===========================================
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma_db"
JSON_PATH = PROJECT_ROOT / "data" / "processed" / "resumes_sectioned_json"

# ===========================================
# CHROMADB SETUP
# ===========================================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def get_vector_store():
    """Get the ChromaDB vector store."""
    if not CHROMA_PATH.exists():
        raise FileNotFoundError(f"ChromaDB not found at {CHROMA_PATH}. Run build_vector_store.py first!")
    
    return Chroma(
        persist_directory=str(CHROMA_PATH),
        embedding_function=embeddings
    )

# ===========================================
# LLM SETUP (OpenRouter)
# ===========================================
llm_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# OpenRouter models
LLM_MODEL = "deepseek/deepseek-chat"

# ===========================================
# HELPER: Build full resume text from JSON
# ===========================================

def build_resume_text(sections: dict) -> str:
    """Build a comprehensive text representation of a resume."""
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
                    exp_text += ": " + "; ".join(responsibilities[:3])
                exp_texts.append(exp_text)
            else:
                exp_texts.append(f"- {exp}")
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
# SEARCH: By keywords in skills/content
# ===========================================

def extract_keywords(query: str) -> list[str]:
    """Extract meaningful keywords from a query (2+ characters, not stop words)."""
    stop_words = {"show", "me", "find", "with", "the", "and", "or", "a", "an", "is", 
                  "are", "has", "have", "who", "what", "where", "when", "candidates",
                  "experience", "skills", "any", "all", "some", "looking", "for", "need"}
    
    # Extract words (including multi-word phrases in quotes)
    words = re.findall(r'"([^"]+)"|(\b\w+\b)', query.lower())
    keywords = []
    
    for match in words:
        word = match[0] if match[0] else match[1]
        if word and len(word) >= 2 and word not in stop_words:
            keywords.append(word)
    
    return keywords


def search_by_keywords(keywords: list[str], limit: int = 10) -> list[dict]:
    """
    Search for candidates matching any of the keywords in their skills or content.
    Works for any industry/field.
    """
    matches = []
    
    if not JSON_PATH.exists() or not keywords:
        return []
    
    for json_file in JSON_PATH.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            sections = data.get("sections", {})
            
            # Build searchable text
            full_text = build_resume_text(sections).lower()
            skills = [s.lower() for s in sections.get("skills", [])]
            
            # Check for keyword matches
            matched_keywords = []
            for kw in keywords:
                # Check in skills first (more precise)
                skill_match = any(kw in skill or skill in kw for skill in skills)
                # Then check in full text
                text_match = kw in full_text
                
                if skill_match or text_match:
                    matched_keywords.append(kw)
            
            if matched_keywords:
                content = build_resume_text(sections)
                matches.append({
                    "id": json_file.stem,
                    "content": content,
                    "matched_keywords": matched_keywords,
                    "score": len(matched_keywords) / len(keywords),  # Score by match ratio
                    "match_type": "exact"
                })
        except Exception:
            continue
    
    # Sort by score (most keyword matches first)
    matches.sort(key=lambda x: -x["score"])
    return matches[:limit]


def search_resumes(query: str, n_results: int = 5) -> list[dict]:
    """
    Hybrid search: combines keyword matching with semantic search.
    Returns deduplicated results.
    """
    all_matches = []
    seen_ids = set()
    
    # Step 1: Extract keywords and search for exact matches
    keywords = extract_keywords(query)
    
    if keywords:
        exact_matches = search_by_keywords(keywords, limit=n_results)
        for match in exact_matches:
            if match["id"] not in seen_ids:
                seen_ids.add(match["id"])
                all_matches.append(match)
    
    # Step 2: Semantic search to find more matches
    if len(all_matches) < n_results:
        try:
            db = get_vector_store()
            semantic_results = db.similarity_search_with_score(query, k=n_results * 3)
            
            for doc, score in semantic_results:
                candidate_id = doc.metadata.get("source_file", "unknown").replace(".json", "")
                
                if candidate_id in seen_ids:
                    continue
                
                seen_ids.add(candidate_id)
                all_matches.append({
                    "id": candidate_id,
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 1 / (1 + score),
                    "match_type": "semantic"
                })
                
                if len(all_matches) >= n_results:
                    break
        except Exception as e:
            print(f"Semantic search error: {e}")
    
    # Sort: exact matches first, then by score
    all_matches.sort(key=lambda x: (x.get("match_type") != "exact", -x["score"]))
    
    return all_matches[:n_results]


def answer_question(question: str, n_results: int = 5) -> dict:
    """
    Answer a question about resumes using RAG.
    """
    # Step 1: Retrieve relevant resumes
    try:
        matches = search_resumes(question, n_results=n_results)
    except FileNotFoundError as e:
        return {
            "answer": str(e),
            "sources": [],
            "num_results": 0
        }
    
    if not matches:
        return {
            "answer": "No matching resumes found. Try different search terms.",
            "sources": [],
            "num_results": 0
        }
    
    # Step 2: Build context from retrieved resumes
    context_parts = []
    for i, match in enumerate(matches, 1):
        resume_id = match["id"]
        content = match["content"]
        match_type = match.get("match_type", "semantic")
        
        matched_kw = match.get("matched_keywords", [])
        if matched_kw:
            marker = f"[MATCHED: {', '.join(matched_kw)}]"
        else:
            marker = "[SEMANTIC MATCH]"
        
        context_parts.append(f"--- Resume {i} (ID: {resume_id}) {marker} ---\n{content}")
    
    context = "\n\n".join(context_parts)
    
    # Step 3: Ask LLM with context
    system_prompt = """You are an AI recruitment assistant for SmartHire. 
Answer questions about candidate resumes accurately based on the provided context.

RULES:
1. Only use information from the provided resume context
2. If the information isn't in the context, say so clearly
3. Be specific - mention candidate IDs when referring to specific people
4. For yes/no questions, give a clear answer then explain
5. List specific candidates that match the criteria"""

    user_prompt = f"""Based on the following resume data, answer this question:

QUESTION: {question}

RESUME CONTEXT:
{context}

Provide a clear, helpful answer listing the relevant candidates."""

    try:
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        
    except Exception as e:
        answer = f"Error getting AI response: {e}"
    
    return {
        "answer": answer,
        "sources": [
            {
                "id": m["id"], 
                "score": m["score"],
                "match_type": m.get("match_type", "semantic"),
                "matched_keywords": m.get("matched_keywords", [])
            } for m in matches
        ],
        "num_results": len(matches)
    }


# ===========================================
# INTERACTIVE CLI
# ===========================================

def interactive_mode():
    """Run interactive Q&A mode for testing."""
    print("=" * 50)
    print("SmartHire - Resume Query System")
    print("=" * 50)
    print("Ask questions about candidates in the database.")
    print("Type 'quit' to exit.\n")
    
    while True:
        question = input("Your question: ").strip()
        
        if question.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        print("\nSearching resumes...")
        result = answer_question(question)
        
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources ({result['num_results']} resumes found):")
        for src in result["sources"]:
            match_type = src.get("match_type", "semantic")
            matched = src.get("matched_keywords", [])
            if matched:
                print(f"   - {src['id']} [MATCHED: {', '.join(matched)}]")
            else:
                print(f"   - {src['id']} [SEMANTIC] (score: {src['score']:.2f})")
        print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    interactive_mode()
