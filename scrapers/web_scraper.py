"""
Web Scraper
Scrapes content from websites without RSS feeds.
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass
import hashlib
import re


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


class WebScraper:
    """Scrapes articles from websites without RSS feeds."""
    
    def __init__(self, lookback_hours: int = 24):
        self.lookback_hours = lookback_hours
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace."""
        return re.sub(r'\s+', ' ', text).strip()
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"[Web] Error fetching {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"[Web] Error fetching {url}: {e}")
            return None
    
    async def scrape_thisdayinai(self) -> List[Article]:
        """Scrape ThisDayInAI.com for today's AI news."""
        articles = []
        url = "https://thisdayinai.com/"
        
        try:
            html = await self._fetch_html(url)
            if not html:
                return articles
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Find article containers
            for article_elem in soup.select('article, .post, .entry')[:10]:
                try:
                    # Title and link
                    title_elem = article_elem.select_one('h2 a, h3 a, .entry-title a')
                    if not title_elem:
                        continue
                    
                    title = self._clean_text(title_elem.get_text())
                    link = title_elem.get('href', '')
                    
                    if not link or not title:
                        continue
                    
                    # Summary
                    summary_elem = article_elem.select_one('p, .excerpt, .summary')
                    summary = self._clean_text(summary_elem.get_text()) if summary_elem else ""
                    
                    article = Article(
                        id=self._generate_id(link),
                        title=title,
                        url=link,
                        source="ThisDayInAI",
                        category="📰 Noticias de Industria",
                        published=datetime.now(),  # Assume today
                        summary=summary[:300]
                    )
                    articles.append(article)
                    
                except Exception as e:
                    continue
            
            print(f"[Web] ThisDayInAI: Found {len(articles)} articles")
            
        except Exception as e:
            print(f"[Web] ThisDayInAI error: {e}")
        
        return articles
    
    async def scrape_artificial_analysis(self) -> List[Article]:
        """Scrape Artificial Analysis for benchmark updates."""
        articles = []
        url = "https://artificialanalysis.ai/"
        
        try:
            html = await self._fetch_html(url)
            if not html:
                return articles
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for benchmark/model cards or news sections
            # This site is dynamic, so we'll extract what we can
            cards = soup.select('.card, [class*="model"], [class*="benchmark"]')[:5]
            
            if not cards:
                # Create a general update article
                article = Article(
                    id=self._generate_id(f"{url}-{datetime.now().date()}"),
                    title="📊 Artificial Analysis - Benchmark Updates",
                    url=url,
                    source="Artificial Analysis",
                    category="📊 Benchmarks & Rankings",
                    published=datetime.now(),
                    summary="Check the latest AI model benchmarks, pricing, and performance comparisons at Artificial Analysis."
                )
                articles.append(article)
            
            print(f"[Web] Artificial Analysis: Found {len(articles)} items")
            
        except Exception as e:
            print(f"[Web] Artificial Analysis error: {e}")
        
        return articles
    
    async def scrape_paper_digest(self) -> List[Article]:
        """Scrape Paper Digest for trending research."""
        articles = []
        url = "https://www.paperdigest.org/2024/12/"  # Will need date formatting
        
        # Use current month URL
        current_month = datetime.now().strftime("%Y/%m/")
        url = f"https://www.paperdigest.org/{current_month}"
        
        try:
            html = await self._fetch_html(url)
            if not html:
                # Fallback to main page
                html = await self._fetch_html("https://www.paperdigest.org/")
            
            if html:
                soup = BeautifulSoup(html, 'lxml')
                
                # Find article links
                for link in soup.select('a[href*="paper"]')[:10]:
                    title = self._clean_text(link.get_text())
                    href = link.get('href', '')
                    
                    if len(title) > 20 and href:
                        article = Article(
                            id=self._generate_id(href),
                            title=f"📑 {title[:100]}",
                            url=href if href.startswith('http') else f"https://www.paperdigest.org{href}",
                            source="Paper Digest",
                            category="📄 Research & Papers",
                            published=datetime.now(),
                            summary=title
                        )
                        articles.append(article)
            
            print(f"[Web] Paper Digest: Found {len(articles)} papers")
            
        except Exception as e:
            print(f"[Web] Paper Digest error: {e}")
        
        return articles
    
    async def fetch_all(self) -> List[Article]:
        """Fetch from all web sources."""
        results = await asyncio.gather(
            self.scrape_thisdayinai(),
            self.scrape_artificial_analysis(),
            self.scrape_paper_digest(),
            return_exceptions=True
        )
        
        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                print(f"[Web] Scraper error: {result}")
        
        return articles


# Convenience function
async def scrape_web_sources(lookback_hours: int = 24) -> List[Article]:
    """Scrape all web sources."""
    async with WebScraper(lookback_hours=lookback_hours) as scraper:
        return await scraper.fetch_all()


if __name__ == "__main__":
    async def test():
        articles = await scrape_web_sources()
        print(f"\nTotal: {len(articles)} articles\n")
        for article in articles:
            print(f"[{article.source}] {article.title}")
            print(f"  {article.url}\n")
    
    asyncio.run(test())
