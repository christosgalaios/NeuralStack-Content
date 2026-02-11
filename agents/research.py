from llm_client import call_ollama

def get_topic(seed: str) -> dict:
    prompt = f"""
You are a technical research agent.

Your task:
- Propose ONE evergreen technical article topic
- Narrow in scope
- High informational intent
- No marketing language
- No news or trends

Seed niche:
{seed}

Reply ONLY in this exact JSON format:

{{
  "slug": "kebab-case-url-slug",
  "title": "Exact article title",
  "description": "One sentence meta description"
}}
"""
    response = call_ollama(prompt)

    import json
    return json.loads(response)