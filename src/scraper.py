import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Optional, Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversityScraper:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_page(self, url: str, use_selenium: bool = False) -> Optional[str]:
        """Fetch webpage content"""
        try:
            if use_selenium:
                return self._fetch_with_selenium(url)
            else:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """Use Selenium for JavaScript-heavy sites"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            return driver.page_source
        except TimeoutException:
            logger.warning(f"Timeout loading {url}")
            return driver.page_source
        except Exception as e:
            logger.error(f"Selenium error: {e}")
            return None
        finally:
            driver.quit()
    
    def scrape_news(self, university_config) -> List[Dict]:
        """Scrape news articles from university website"""
        html = self.fetch_page(university_config.news_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        
        # Find articles using configured selectors
        article_elements = soup.select(university_config.selectors.get('news_articles', ''))
        
        for element in article_elements[:10]:  # Limit to 10 articles
            try:
                title_elem = element.select_one(university_config.selectors.get('news_title', ''))
                date_elem = element.select_one(university_config.selectors.get('news_date', ''))
                content_elem = element.select_one(university_config.selectors.get('news_content', ''))
                
                if title_elem:
                    article = {
                        'university': university_config.name,
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', '') if title_elem.get('href') else '',
                        'date': date_elem.get_text(strip=True) if date_elem else '',
                        'content': content_elem.get_text(strip=True) if content_elem else '',
                        'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Make URL absolute if relative
                    if article['url'] and not article['url'].startswith('http'):
                        article['url'] = university_config.base_url + article['url']
                    
                    articles.append(article)
            except Exception as e:
                logger.error(f"Error parsing article: {e}")
                continue
        
        return articles
    
    def scrape_applications(self, university_config) -> List[Dict]:
        """Scrape application information and deadlines"""
        html = self.fetch_page(university_config.applications_url, use_selenium=True)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        deadlines = []
        
        # Try to find deadline information
        deadline_elements = soup.select(university_config.selectors.get('application_deadlines', ''))
        
        for element in deadline_elements:
            try:
                # Extract text and look for date patterns
                text = element.get_text(strip=True)
                if any(keyword in text.lower() for keyword in ['deadline', 'closing', 'apply by', 'due']):
                    deadline = {
                        'university': university_config.name,
                        'info': text,
                        'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    deadlines.append(deadline)
            except Exception as e:
                logger.error(f"Error parsing deadline: {e}")
                continue
        
        return deadlines