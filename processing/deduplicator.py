"""
Article Deduplicator
Prevents duplicate articles from being sent using SQLite cache.
"""

import aiosqlite
import hashlib
import os
from datetime import datetime, timedelta
from typing import List, Set
from dataclasses import dataclass, asdict


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
    content: str = None
    author: str = None


class Deduplicator:
    """Manages article deduplication using SQLite."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "sent_articles.db"
        )
        self.conn = None
    
    async def __aenter__(self):
        await self._init_db()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            await self.conn.close()
    
    async def _init_db(self):
        """Initialize database and table."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = await aiosqlite.connect(self.db_path)
        
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_articles (
                id TEXT PRIMARY KEY,
                url TEXT,
                title_hash TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url ON sent_articles(url)
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_title_hash ON sent_articles(title_hash)
        """)
        
        await self.conn.commit()
    
    def _hash_title(self, title: str) -> str:
        """Create hash of normalized title for comparison."""
        # Normalize: lowercase, remove punctuation, trim
        normalized = ''.join(c.lower() for c in title if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    async def is_duplicate(self, article: Article) -> bool:
        """Check if article has been sent before."""
        title_hash = self._hash_title(article.title)
        
        # Check by URL or similar title
        cursor = await self.conn.execute("""
            SELECT 1 FROM sent_articles 
            WHERE url = ? OR title_hash = ?
            LIMIT 1
        """, (article.url, title_hash))
        
        result = await cursor.fetchone()
        return result is not None
    
    async def mark_as_sent(self, article: Article):
        """Mark article as sent."""
        title_hash = self._hash_title(article.title)
        
        try:
            await self.conn.execute("""
                INSERT OR REPLACE INTO sent_articles (id, url, title_hash, sent_at)
                VALUES (?, ?, ?, ?)
            """, (article.id, article.url, title_hash, datetime.now()))
            await self.conn.commit()
        except Exception as e:
            print(f"[Dedup] Error marking article: {e}")
    
    async def mark_batch_as_sent(self, articles: List[Article]):
        """Mark multiple articles as sent."""
        for article in articles:
            await self.mark_as_sent(article)
    
    async def filter_duplicates(self, articles: List[Article]) -> List[Article]:
        """Filter out duplicate articles, keeping only new ones."""
        unique = []
        
        for article in articles:
            if not await self.is_duplicate(article):
                unique.append(article)
        
        print(f"[Dedup] Filtered {len(articles)} -> {len(unique)} unique articles")
        return unique
    
    async def cleanup_old(self, days: int = 30):
        """Remove entries older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        
        await self.conn.execute("""
            DELETE FROM sent_articles WHERE sent_at < ?
        """, (cutoff,))
        
        await self.conn.commit()
        print(f"[Dedup] Cleaned up entries older than {days} days")
    
    async def get_stats(self) -> dict:
        """Get deduplication statistics."""
        cursor = await self.conn.execute("SELECT COUNT(*) FROM sent_articles")
        total = (await cursor.fetchone())[0]
        
        cursor = await self.conn.execute("""
            SELECT COUNT(*) FROM sent_articles 
            WHERE sent_at > datetime('now', '-24 hours')
        """)
        last_24h = (await cursor.fetchone())[0]
        
        return {
            "total_tracked": total,
            "sent_last_24h": last_24h
        }


# Convenience function
async def deduplicate_articles(articles: List[Article], db_path: str = None) -> List[Article]:
    """Filter duplicate articles."""
    async with Deduplicator(db_path) as dedup:
        return await dedup.filter_duplicates(articles)


if __name__ == "__main__":
    import asyncio
    
    async def test():
        async with Deduplicator() as dedup:
            stats = await dedup.get_stats()
            print(f"Stats: {stats}")
    
    asyncio.run(test())
