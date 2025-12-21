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
        """Summarize article content and translate title and summary to Spanish."""
        if not self.api_key:
            article.summary_es = article.summary
            return article
        
        content = article.content or article.summary
        if not content:
            content = article.title
        
        # Truncate to reduce tokens but allow more content for better summary
        content = content[:1500]
        
        prompt = f"""Eres un periodista tecnológico nativo en español. Tu tarea es REESCRIBIR la siguiente noticia en español de forma natural y profesional.

REGLAS IMPORTANTES:
1. El título debe sonar NATURAL en español, como si lo hubiera escrito un periodista hispanohablante. NO hagas traducciones literales.
2. Mantén los nombres propios en inglés (GPT, Claude, OpenAI, etc.)
3. El resumen debe ser de 4-5 oraciones, claro y bien redactado
4. Evita construcciones gramaticales que suenen "traducidas del inglés"

EJEMPLOS DE TÍTULOS:
- MAL: "Anunciar a los consumidores que un anuncio es generado por IA reduce clics"
- BIEN: "Los usuarios hacen menos clic cuando saben que un anuncio fue creado con IA"

- MAL: "OpenAI lanza actualización para GPT-4"  
- BIEN: "OpenAI presenta una nueva versión de GPT-4"

Título original: {article.title}
Contenido: {content}

Responde EXACTAMENTE así:
TÍTULO: [título en español natural]
RESUMEN: [resumen de 4-5 oraciones]"""

        messages = [
            {"role": "system", "content": "Eres un periodista tecnológico hispanohablante. Escribes noticias de IA de forma natural y profesional, nunca como traducciones literales."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_api(messages, max_tokens=400)
        
        if result:
            # Parse the response
            lines = result.strip().split('\n')
            title_es = article.title
            summary_es = article.summary
            
            for line in lines:
                if line.startswith('TÍTULO:'):
                    title_es = line.replace('TÍTULO:', '').strip()
                elif line.startswith('RESUMEN:'):
                    summary_es = line.replace('RESUMEN:', '').strip()
                elif summary_es and not line.startswith('TÍTULO'):
                    # Continuation of summary
                    summary_es += ' ' + line.strip()
            
            article.title = title_es
            article.summary_es = summary_es
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
