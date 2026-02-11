from pathlib import Path
import sys


# Ensure project root is on sys.path so that "agents" can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.research import get_topic
from agents.writer import write_article
from agents.validator import validate

def main():
    topic = get_topic("Static site hosting and developer documentation")

    print("Topic selected:", topic["title"])

    html = write_article(topic)

    if not validate(html):
        print("Validation failed. Aborting.")
        return

    articles_dir = PROJECT_ROOT / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    output_path = articles_dir / f"{topic['slug']}.html"
    output_path.write_text(html)

    print("Article published:", output_path)

if __name__ == "__main__":
    main()