"""
Article Summarizer
Uses Groq API to summarize articles and translate to Spanish.
"""

import asyncio
from openai import AsyncOpenAI
from typing import List, Optional
from dataclasses import dataclass
import os


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
    summary_es: str = None  # Spanish summary


class Summarizer:
    """Summarizes and translates articles using Groq API."""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.base_url = base_url or "https://api.groq.com/openai/v1"
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        if not self.api_key:
            print("[Summarizer] Warning: No API key configured")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def _call_api(self, messages: List[dict], max_tokens: int = 300, retries: int = 3) -> Optional[str]:
        """Make API call to Groq with retry logic."""
        for attempt in range(retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    wait_time = (attempt + 1) * 3  # 3, 6, 9 seconds
                    print(f"[Summarizer] Rate limit, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"[Summarizer] API error: {e}")
                    return None
        print(f"[Summarizer] Max retries exceeded")
        return None
    
    async def summarize_and_translate(self, article: Article) -> Article:
        """Summarize article content and translate to Spanish."""
        if not self.api_key:
            article.summary_es = article.summary
            return article
        
        content = article.content or article.summary
        if not content:
            content = article.title
        
        # Truncate to reduce tokens
        content = content[:1000]
        
        prompt = f"""Resume en 2 oraciones en español:

Título: {article.title}
Fuente: {article.source}
Contenido: {content}

Solo el resumen, sin prefijos."""

        messages = [
            {"role": "system", "content": "Resumes noticias de IA en español de forma concisa."},
            {"role": "user", "content": prompt}
        ]
        
        summary = await self._call_api(messages)
        
        if summary:
            article.summary_es = summary
        else:
            article.summary_es = article.summary
        
        return article
    
    async def process_batch(self, articles: List[Article], max_articles: int = 15) -> List[Article]:
        """Process articles sequentially to avoid rate limits."""
        processed = []
        
        # Limit total articles to avoid excessive API calls
        articles = articles[:max_articles]
        
        for i, article in enumerate(articles):
            print(f"[Summarizer] Processing {i+1}/{len(articles)}: {article.title[:50]}...")
            result = await self.summarize_and_translate(article)
            processed.append(result)
            
            # Wait between each article to respect rate limit
            if i < len(articles) - 1:
                await asyncio.sleep(2)  # 2 seconds between each
        
        print(f"[Summarizer] Processed {len(processed)} articles")
        return processed
    
    async def summarize_all(self, articles: List[Article]) -> List[Article]:
        """Summarize and translate all articles."""
        if not articles:
            return articles
        
        return await self.process_batch(articles)


# Convenience function
async def summarize_articles(articles: List[Article], api_key: str = None) -> List[Article]:
    """Summarize and translate articles."""
    summarizer = Summarizer(api_key=api_key)
    return await summarizer.summarize_all(articles)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    async def test():
        test_article = Article(
            id="test",
            title="OpenAI releases GPT-5 with advanced reasoning",
            url="https://example.com",
            source="OpenAI Blog",
            category="Releases",
            published=None,
            summary="OpenAI has announced the release of GPT-5, their most advanced language model yet. The model features improved reasoning capabilities and can handle complex multi-step problems.",
            content="OpenAI has announced the release of GPT-5, their most advanced language model yet. The model features improved reasoning capabilities and can handle complex multi-step problems. CEO Sam Altman stated this represents a major leap forward in AI capabilities."
        )
        
        summarizer = Summarizer()
        result = await summarizer.summarize_and_translate(test_article)
        print(f"Original: {result.summary}")
        print(f"Spanish: {result.summary_es}")
    
    asyncio.run(test())
