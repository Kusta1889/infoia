"""
RSS Feed Fetcher
Fetches and parses RSS feeds from various AI news sources.
"""

import feedparser
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
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


class RSSFetcher:
    """Fetches articles from RSS feeds."""
    
    def __init__(self, lookback_hours: int = 24):
        self.lookback_hours = lookback_hours
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "AI-News-Aggregator/1.0 (https://github.com/ai-news-bot)"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_id(self, url: str, title: str) -> str:
        """Generate unique ID for an article."""
        content = f"{url}:{title}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _parse_date(self, entry: Dict) -> Optional[datetime]:
        """Parse date from RSS entry."""
        # Try different date fields
        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if field in entry and entry[field]:
                try:
                    from time import mktime
                    return datetime.fromtimestamp(mktime(entry[field]))
                except Exception:
                    continue
        
        # Try string dates
        for field in ['published', 'updated', 'created']:
            if field in entry and entry[field]:
                try:
                    from dateutil.parser import parse
                    return parse(entry[field])
                except Exception:
                    continue
        
        return None
    
    def _extract_content(self, entry: Dict) -> str:
        """Extract content/summary from RSS entry."""
        # Try content field first
        if 'content' in entry and entry['content']:
            return entry['content'][0].get('value', '')
        
        # Try summary
        if 'summary' in entry:
            return entry['summary']
        
        # Try description
        if 'description' in entry:
            return entry['description']
        
        return ""
    
    async def fetch_feed(self, rss_url: str, source_name: str, category: str) -> List[Article]:
        """Fetch articles from a single RSS feed."""
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)
        
        try:
            # Fetch the feed
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    print(f"[RSS] Error fetching {source_name}: HTTP {response.status}")
                    return articles
                
                content = await response.text()
            
            # Parse the feed
            feed = feedparser.parse(content)
            
            if feed.bozo and not feed.entries:
                print(f"[RSS] Error parsing {source_name}: {feed.bozo_exception}")
                return articles
            
            # Process entries
            for entry in feed.entries:
                # Get publication date
                pub_date = self._parse_date(entry)
                
                # Skip if no date or too old
                if pub_date is None:
                    pub_date = datetime.now()  # Assume recent if no date
                elif pub_date < cutoff_time:
                    continue
                
                # Extract article data
                title = entry.get('title', 'No Title')
                url = entry.get('link', '')
                
                if not url:
                    continue
                
                article = Article(
                    id=self._generate_id(url, title),
                    title=title,
                    url=url,
                    source=source_name,
                    category=category,
                    published=pub_date,
                    summary=self._extract_content(entry)[:500],  # Limit summary length
                    author=entry.get('author', None)
                )
                
                articles.append(article)
            
            print(f"[RSS] {source_name}: Found {len(articles)} recent articles")
            
        except asyncio.TimeoutError:
            print(f"[RSS] Timeout fetching {source_name}")
        except Exception as e:
            print(f"[RSS] Error fetching {source_name}: {e}")
        
        return articles
    
    async def fetch_all(self, sources: List[Dict[str, str]]) -> List[Article]:
        """
        Fetch articles from multiple RSS sources.
        
        Args:
            sources: List of dicts with 'rss_url', 'name', 'category'
        
        Returns:
            List of all articles from all sources
        """
        tasks = [
            self.fetch_feed(
                source['rss_url'],
                source['name'],
                source['category']
            )
            for source in sources
            if source.get('rss_url')
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                print(f"[RSS] Batch error: {result}")
        
        return all_articles


# Convenience function for standalone usage
async def fetch_rss_articles(sources: List[Dict[str, str]], lookback_hours: int = 24) -> List[Article]:
    """Fetch articles from RSS sources."""
    async with RSSFetcher(lookback_hours=lookback_hours) as fetcher:
        return await fetcher.fetch_all(sources)


if __name__ == "__main__":
    # Test with a sample source
    import asyncio
    
    test_sources = [
        {
            "rss_url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "name": "TechCrunch AI",
            "category": "📰 Noticias de Industria"
        }
    ]
    
    async def test():
        articles = await fetch_rss_articles(test_sources, lookback_hours=48)
        for article in articles[:3]:
            print(f"\n{article.title}")
            print(f"  URL: {article.url}")
            print(f"  Date: {article.published}")
    
    asyncio.run(test())
