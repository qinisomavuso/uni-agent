import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Dict
import os

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self, config):
        self.config = config
    
    def send_email_notification(self, subject: str, content: str, recipients: List[str]):
        """Send email notification"""
        if not self.config.EMAIL_ENABLED:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_SENDER
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'html'))
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipients}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def format_news_email(self, new_articles: List[Dict]) -> str:
        """Format news articles for email"""
        if not new_articles:
            return ""
        
        html = "<h2>New University News Updates</h2>"
        
        # Group by university
        by_university = {}
        for article in new_articles:
            uni = article['university']
            if uni not in by_university:
                by_university[uni] = []
            by_university[uni].append(article)
        
        for uni, articles in by_university.items():
            html += f"<h3>{uni}</h3>"
            html += "<ul>"
            for article in articles:
                html += f'<li><a href="{article["url"]}">{article["title"]}</a>'
                if article['date']:
                    html += f' ({article["date"]})'
                html += "</li>"
            html += "</ul>"
        
        return html
    
    def send_console_notification(self, new_articles: List[Dict], new_deadlines: List[Dict]):
        """Print notification to console"""
        if new_articles:
            print("\n" + "="*60)
            print("📰 NEW UNIVERSITY NEWS FOUND")
            print("="*60)
            for article in new_articles:
                print(f"\n🏛️  {article['university']}")
                print(f"📝 {article['title']}")
                if article['date']:
                    print(f"📅 {article['date']}")
                if article['url']:
                    print(f"🔗 {article['url']}")
        
        if new_deadlines:
            print("\n" + "="*60)
            print("⏰ NEW APPLICATION DEADLINES")
            print("="*60)
            for deadline in new_deadlines:
                print(f"\n🏛️  {deadline['university']}")
                print(f"📋 {deadline['info']}")