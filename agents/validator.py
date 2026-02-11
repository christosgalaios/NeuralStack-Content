from llm_client import call_ollama

def validate(html: str) -> bool:
    prompt = f"""
You are a strict technical editor.

Rules:
- Must be valid HTML
- Must be at least 900 words
- No marketing language
- No repeated paragraphs
- Neutral technical tone

Reply with ONLY:
PASS
or
FAIL

HTML:
{html}
"""
    verdict = call_ollama(prompt).strip()
    return verdict == "PASS"