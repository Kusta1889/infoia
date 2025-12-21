"""
Article Summarizer
Uses Google Gemini API to summarize articles and translate to Spanish.
"""

import asyncio
import google.generativeai as genai
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
    """Summarizes and translates articles using Google Gemini API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        
        if not self.api_key:
            print("[Summarizer] Warning: No GEMINI_API_KEY configured")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def _call_api(self, prompt: str, retries: int = 3) -> Optional[str]:
        """Make API call to Gemini with retry logic."""
        for attempt in range(retries):
            try:
                # Run sync call in executor for async compatibility
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt)
                )
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    wait_time = (attempt + 1) * 2
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
        
        # Truncate to reduce tokens
        content = content[:2000]
        
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

        result = await self._call_api(prompt)
        
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
    
    async def process_batch(self, articles: List[Article], max_articles: int = 20) -> List[Article]:
        """Process articles sequentially to respect API limits."""
        processed = []
        
        # Gemini has generous limits, process more articles
        articles = articles[:max_articles]
        
        for i, article in enumerate(articles):
            print(f"[Summarizer] Processing {i+1}/{len(articles)}: {article.title[:50]}...")
            result = await self.summarize_and_translate(article)
            processed.append(result)
            
            # Small delay between calls
            if i < len(articles) - 1:
                await asyncio.sleep(1)
        
        print(f"[Summarizer] Processed {len(processed)} articles")
        return processed
    
    async def summarize_all(self, articles: List[Article]) -> List[Article]:
        """Summarize and translate all articles."""
        if not articles:
            return articles
        
        if not self.api_key:
            print("[Summarizer] No API key - skipping summarization")
            for article in articles:
                article.summary_es = article.summary
            return articles
        
        return await self.process_batch(articles)


# Convenience function
async def summarize_articles(articles: List[Article]) -> List[Article]:
    """Summarize and translate all articles."""
    summarizer = Summarizer()
    return await summarizer.summarize_all(articles)


if __name__ == "__main__":
    # Test
    import asyncio
    
    test_article = Article(
        id="1",
        title="OpenAI announces GPT-5 with advanced reasoning",
        url="https://example.com",
        source="OpenAI Blog",
        category="Releases",
        published=None,
        summary="OpenAI has released GPT-5, their most advanced model yet."
    )
    
    async def test():
        summarizer = Summarizer()
        result = await summarizer.summarize_and_translate(test_article)
        print(f"Title: {result.title}")
        print(f"Summary: {result.summary_es}")
    
    asyncio.run(test())
