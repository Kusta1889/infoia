"""
Article Categorizer
Classifies articles into predefined categories.
"""

from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Article:
    """Represents a single news article."""
    id: str
    title: str
    url: str
    source: str
    category: str
    published: any
    summary: str
    content: str = None
    author: str = None


# Category definitions with keywords (priority = order of display)
CATEGORIES = {
    "📰 Noticias de Industria": {
        "priority": 1,  # FIRST
        "keywords": [
            "funding", "investment", "acquisition", "partnership",
            "million", "billion", "startup", "company", "ceo",
            "regulation", "policy", "government", "law",
            "inversión", "empresa", "regulación"
        ],
        "sources": ["TechCrunch", "VentureBeat", "MIT Tech Review", "The Decoder", "The Verge"]
    },
    "🚀 Lanzamientos de Modelos": {
        "priority": 2,
        "keywords": [
            "launch", "release", "announce", "new model", "introducing",
            "gpt-5", "gpt-4", "claude", "gemini", "llama", "mistral",
            "update", "version", "v2", "v3", "upgrade",
            "lanzamiento", "nuevo modelo", "actualización"
        ],
        "sources": ["OpenAI", "Anthropic", "DeepMind", "LLM Tracker"]
    },
    "📊 Benchmarks & Rankings": {
        "priority": 3,
        "keywords": [
            "benchmark", "leaderboard", "ranking", "comparison",
            "performance", "score", "evaluation", "test",
            "arena", "elo", "rating"
        ],
        "sources": ["Artificial Analysis", "LMArena"]
    },
    "🛠️ Herramientas & APIs": {
        "priority": 4,
        "keywords": [
            "api", "tool", "library", "framework", "sdk",
            "open source", "github", "huggingface", "model",
            "integration", "plugin", "extension",
            "herramienta", "librería"
        ],
        "sources": ["HuggingFace Models", "Hugging Face Blog"]
    },
    "🇪🇸 En Español": {
        "priority": 5,
        "keywords": [],  # Determined by source
        "sources": ["Xataka"]
    },
    "📄 Research & Papers": {
        "priority": 6,  # LAST
        "keywords": [
            "paper", "research", "study", "arxiv", "conference",
            "neural", "transformer", "attention", "benchmark",
            "training", "fine-tune", "dataset", "evaluation",
            "investigación", "estudio"
        ],
        "sources": ["arXiv", "HuggingFace Papers", "BAIR", "Paper Digest"]
    },
}


class Categorizer:
    """Categorizes articles based on content and source."""
    
    def __init__(self):
        self.categories = CATEGORIES
    
    def _score_category(self, article: Article, category_name: str) -> int:
        """Score how well an article matches a category."""
        category = self.categories[category_name]
        score = 0
        
        # Check source match (high weight)
        for source_pattern in category["sources"]:
            if source_pattern.lower() in article.source.lower():
                score += 100
                break
        
        # Check keyword matches in title and summary
        text = f"{article.title} {article.summary}".lower()
        
        for keyword in category["keywords"]:
            if keyword.lower() in text:
                score += 10
        
        return score
    
    def categorize_article(self, article: Article) -> str:
        """Assign the best category to an article."""
        # If article already has a category from source, validate it
        if article.category and article.category in self.categories:
            return article.category
        
        # Score each category
        scores = {}
        for category_name in self.categories:
            scores[category_name] = self._score_category(article, category_name)
        
        # Return highest scoring category (with priority tiebreaker)
        best_category = max(
            scores.keys(),
            key=lambda c: (scores[c], -self.categories[c]["priority"])
        )
        
        # Default to industry news if no good match
        if scores[best_category] == 0:
            return "📰 Noticias de Industria"
        
        return best_category
    
    def categorize_all(self, articles: List[Article]) -> List[Article]:
        """Categorize all articles."""
        for article in articles:
            article.category = self.categorize_article(article)
        return articles
    
    def group_by_category(self, articles: List[Article]) -> Dict[str, List[Article]]:
        """Group articles by category, sorted by priority."""
        # First categorize
        articles = self.categorize_all(articles)
        
        # Group
        groups = defaultdict(list)
        for article in articles:
            groups[article.category].append(article)
        
        # Sort each group by publication date (newest first)
        for category in groups:
            groups[category].sort(key=lambda a: a.published, reverse=True)
        
        # Return ordered dict by category priority
        ordered = {}
        for category in sorted(
            self.categories.keys(),
            key=lambda c: self.categories[c]["priority"]
        ):
            if category in groups:
                ordered[category] = groups[category]
        
        return ordered


# Convenience functions
def categorize_articles(articles: List[Article]) -> List[Article]:
    """Categorize all articles."""
    return Categorizer().categorize_all(articles)


def group_articles_by_category(articles: List[Article]) -> Dict[str, List[Article]]:
    """Group articles by category."""
    return Categorizer().group_by_category(articles)


if __name__ == "__main__":
    # Test
    test_articles = [
        Article(
            id="1", title="OpenAI announces GPT-5", url="", 
            source="OpenAI Blog", category="", published=None, summary=""
        ),
        Article(
            id="2", title="New benchmark shows Claude leading", url="",
            source="Artificial Analysis", category="", published=None, summary=""
        ),
    ]
    
    grouped = group_articles_by_category(test_articles)
    for category, arts in grouped.items():
        print(f"\n{category}:")
        for a in arts:
            print(f"  - {a.title}")
