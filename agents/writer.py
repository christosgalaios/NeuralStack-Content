from llm_client import call_ollama
from pathlib import Path

TEMPLATE = Path("templates/article.html").read_text()

def write_article(topic: dict) -> str:
    prompt = f"""
You are a senior technical writer.

Write a long-form technical article in pure HTML.

Constraints:
- Output ONLY valid HTML
- No markdown
- No emojis
- One <h1>, multiple <h2>
- 1,000–1,500 words
- Neutral, factual tone
- No speculation
- No marketing language

Title:
{topic["title"]}

Meta description:
{topic["description"]}
"""

    html_body = call_ollama(prompt)

    return html_body