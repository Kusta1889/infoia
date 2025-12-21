"""
AI News Aggregator - Main Entry Point
Orchestrates the entire pipeline: fetch → process → summarize → email
"""

import asyncio
import argparse
import schedule
import time
import sys
import os
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Import configuration
from config import (
    SOURCES, SourceType, Category,
    LOOKBACK_HOURS, MAX_ARTICLES_PER_SOURCE,
    EMAIL_TO, SEND_HOUR, SEND_MINUTE,
    ARXIV_MAX_RESULTS, ARXIV_CATEGORIES
)

# Import scrapers
from scrapers.rss_fetcher import RSSFetcher
from scrapers.arxiv_fetcher import ArxivFetcher
from scrapers.huggingface_fetcher import HuggingFaceFetcher
from scrapers.web_scraper import WebScraper
from scrapers.llm_tracker import LLMTracker

# Import processing
from processing.deduplicator import Deduplicator
from processing.categorizer import Categorizer
from processing.summarizer import Summarizer

# Import email system
from email_system.composer import EmailComposer
from email_system.sender import EmailSender


class AINewsAggregator:
    """Main aggregator class that orchestrates the pipeline."""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.articles = []
    
    async def fetch_all_sources(self) -> List:
        """Fetch articles from all configured sources."""
        all_articles = []
        
        print("\n" + "=" * 50)
        print("📡 FETCHING FROM ALL SOURCES")
        print("=" * 50)
        
        # 1. RSS Sources
        rss_sources = [
            {
                "rss_url": s.rss_url,
                "name": s.name,
                "category": s.category.value
            }
            for s in SOURCES
            if s.source_type == SourceType.RSS and s.enabled and s.rss_url
        ]
        
        if rss_sources:
            print(f"\n📰 Fetching {len(rss_sources)} RSS feeds...")
            async with RSSFetcher(lookback_hours=LOOKBACK_HOURS) as fetcher:
                rss_articles = await fetcher.fetch_all(rss_sources)
                all_articles.extend(rss_articles)
        
        # 2. arXiv Papers
        print("\n📄 Fetching arXiv papers...")
        async with ArxivFetcher(
            max_results=ARXIV_MAX_RESULTS,
            categories=ARXIV_CATEGORIES
        ) as fetcher:
            arxiv_articles = await fetcher.fetch_papers(lookback_hours=LOOKBACK_HOURS)
            all_articles.extend(arxiv_articles)
        
        # 3. Hugging Face
        print("\n🤗 Fetching Hugging Face content...")
        async with HuggingFaceFetcher() as fetcher:
            hf_articles = await fetcher.fetch_all()
            all_articles.extend(hf_articles)
        
        # 4. Web Scraping
        print("\n🌐 Scraping web sources...")
        async with WebScraper(lookback_hours=LOOKBACK_HOURS) as scraper:
            web_articles = await scraper.fetch_all()
            all_articles.extend(web_articles)
        
        # 5. LLM Tracker
        print("\n🔄 Checking LLM updates...")
        async with LLMTracker() as tracker:
            llm_articles = await tracker.check_all_providers()
            all_articles.extend(llm_articles)
        
        print(f"\n✅ Total fetched: {len(all_articles)} articles")
        return all_articles
    
    async def process_articles(self, articles: List) -> Dict[str, List]:
        """Process articles: deduplicate, categorize, summarize."""
        print("\n" + "=" * 50)
        print("⚙️ PROCESSING ARTICLES")
        print("=" * 50)
        
        # 1. Deduplicate
        print("\n🔍 Removing duplicates...")
        async with Deduplicator() as dedup:
            unique_articles = await dedup.filter_duplicates(articles)
            
            # Limit per source
            from collections import defaultdict
            by_source = defaultdict(list)
            for article in unique_articles:
                by_source[article.source].append(article)
            
            limited_articles = []
            for source, arts in by_source.items():
                limited_articles.extend(arts[:MAX_ARTICLES_PER_SOURCE])
            
            print(f"   After limiting: {len(limited_articles)} articles")
        
        # 2. Categorize
        print("\n📂 Categorizing...")
        categorizer = Categorizer()
        categorized = categorizer.categorize_all(limited_articles)
        
        # 3. Summarize and translate
        print("\n🌐 Summarizing and translating to Spanish...")
        summarizer = Summarizer()
        summarized = await summarizer.summarize_all(categorized)
        
        # 4. Group by category
        print("\n📊 Grouping by category...")
        grouped = categorizer.group_by_category(summarized)
        
        for category, arts in grouped.items():
            print(f"   {category}: {len(arts)} articles")
        
        return grouped
    
    async def send_digest(self, grouped_articles: Dict[str, List]) -> bool:
        """Compose and send email digest."""
        print("\n" + "=" * 50)
        print("📧 SENDING EMAIL DIGEST")
        print("=" * 50)
        
        # Compose email
        composer = EmailComposer()
        subject, html_body = composer.compose(grouped_articles)
        plain_text = composer.compose_plain_text(grouped_articles)
        
        print(f"\n📝 Subject: {subject}")
        
        # Get recipients
        recipients = [r.strip() for r in EMAIL_TO if r.strip()]
        
        if not recipients:
            print("⚠️ No recipients configured. Check EMAIL_TO in .env")
            # Save to file instead
            output_path = os.path.join(os.path.dirname(__file__), "latest_digest.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_body)
            print(f"💾 Saved digest to: {output_path}")
            return True
        
        print(f"📬 Sending to: {', '.join(recipients)}")
        
        # Send email
        sender = EmailSender()
        success = sender.send(
            to_addresses=recipients,
            subject=subject,
            html_body=html_body,
            plain_text_body=plain_text
        )
        
        if success:
            print("✅ Email sent successfully!")
            
            # Mark articles as sent
            async with Deduplicator() as dedup:
                for category, arts in grouped_articles.items():
                    await dedup.mark_batch_as_sent(arts)
        else:
            print("❌ Failed to send email")
        
        return success
    
    async def save_to_github_pages(self, grouped_articles: Dict[str, List]) -> bool:
        """Save digest as HTML to docs/ folder for GitHub Pages."""
        print("\n" + "=" * 50)
        print("📄 SAVING TO GITHUB PAGES")
        print("=" * 50)
        
        # Compose HTML
        composer = EmailComposer()
        subject, html_body = composer.compose(grouped_articles)
        
        # Save to docs/index.html
        docs_dir = os.path.join(os.path.dirname(__file__), "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        output_path = os.path.join(docs_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        
        print(f"✅ Saved to: {output_path}")
        
        # Also save archive copy with date
        date_str = datetime.now().strftime("%Y-%m-%d")
        archive_path = os.path.join(docs_dir, f"digest-{date_str}.html")
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        
        print(f"📁 Archive: {archive_path}")
        
        return True
    
    async def run(self, github_pages: bool = False) -> bool:
        """Run the complete pipeline."""
        print("\n" + "=" * 60)
        print("🤖 AI NEWS AGGREGATOR - Starting pipeline")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Fetch
            articles = await self.fetch_all_sources()
            
            if not articles:
                print("\n⚠️ No articles fetched. Check your internet connection.")
                return False
            
            # Process
            grouped = await self.process_articles(articles)
            
            if not grouped:
                print("\n📭 No new articles to send today.")
                return True
            
            # Output (GitHub Pages or Email)
            if github_pages:
                success = await self.save_to_github_pages(grouped)
            else:
                success = await self.send_digest(grouped)
            
            print("\n" + "=" * 60)
            print("🏁 Pipeline completed!")
            print("=" * 60)
            
            return success
            
        except Exception as e:
            print(f"\n❌ Error in pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False


def run_aggregator(github_pages: bool = False):
    """Synchronous wrapper for the aggregator."""
    aggregator = AINewsAggregator()
    asyncio.run(aggregator.run(github_pages=github_pages))


def run_scheduled():
    """Run the aggregator on a schedule."""
    print(f"\n⏰ Scheduler started. Will run daily at {SEND_HOUR:02d}:{SEND_MINUTE:02d}")
    print("   Press Ctrl+C to stop.\n")
    
    # Schedule the job
    schedule_time = f"{SEND_HOUR:02d}:{SEND_MINUTE:02d}"
    schedule.every().day.at(schedule_time).do(run_aggregator)
    
    # Run immediately on start (optional)
    print("🚀 Running initial digest...")
    run_aggregator()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def test_email():
    """Test email configuration."""
    from email_system.sender import EmailSender
    sender = EmailSender()
    success = sender.send_test()
    print(f"\nTest result: {'✅ Success' if success else '❌ Failed'}")


def main():
    """Main entry point with CLI."""
    parser = argparse.ArgumentParser(
        description="AI News Aggregator - Daily Digest Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                 # Run once (manual, saves to file)
  python main.py --schedule      # Run on schedule (8 AM daily)
  python main.py --github-pages  # Run and save to docs/ for GitHub Pages
  python main.py --test          # Test email configuration
        """
    )
    
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on schedule (daily at configured time)"
    )
    
    parser.add_argument(
        "--github-pages",
        action="store_true",
        help="Save output to docs/index.html for GitHub Pages"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test email configuration"
    )
    
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Send test email"
    )
    
    args = parser.parse_args()
    
    if args.test or args.test_email:
        test_email()
    elif args.schedule:
        run_scheduled()
    else:
        run_aggregator(github_pages=args.github_pages)


if __name__ == "__main__":
    main()

