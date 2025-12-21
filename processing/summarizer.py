"""
Article Summarizer
Uses DeepSeek API to summarize articles and translate to Spanish.
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
    """Summarizes and translates articles using DeepSeek API."""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        
        if not self.api_key:
            print("[Summarizer] Warning: No API key configured")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def _call_api(self, messages: List[dict], max_tokens: int = 500) -> Optional[str]:
        """Make API call to DeepSeek."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3  # Lower for more consistent summaries
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Summarizer] API error: {e}")
            return None
    
    async def summarize_and_translate(self, article: Article) -> Article:
        """Summarize article content and translate to Spanish."""
        if not self.api_key:
            # No API key - just use existing summary
            article.summary_es = article.summary
            return article
        
        # Prepare content to summarize
        content = article.content or article.summary
        if not content:
            content = article.title
        
        # Truncate if too long
        content = content[:2000]
        
        prompt = f"""Eres un asistente experto en IA y tecnología. Tu tarea es:

1. Resumir el siguiente artículo en 2-3 oraciones concisas
2. El resumen DEBE estar en español
3. Mantén los nombres técnicos y de productos en inglés (GPT-4, Claude, etc.)
4. Enfócate en lo más importante y novedoso

Título: {article.title}
Fuente: {article.source}

Contenido:
{content}

Responde ÚNICAMENTE con el resumen en español, sin prefijos ni explicaciones."""

        messages = [
            {"role": "system", "content": "Eres un experto en IA que resume noticias de forma concisa y precisa en español."},
            {"role": "user", "content": prompt}
        ]
        
        summary = await self._call_api(messages)
        
        if summary:
            article.summary_es = summary
        else:
            # Fallback to original summary
            article.summary_es = article.summary
        
        return article
    
    async def process_batch(self, articles: List[Article], batch_size: int = 5) -> List[Article]:
        """Process articles in batches to avoid rate limits."""
        processed = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.summarize_and_translate(article) for article in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Article):
                    processed.append(result)
                elif isinstance(result, Exception):
                    print(f"[Summarizer] Batch error: {result}")
            
            # Small delay between batches to avoid rate limits
            if i + batch_size < len(articles):
                await asyncio.sleep(1)
        
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
