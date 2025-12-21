"""
Article Summarizer
Uses Groq (free) for intelligent summaries + Google Translate for titles.
"""

import asyncio
import re
import os
from groq import Groq
from deep_translator import GoogleTranslator
from typing import List, Optional
from dataclasses import dataclass


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    text = re.sub(r'<img[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


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
    summary_es: str = None


class Summarizer:
    """Summarizes with Groq and translates titles with Google Translate."""
    
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.groq_client = None
        self.translator = GoogleTranslator(source='auto', target='es')
        
        if self.groq_key:
            self.groq_client = Groq(api_key=self.groq_key)
            print("[Summarizer] Groq API configured (free tier)")
        else:
            print("[Summarizer] No Groq API key - using translation only")
    
    def _translate_title(self, text: str) -> str:
        """Translate title with Google Translate."""
        if not text or not text.strip():
            return text
        try:
            clean_text = strip_html_tags(text)
            return self.translator.translate(clean_text)
        except Exception as e:
            print(f"[Translator] Error: {e}")
            return text
    
    def _summarize_with_groq(self, title: str, content: str) -> Optional[str]:
        """Use Groq to generate Spanish summary."""
        if not self.groq_client:
            return None
        
        try:
            content = strip_html_tags(content)[:1500]
            
            prompt = f"""Genera un resumen en español de 3-4 oraciones sobre esta noticia de tecnología/IA.
El resumen debe ser claro, profesional y en español natural.

Título: {title}
Contenido: {content}

Responde SOLO con el resumen en español, sin introducciones ni explicaciones."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Clean up if it starts with common prefixes
            prefixes = ["Resumen:", "Aquí está", "El resumen:", "Summary:"]
            for prefix in prefixes:
                if summary.lower().startswith(prefix.lower()):
                    summary = summary[len(prefix):].strip()
            
            return summary if summary else None
            
        except Exception as e:
            print(f"[Groq] Error: {e}")
            return None
    
    def _translate_summary(self, text: str) -> str:
        """Fallback: translate summary with Google Translate."""
        if not text or not text.strip():
            return text
        try:
            clean_text = strip_html_tags(text)[:1000]
            return self.translator.translate(clean_text)
        except Exception as e:
            print(f"[Translator] Error: {e}")
            return text
    
    async def summarize_and_translate(self, article: Article) -> Article:
        """Summarize and translate article to Spanish."""
        loop = asyncio.get_event_loop()
        
        content = article.content or article.summary or article.title
        
        # Translate title with Google Translate
        try:
            article.title = await loop.run_in_executor(
                None, self._translate_title, article.title
            )
        except Exception as e:
            print(f"[Translator] Title error: {e}")
        
        # Generate summary with Groq
        if self.groq_client:
            try:
                summary = await loop.run_in_executor(
                    None, 
                    self._summarize_with_groq, 
                    article.title, 
                    content
                )
                if summary:
                    article.summary_es = summary
                    return article
            except Exception as e:
                print(f"[Groq] Fallback to translator: {e}")
        
        # Fallback to simple translation
        try:
            article.summary_es = await loop.run_in_executor(
                None, self._translate_summary, content
            )
        except Exception as e:
            print(f"[Translator] Error: {e}")
            article.summary_es = strip_html_tags(article.summary)
        
        return article
    
    async def process_batch(self, articles: List[Article], max_articles: int = 25) -> List[Article]:
        """Process articles with delays to respect rate limits."""
        processed = []
        articles = articles[:max_articles]
        
        for i, article in enumerate(articles):
            title_preview = (article.title or "No title")[:40]
            print(f"[Summarizer] {i+1}/{len(articles)}: {title_preview}...")
            
            result = await self.summarize_and_translate(article)
            processed.append(result)
            
            # Delay between Groq API calls (rate limit: 30 req/min)
            if i < len(articles) - 1:
                await asyncio.sleep(2)
        
        print(f"[Summarizer] Processed {len(processed)} articles")
        return processed
    
    async def summarize_all(self, articles: List[Article]) -> List[Article]:
        """Summarize and translate all articles."""
        if not articles:
            return articles
        return await self.process_batch(articles)


async def summarize_articles(articles: List[Article]) -> List[Article]:
    """Summarize and translate all articles."""
    summarizer = Summarizer()
    return await summarizer.summarize_all(articles)


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    
    test_article = Article(
        id="1",
        title="OpenAI announces GPT-5 with advanced reasoning capabilities",
        url="https://example.com",
        source="OpenAI Blog",
        category="Releases",
        published=None,
        summary="OpenAI has released GPT-5, their most advanced model yet. It features improved reasoning and can handle complex multi-step tasks. The model shows significant improvements in mathematics and coding."
    )
    
    async def test():
        summarizer = Summarizer()
        result = await summarizer.summarize_and_translate(test_article)
        print(f"Title: {result.title}")
        print(f"Summary: {result.summary_es}")
    
    asyncio.run(test())
