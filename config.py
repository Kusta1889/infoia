"""
AI News Aggregator - Configuration
Central configuration for all sources, categories, and settings.
"""

import os
from dotenv import load_dotenv
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

load_dotenv()


class SourceType(Enum):
    RSS = "rss"
    API = "api"
    WEB = "web"
    CUSTOM = "custom"


class Category(Enum):
    RELEASES = "🚀 Lanzamientos de Modelos"
    INDUSTRY = "📰 Noticias de Industria"
    RESEARCH = "📄 Research & Papers"
    BENCHMARKS = "📊 Benchmarks & Rankings"
    TOOLS = "🛠️ Herramientas & APIs"
    SPANISH = "🇪🇸 En Español"


@dataclass
class Source:
    name: str
    url: str
    source_type: SourceType
    category: Category
    enabled: bool = True
    rss_url: Optional[str] = None  # For RSS sources


# =============================================================================
# ALL 17 SOURCES CONFIGURATION
# =============================================================================

SOURCES: List[Source] = [
    # --- OFFICIAL BLOGS (RSS) ---
    Source(
        name="OpenAI Blog",
        url="https://openai.com/blog",
        rss_url="https://openai.com/blog/rss.xml",
        source_type=SourceType.RSS,
        category=Category.RELEASES,
    ),
    Source(
        name="Google DeepMind Blog",
        url="https://deepmind.google/blog",
        rss_url="https://deepmind.google/blog/rss.xml",
        source_type=SourceType.RSS,
        category=Category.RELEASES,
    ),
    Source(
        name="Anthropic Blog",
        url="https://www.anthropic.com/news",
        rss_url="https://www.anthropic.com/rss.xml",
        source_type=SourceType.RSS,
        category=Category.RELEASES,
    ),
    Source(
        name="Hugging Face Blog",
        url="https://huggingface.co/blog",
        rss_url="https://huggingface.co/blog/feed.xml",
        source_type=SourceType.RSS,
        category=Category.RELEASES,
    ),
    
    # --- RESEARCH (API) ---
    Source(
        name="arXiv AI Papers",
        url="https://arxiv.org/list/cs.AI/recent",
        source_type=SourceType.API,
        category=Category.RESEARCH,
    ),
    Source(
        name="Hugging Face Daily Papers",
        url="https://huggingface.co/papers",
        source_type=SourceType.API,
        category=Category.RESEARCH,
    ),
    Source(
        name="BAIR Blog",
        url="https://bair.berkeley.edu/blog/",
        rss_url="https://bair.berkeley.edu/blog/feed.xml",
        source_type=SourceType.RSS,
        category=Category.RESEARCH,
    ),
    
    # --- NEWS SITES (RSS) ---
    Source(
        name="TechCrunch AI",
        url="https://techcrunch.com/category/artificial-intelligence/",
        rss_url="https://techcrunch.com/category/artificial-intelligence/feed/",
        source_type=SourceType.RSS,
        category=Category.INDUSTRY,
    ),
    Source(
        name="The Decoder",
        url="https://the-decoder.com/",
        rss_url="https://the-decoder.com/feed/",
        source_type=SourceType.RSS,
        category=Category.INDUSTRY,
    ),
    Source(
        name="VentureBeat AI",
        url="https://venturebeat.com/category/ai/",
        rss_url="https://venturebeat.com/category/ai/feed/",
        source_type=SourceType.RSS,
        category=Category.INDUSTRY,
    ),
    Source(
        name="MIT Technology Review",
        url="https://www.technologyreview.com/topic/artificial-intelligence/",
        rss_url="https://www.technologyreview.com/feed/",
        source_type=SourceType.RSS,
        category=Category.INDUSTRY,
    ),
    Source(
        name="The Verge AI",
        url="https://www.theverge.com/ai-artificial-intelligence",
        rss_url="https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        source_type=SourceType.RSS,
        category=Category.INDUSTRY,
    ),
    Source(
        name="Ars Technica AI",
        url="https://arstechnica.com/ai/",
        rss_url="https://feeds.arstechnica.com/arstechnica/features",
        source_type=SourceType.RSS,
        category=Category.INDUSTRY,
    ),
    Source(
        name="Simon Willison Blog",
        url="https://simonwillison.net/",
        rss_url="https://simonwillison.net/atom/everything/",
        source_type=SourceType.RSS,
        category=Category.RELEASES,  # Expert analysis on LLM releases
    ),
    
    # --- WEB SCRAPING ---
    Source(
        name="ThisDayInAI",
        url="https://thisdayinai.com/",
        source_type=SourceType.WEB,
        category=Category.INDUSTRY,
    ),
    Source(
        name="Artificial Analysis",
        url="https://artificialanalysis.ai/",
        source_type=SourceType.WEB,
        category=Category.BENCHMARKS,
    ),
    Source(
        name="LMArena Leaderboard",
        url="https://lmarena.ai/",
        source_type=SourceType.WEB,
        category=Category.BENCHMARKS,
    ),
    Source(
        name="Paper Digest AI",
        url="https://www.paperdigest.org/",
        source_type=SourceType.WEB,
        category=Category.RESEARCH,
    ),
    
    # --- SPANISH SOURCE ---
    Source(
        name="Xataka IA",
        url="https://www.xataka.com/tag/inteligencia-artificial",
        rss_url="https://www.xataka.com/tag/inteligencia-artificial/feedrss2",
        source_type=SourceType.RSS,
        category=Category.SPANISH,
    ),
    
    # --- LLM VERSION TRACKER (Custom) ---
    Source(
        name="LLM Release Tracker",
        url="",  # Custom implementation
        source_type=SourceType.CUSTOM,
        category=Category.RELEASES,
    ),
]


# =============================================================================
# LLM MODELS TO TRACK FOR VERSION UPDATES
# =============================================================================

LLM_MODELS_TO_TRACK = [
    {
        "name": "GPT-4",
        "provider": "OpenAI",
        "changelog_url": "https://platform.openai.com/docs/models",
    },
    {
        "name": "Claude",
        "provider": "Anthropic", 
        "changelog_url": "https://docs.anthropic.com/en/docs/models-overview",
    },
    {
        "name": "Gemini",
        "provider": "Google",
        "changelog_url": "https://ai.google.dev/gemini-api/docs/models/gemini",
    },
    {
        "name": "Llama",
        "provider": "Meta",
        "changelog_url": "https://llama.meta.com/",
    },
    {
        "name": "Mistral",
        "provider": "Mistral AI",
        "changelog_url": "https://docs.mistral.ai/getting-started/models/",
    },
    {
        "name": "DeepSeek",
        "provider": "DeepSeek",
        "changelog_url": "https://api-docs.deepseek.com/",
    },
    {
        "name": "Qwen",
        "provider": "Alibaba",
        "changelog_url": "https://qwen.readthedocs.io/en/latest/",
    },
]


# =============================================================================
# API CONFIGURATION
# =============================================================================

# DeepSeek API (OpenAI-compatible)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"  # or "deepseek-reasoner" for R1

# arXiv API
ARXIV_MAX_RESULTS = 20  # Papers per day
ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]  # AI, ML, Computational Linguistics


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "").split(",")
EMAIL_SUBJECT_PREFIX = "🤖 infoIA"


# =============================================================================
# SCHEDULE CONFIGURATION
# =============================================================================

SEND_HOUR = int(os.getenv("SEND_HOUR", "8"))
SEND_MINUTE = int(os.getenv("SEND_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "sent_articles.db")


# =============================================================================
# PROCESSING CONFIGURATION
# =============================================================================

# Maximum articles per source per day
MAX_ARTICLES_PER_SOURCE = 10

# Hours to look back for articles
LOOKBACK_HOURS = 24

# Summary configuration
SUMMARY_MAX_WORDS = 50  # Max words per article summary
BATCH_SIZE = 5  # Articles to summarize in one API call
