import schedule
import time
import logging
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)

class UniversityAgent:
    def __init__(self, scraper, db_manager, notifier):
        self.scraper = scraper
        self.db_manager = db_manager
        self.notifier = notifier
        self.universities = []
        
    def load_universities(self, universities_config):
        """Load university configurations"""
        self.universities = universities_config
    
    def run_scraping_cycle(self):
        """Run one complete scraping cycle"""
        logger.info(f"Starting scraping cycle at {datetime.now()}")
        
        all_new_articles = []
        all_new_deadlines = []
        
        for uni_config in self.universities:
            try:
                logger.info(f"Scraping {uni_config.name}...")
                
                # Scrape news
                articles = self.scraper.scrape_news(uni_config)
                new_articles = self.db_manager.save_news_articles(articles)
                all_new_articles.extend(new_articles)
                
                # Scrape application deadlines
                deadlines = self.scraper.scrape_applications(uni_config)
                new_deadlines = self.db_manager.save_deadlines(deadlines)
                all_new_deadlines.extend(new_deadlines)
                
                logger.info(f"  Found {len(articles)} articles ({len(new_articles)} new)")
                logger.info(f"  Found {len(deadlines)} deadlines ({len(new_deadlines)} new)")
                
                # Small delay between universities
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping {uni_config.name}: {e}")
                continue
        
        # Send notifications
        if all_new_articles or all_new_deadlines:
            self.notifier.send_console_notification(all_new_articles, all_new_deadlines)
            
            # Email notification (if configured)
            if all_new_articles:
                email_content = self.notifier.format_news_email(all_new_articles)
                if email_content:
                    self.notifier.send_email_notification(
                        subject="New University News Updates",
                        content=email_content,
                        recipients=["your-email@example.com"]
                    )
        
        logger.info(f"Scraping cycle completed at {datetime.now()}")
        return len(all_new_articles) + len(all_new_deadlines)
    
    def run_continuously(self, interval_hours: int = 6):
        """Run the agent continuously on a schedule"""
        logger.info(f"Starting agent with {interval_hours}-hour intervals")
        
        # Run immediately
        self.run_scraping_cycle()
        
        # Schedule regular runs
        schedule.every(interval_hours).hours.do(self.run_scraping_cycle)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")