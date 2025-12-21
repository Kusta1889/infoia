"""
LLM Release Tracker
Tracks version updates and releases from major LLM providers.
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import hashlib
import json
import os


@dataclass
class Article:
    """Represents a single news article."""
    id: str
    title: str
    url: str
    source: str
    category: str
    published: datetime
    summary: str
    content: Optional[str] = None
    author: Optional[str] = None


# LLM Providers and their changelog/model pages
LLM_SOURCES = [
    {
        "provider": "OpenAI",
        "models": ["GPT-4", "GPT-4o", "GPT-4 Turbo", "o1"],
        "changelog_url": "https://platform.openai.com/docs/changelog",
        "models_url": "https://platform.openai.com/docs/models",
    },
    {
        "provider": "Anthropic",
        "models": ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Haiku"],
        "changelog_url": "https://docs.anthropic.com/en/release-notes/overview",
        "models_url": "https://docs.anthropic.com/en/docs/about-claude/models",
    },
    {
        "provider": "Google",
        "models": ["Gemini 2.0", "Gemini 1.5 Pro", "Gemini 1.5 Flash"],
        "changelog_url": "https://ai.google.dev/gemini-api/docs/changelog",
        "models_url": "https://ai.google.dev/gemini-api/docs/models/gemini",
    },
    {
        "provider": "Meta",
        "models": ["Llama 3.2", "Llama 3.1"],
        "changelog_url": "https://github.com/meta-llama/llama/releases",
        "models_url": "https://llama.meta.com/",
    },
    {
        "provider": "Mistral AI",
        "models": ["Mistral Large", "Mistral Medium", "Mixtral"],
        "changelog_url": "https://docs.mistral.ai/getting-started/changelog/",
        "models_url": "https://docs.mistral.ai/getting-started/models/",
    },
    {
        "provider": "DeepSeek",
        "models": ["DeepSeek-V3", "DeepSeek-R1", "DeepSeek Coder"],
        "changelog_url": "https://api-docs.deepseek.com/news/news1226",
        "models_url": "https://api-docs.deepseek.com/",
    },
    {
        "provider": "Alibaba",
        "models": ["Qwen 2.5", "Qwen-VL"],
        "changelog_url": "https://github.com/QwenLM/Qwen/releases",
        "models_url": "https://qwen.readthedocs.io/en/latest/",
    },
]


class LLMTracker:
    """Tracks LLM model updates and releases."""
    
    CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "llm_versions.json")
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.known_versions: Dict[str, str] = self._load_cache()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self._save_cache()
    
    def _load_cache(self) -> Dict[str, str]:
        """Load cached version data."""
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_cache(self):
        """Save version data to cache."""
        try:
            os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(self.known_versions, f, indent=2)
        except Exception as e:
            print(f"[LLM Tracker] Could not save cache: {e}")
    
    def _generate_id(self, provider: str, title: str) -> str:
        """Generate unique ID."""
        content = f"{provider}:{title}:{datetime.now().date()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _check_provider(self, source: Dict) -> List[Article]:
        """Check a provider for updates."""
        articles = []
        provider = source["provider"]
        
        try:
            # Try to fetch changelog
            async with self.session.get(source["changelog_url"]) as response:
                if response.status != 200:
                    return articles
                
                html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for recent entries (this varies by site)
            # We'll look for common patterns
            
            entries = []
            
            # Try different selectors
            for selector in [
                'article', '.changelog-entry', '.release', 
                '[class*="changelog"]', '[class*="release"]',
                'h2', 'h3'
            ]:
                found = soup.select(selector)[:5]
                if found:
                    entries = found
                    break
            
            for entry in entries[:3]:
                text = entry.get_text(strip=True)[:200]
                
                # Check if this looks like a model update
                model_mentioned = any(
                    model.lower() in text.lower() 
                    for model in source["models"]
                )
                
                if model_mentioned or 'update' in text.lower() or 'release' in text.lower():
                    # Check if we've seen this
                    entry_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                    cache_key = f"{provider}:{entry_hash}"
                    
                    if cache_key not in self.known_versions:
                        self.known_versions[cache_key] = str(datetime.now())
                        
                        article = Article(
                            id=self._generate_id(provider, text),
                            title=f"🔄 {provider}: {text[:80]}...",
                            url=source["changelog_url"],
                            source=f"{provider} Updates",
                            category="🚀 Lanzamientos de Modelos",
                            published=datetime.now(),
                            summary=f"New update from {provider}. Models: {', '.join(source['models'][:3])}. Check changelog for details."
                        )
                        articles.append(article)
            
            if articles:
                print(f"[LLM Tracker] {provider}: Found {len(articles)} updates")
            
        except Exception as e:
            print(f"[LLM Tracker] Error checking {provider}: {e}")
        
        return articles
    
    async def check_all_providers(self) -> List[Article]:
        """Check all LLM providers for updates."""
        tasks = [self._check_provider(source) for source in LLM_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
        
        # Always add a summary of tracked models if no specific updates
        if not articles:
            # Create a daily "status" article
            today = datetime.now().strftime("%Y-%m-%d")
            providers_list = ", ".join([s["provider"] for s in LLM_SOURCES])
            
            article = Article(
                id=self._generate_id("summary", today),
                title="📡 LLM Tracker: Sin actualizaciones importantes hoy",
                url="https://artificialanalysis.ai/",
                source="LLM Tracker",
                category="🚀 Lanzamientos de Modelos",
                published=datetime.now(),
                summary=f"Monitoreando: {providers_list}. No se detectaron cambios significativos en las últimas 24h."
            )
            articles.append(article)
        
        return articles


# Convenience function
async def track_llm_updates() -> List[Article]:
    """Track LLM model updates."""
    async with LLMTracker() as tracker:
        return await tracker.check_all_providers()


if __name__ == "__main__":
    async def test():
        articles = await track_llm_updates()
        for article in articles:
            print(f"\n{article.title}")
            print(f"  {article.summary}")
    
    asyncio.run(test())
