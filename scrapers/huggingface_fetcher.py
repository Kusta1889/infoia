"""
Hugging Face Fetcher
Fetches trending papers and popular new models from Hugging Face.
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
import hashlib


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


class HuggingFaceFetcher:
    """Fetches trending papers and models from Hugging Face."""
    
    PAPERS_API = "https://huggingface.co/api/daily_papers"
    MODELS_API = "https://huggingface.co/api/models"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "AI-News-Aggregator/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def fetch_daily_papers(self, limit: int = 15) -> List[Article]:
        """Fetch today's trending papers from HF Daily Papers."""
        articles = []
        
        try:
            async with self.session.get(self.PAPERS_API) as response:
                if response.status != 200:
                    print(f"[HF Papers] Error: HTTP {response.status}")
                    return articles
                
                papers = await response.json()
            
            for paper in papers[:limit]:
                try:
                    # Extract paper info
                    paper_data = paper.get('paper', {})
                    title = paper_data.get('title', 'No Title')
                    paper_id = paper_data.get('id', '')
                    summary = paper_data.get('summary', '')[:500]
                    
                    # Authors
                    authors = paper_data.get('authors', [])
                    author_names = [a.get('name', '') for a in authors[:3]]
                    author_str = ", ".join(author_names)
                    if len(authors) > 3:
                        author_str += f" et al."
                    
                    # Published date
                    pub_date_str = paper.get('publishedAt', '')
                    if pub_date_str:
                        published = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    else:
                        published = datetime.now()
                    
                    url = f"https://huggingface.co/papers/{paper_id}"
                    
                    article = Article(
                        id=self._generate_id(url),
                        title=f"📑 {title}",
                        url=url,
                        source="HuggingFace Papers",
                        category="📄 Research & Papers",
                        published=published,
                        summary=summary,
                        author=author_str
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    print(f"[HF Papers] Error parsing paper: {e}")
                    continue
            
            print(f"[HF Papers] Found {len(articles)} trending papers")
            
        except asyncio.TimeoutError:
            print("[HF Papers] Timeout")
        except Exception as e:
            print(f"[HF Papers] Error: {e}")
        
        return articles
    
    async def fetch_new_models(self, limit: int = 10) -> List[Article]:
        """Fetch new popular models from Hugging Face."""
        articles = []
        
        params = {
            "sort": "createdAt",
            "direction": "-1",
            "limit": limit * 2,  # Get more to filter
            "full": "false"
        }
        
        try:
            async with self.session.get(self.MODELS_API, params=params) as response:
                if response.status != 200:
                    print(f"[HF Models] Error: HTTP {response.status}")
                    return articles
                
                models = await response.json()
            
            # Filter for models with significant downloads (popular)
            cutoff = datetime.now() - timedelta(hours=48)
            
            for model in models:
                try:
                    model_id = model.get('id', '')
                    downloads = model.get('downloads', 0)
                    
                    # Only include models with some traction
                    if downloads < 100:
                        continue
                    
                    # Created date
                    created_str = model.get('createdAt', '')
                    if created_str:
                        created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        if created.replace(tzinfo=None) < cutoff:
                            continue
                    else:
                        created = datetime.now()
                    
                    # Tags/pipeline
                    pipeline = model.get('pipeline_tag', 'unknown')
                    tags = model.get('tags', [])[:3]
                    
                    url = f"https://huggingface.co/{model_id}"
                    
                    article = Article(
                        id=self._generate_id(url),
                        title=f"🤗 New Model: {model_id}",
                        url=url,
                        source="HuggingFace Models",
                        category="🛠️ Herramientas & APIs",
                        published=created,
                        summary=f"Pipeline: {pipeline}. Tags: {', '.join(tags)}. Downloads: {downloads:,}",
                        author=model_id.split('/')[0] if '/' in model_id else None
                    )
                    
                    articles.append(article)
                    
                    if len(articles) >= limit:
                        break
                        
                except Exception as e:
                    print(f"[HF Models] Error parsing model: {e}")
                    continue
            
            print(f"[HF Models] Found {len(articles)} new popular models")
            
        except asyncio.TimeoutError:
            print("[HF Models] Timeout")
        except Exception as e:
            print(f"[HF Models] Error: {e}")
        
        return articles
    
    async def fetch_all(self) -> List[Article]:
        """Fetch both papers and models."""
        papers, models = await asyncio.gather(
            self.fetch_daily_papers(),
            self.fetch_new_models(),
            return_exceptions=True
        )
        
        articles = []
        
        if isinstance(papers, list):
            articles.extend(papers)
        
        if isinstance(models, list):
            articles.extend(models)
        
        return articles


# Convenience function
async def fetch_huggingface_content() -> List[Article]:
    """Fetch all content from Hugging Face."""
    async with HuggingFaceFetcher() as fetcher:
        return await fetcher.fetch_all()


if __name__ == "__main__":
    async def test():
        articles = await fetch_huggingface_content()
        print(f"\nTotal: {len(articles)} items\n")
        for article in articles[:5]:
            print(f"{article.title}")
            print(f"  {article.url}")
            print()
    
    asyncio.run(test())
