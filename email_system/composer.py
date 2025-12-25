"""
Email Composer
Generates HTML email digest from articles.
"""

from jinja2 import Environment
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass
import html
import re


def strip_html_tags(text: str) -> str:
    """Remove HTML tags, images, and clean up the text."""
    if not text:
        return ""
    # Remove img tags
    text = re.sub(r'<img[^>]*>', '', text, flags=re.IGNORECASE)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _slugify(text: str) -> str:
    """Convert category name to CSS class."""
    mapping = {
        "🚀 Lanzamientos de Modelos": "releases",
        "📄 Research & Papers": "research",
        "📊 Benchmarks & Rankings": "benchmarks",
        "📰 Noticias de Industria": "industry",
        "🛠️ Herramientas & APIs": "tools",
        "🇪🇸 En Español": "spanish",
    }
    return mapping.get(text, "default")


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
    summary_es: str = None


# HTML Email Template
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a2e;
            background-color: #f0f2f5;
        }
        
        .container {
            max-width: 700px;
            margin: 0 auto;
            background-color: #ffffff;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
        }
        
        .header .date {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
        }
        
        .stat {
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
        }
        
        .category-section {
            padding: 20px 25px;
            border-bottom: 1px solid #eee;
        }
        
        .category-header {
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            color: #1a1a2e;
        }
        
        .article {
            margin-bottom: 18px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .article:hover {
            background: #f0f2f5;
        }
        
        .article-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .article-title a {
            color: #1a1a2e;
            text-decoration: none;
        }
        
        .article-title a:hover {
            color: #667eea;
        }
        
        .article-meta {
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
        }
        
        .article-summary {
            font-size: 14px;
            color: #444;
        }
        
        .footer {
            background: #1a1a2e;
            color: #999;
            padding: 25px;
            text-align: center;
            font-size: 12px;
        }
        
        .footer a {
            color: #667eea;
        }
        
        .no-articles {
            padding: 40px;
            text-align: center;
            color: #666;
        }
        
        /* Category Colors */
        .category-releases .article { border-left-color: #10b981; }
        .category-research .article { border-left-color: #3b82f6; }
        .category-benchmarks .article { border-left-color: #f59e0b; }
        .category-industry .article { border-left-color: #8b5cf6; }
        .category-tools .article { border-left-color: #ef4444; }
        .category-spanish .article { border-left-color: #ec4899; }
        
        /* Archive Section */
        .archive-section {
            padding: 25px;
            background: #f8f9fa;
            border-top: 2px solid #667eea;
        }
        
        .archive-section h3 {
            font-size: 18px;
            margin-bottom: 15px;
            color: #1a1a2e;
        }
        
        .archive-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .archive-link {
            display: inline-block;
            padding: 8px 16px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            color: #667eea;
            text-decoration: none;
            font-size: 13px;
            transition: all 0.2s;
        }
        
        .archive-link:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 infoIA</h1>
            <div class="date">{{ date }}</div>
        </div>
        
        {% if grouped_articles %}
            {% for category, articles in grouped_articles.items() %}
            <div class="category-section category-{{ category | slug }}">
                <h2 class="category-header">{{ category }} ({{ articles | length }})</h2>
                
                {% for article in articles %}
                <div class="article">
                    <div class="article-title">
                        <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
                    </div>
                    <div class="article-summary">
                        {{ (article.summary_es or article.summary) | strip_html }}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        {% else %}
            <div class="no-articles">
                <p>📭 No hay artículos nuevos para hoy.</p>
                <p>¡Vuelve mañana para más novedades de IA!</p>
            </div>
        {% endif %}
        
        {% if archive_dates %}
        <div class="archive-section">
            <h3>📅 Noticias Anteriores</h3>
            <div class="archive-list">
                {% for archive in archive_dates %}
                <a href="{{ archive.filename }}" class="archive-link">{{ archive.display }}</a>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Generado automáticamente por <strong>infoIA</strong></p>
            <p>Monitoreando 18 fuentes de IA 24/7</p>
        </div>
    </div>
</body>
</html>
"""


class EmailComposer:
    """Composes HTML email digest."""
    
    def __init__(self):
        # Create environment with custom filters BEFORE compiling template
        self.env = Environment()
        self.env.filters['slug'] = _slugify
        self.env.filters['strip_html'] = strip_html_tags
        self.template = self.env.from_string(EMAIL_TEMPLATE)
    
    def compose(
        self,
        grouped_articles: Dict[str, List[Article]],
        subject_prefix: str = "🤖 infoIA",
        docs_dir: str = None
    ) -> tuple[str, str]:
        """
        Compose HTML email.
        
        Returns:
            Tuple of (subject, html_body)
        """
        import os
        import glob
        from datetime import timedelta
        
        today = datetime.now()
        
        # Spanish day and month names
        days_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        months_es = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                     'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        
        day_name = days_es[today.weekday()]
        month_name = months_es[today.month - 1]
        date_str = f"{day_name}, {today.day} de {month_name} de {today.year}"
        
        # Calculate stats
        total_articles = sum(len(arts) for arts in grouped_articles.values())
        total_categories = len(grouped_articles)
        sources = set()
        for articles in grouped_articles.values():
            for article in articles:
                sources.add(article.source)
        
        # Get archive dates from existing files (last 7 days, excluding today)
        archive_dates = []
        if docs_dir and os.path.exists(docs_dir):
            today_str = today.strftime("%Y-%m-%d")
            for i in range(1, 8):  # Last 7 days
                past_date = today - timedelta(days=i)
                past_str = past_date.strftime("%Y-%m-%d")
                filename = f"digest-{past_str}.html"
                filepath = os.path.join(docs_dir, filename)
                
                if os.path.exists(filepath):
                    # Format display date in Spanish
                    past_day_name = days_es[past_date.weekday()]
                    past_month_name = months_es[past_date.month - 1]
                    display = f"{past_day_name} {past_date.day}"
                    archive_dates.append({
                        "filename": filename,
                        "display": display,
                        "date": past_date
                    })
        
        # Render HTML
        html_body = self.template.render(
            subject=subject_prefix,
            date=date_str,
            grouped_articles=grouped_articles,
            total_articles=total_articles,
            total_categories=total_categories,
            total_sources=len(sources),
            archive_dates=archive_dates
        )
        
        
        # Generate subject line
        subject = f"{subject_prefix} - {today.strftime('%d/%m/%Y')} ({total_articles} artículos)"
        
        return subject, html_body
    
    def compose_plain_text(self, grouped_articles: Dict[str, List[Article]]) -> str:
        """Generate plain text version of email."""
        lines = []
        lines.append("=" * 50)
        lines.append("🤖 INFOIA")
        lines.append(f"📅 {datetime.now().strftime('%d/%m/%Y')}")
        lines.append("=" * 50)
        lines.append("")
        
        for category, articles in grouped_articles.items():
            lines.append(f"\n{category}")
            lines.append("-" * 40)
            
            for article in articles:
                lines.append(f"\n• {article.title}")
                lines.append(f"  Fuente: {article.source}")
                lines.append(f"  URL: {article.url}")
                summary = article.summary_es or article.summary
                if summary:
                    lines.append(f"  Resumen: {summary[:200]}...")
            
            lines.append("")
        
        lines.append("=" * 50)
        lines.append("Generado por AI News Aggregator")
        
        return "\n".join(lines)


def compose_email_digest(grouped_articles: Dict[str, List[Article]]) -> tuple[str, str, str]:
    """
    Compose email digest.
    
    Returns:
        Tuple of (subject, html_body, plain_text_body)
    """
    composer = EmailComposer()
    subject, html_body = composer.compose(grouped_articles)
    plain_text = composer.compose_plain_text(grouped_articles)
    return subject, html_body, plain_text


if __name__ == "__main__":
    # Test with sample data
    from datetime import datetime
    
    test_articles = {
        "🚀 Lanzamientos de Modelos": [
            Article(
                id="1",
                title="OpenAI lanza GPT-5 con razonamiento avanzado",
                url="https://openai.com/blog/gpt-5",
                source="OpenAI Blog",
                category="🚀 Lanzamientos de Modelos",
                published=datetime.now(),
                summary="GPT-5 representa un avance significativo en capacidades de razonamiento.",
                summary_es="OpenAI ha lanzado GPT-5, su modelo más avanzado hasta la fecha, con capacidades de razonamiento mejoradas."
            )
        ],
        "📄 Research & Papers": [
            Article(
                id="2",
                title="New Attention Mechanism Outperforms Transformers",
                url="https://arxiv.org/abs/xxx",
                source="arXiv",
                category="📄 Research & Papers",
                published=datetime.now(),
                summary="A new attention mechanism...",
                summary_es="Un nuevo mecanismo de atención supera a los transformers tradicionales en múltiples benchmarks."
            )
        ]
    }
    
    subject, html, text = compose_email_digest(test_articles)
    
    # Save test output
    with open("test_email.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Subject: {subject}")
    print(f"HTML saved to test_email.html")
