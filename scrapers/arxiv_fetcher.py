"""
arXiv API Fetcher
Fetches recent AI/ML papers from arXiv.
"""

import aiohttp
import asyncio
import xml.etree.ElementTree as ET
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


class ArxivFetcher:
    """Fetches papers from arXiv API."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self, max_results: int = 20, categories: List[str] = None):
        self.max_results = max_results
        self.categories = categories or ["cs.AI", "cs.LG", "cs.CL"]
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                "User-Agent": "AI-News-Aggregator/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_id(self, arxiv_id: str) -> str:
        """Generate unique ID from arXiv ID."""
        return hashlib.md5(arxiv_id.encode()).hexdigest()
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace."""
        return re.sub(r'\s+', ' ', text).strip()
    
    def _parse_entry(self, entry: ET.Element, ns: dict) -> Optional[Article]:
        """Parse a single arXiv entry."""
        try:
            # Extract arXiv ID
            id_elem = entry.find('atom:id', ns)
            if id_elem is None:
                return None
            arxiv_url = id_elem.text
            arxiv_id = arxiv_url.split('/abs/')[-1] if '/abs/' in arxiv_url else arxiv_url
            
            # Title
            title_elem = entry.find('atom:title', ns)
            title = self._clean_text(title_elem.text) if title_elem is not None else "No Title"
            
            # Summary/Abstract
            summary_elem = entry.find('atom:summary', ns)
            summary = self._clean_text(summary_elem.text) if summary_elem is not None else ""
            
            # Published date
            published_elem = entry.find('atom:published', ns)
            if published_elem is not None:
                published = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
            else:
                published = datetime.now()
            
            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text)
            author_str = ", ".join(authors[:3])  # First 3 authors
            if len(authors) > 3:
                author_str += f" et al. ({len(authors)} authors)"
            
            # PDF link
            pdf_link = arxiv_url.replace('/abs/', '/pdf/')
            
            return Article(
                id=self._generate_id(arxiv_id),
                title=title,
                url=arxiv_url,
                source="arXiv",
                category="📄 Research & Papers",
                published=published,
                summary=summary[:500],  # Limit length
                content=summary,
                author=author_str
            )
            
        except Exception as e:
            print(f"[arXiv] Error parsing entry: {e}")
            return None
    
    async def fetch_papers(self, lookback_hours: int = 24) -> List[Article]:
        """Fetch recent papers from arXiv."""
        articles = []
        
        # Build query for AI/ML categories
        category_query = " OR ".join([f"cat:{cat}" for cat in self.categories])
        
        params = {
            "search_query": f"({category_query})",
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    print(f"[arXiv] Error: HTTP {response.status}")
                    return articles
                
                content = await response.text()
            
            # Parse XML response
            root = ET.fromstring(content)
            
            # Define namespace
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Process entries
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            
            for entry in root.findall('atom:entry', ns):
                article = self._parse_entry(entry, ns)
                
                if article:
                    # Check if recent enough (arXiv dates are UTC)
                    if article.published.replace(tzinfo=None) >= cutoff_time:
                        articles.append(article)
            
            print(f"[arXiv] Found {len(articles)} recent papers")
            
        except asyncio.TimeoutError:
            print("[arXiv] Timeout fetching papers")
        except Exception as e:
            print(f"[arXiv] Error: {e}")
        
        return articles


# Convenience function
async def fetch_arxiv_papers(max_results: int = 20, 
                             categories: List[str] = None,
                             lookback_hours: int = 24) -> List[Article]:
    """Fetch recent papers from arXiv."""
    async with ArxivFetcher(max_results=max_results, categories=categories) as fetcher:
        return await fetcher.fetch_papers(lookback_hours=lookback_hours)


if __name__ == "__main__":
    # Test
    async def test():
        papers = await fetch_arxiv_papers(max_results=10, lookback_hours=72)
        for paper in papers[:3]:
            print(f"\n📄 {paper.title[:80]}...")
            print(f"   Authors: {paper.author}")
            print(f"   URL: {paper.url}")
    
    asyncio.run(test())
