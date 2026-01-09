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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
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
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        try:
            driver.get(url)
            # Wait for content to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Additional wait for dynamic content
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
        html = self.fetch_page(university_config.news_url, use_selenium=True)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        
        # Find articles using configured selectors
        selector = university_config.selectors.get('news_articles', '')
        article_elements = soup.select(selector)
        logger.info(f"Found {len(article_elements)} article elements with selector '{selector}'")
        
        for element in article_elements[:10]:  # Limit to 10 articles
            try:
                title_elem = element.select_one(university_config.selectors.get('news_title', ''))
                if not title_elem:
                    logger.warning(f"No title found in element: {element.name} {element.get('class')}")
                    continue
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
    
    def scrape_vacancies(self, university_config) -> List[Dict]:
        """Scrape job vacancies from university website"""
        vacancies_url = university_config.vacancies_url or (university_config.base_url + '/vacancies')
        html = self.fetch_page(vacancies_url, use_selenium=True)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        vacancies = []
        
        # Find vacancy elements
        vacancy_elements = soup.select(university_config.selectors.get('vacancies', 'article, .vacancy, .job'))
        
        for element in vacancy_elements[:20]:  # Limit to 20
            try:
                title_elem = element.select_one(university_config.selectors.get('vacancy_title', 'h3, h2, a'))
                if not title_elem:
                    continue
                date_elem = element.select_one(university_config.selectors.get('vacancy_date', '.date, time'))
                desc_elem = element.select_one(university_config.selectors.get('vacancy_desc', 'p'))
                
                vacancy = {
                    'university': university_config.name,
                    'title': title_elem.get_text(strip=True),
                    'url': title_elem.get('href', '') if title_elem.get('href') else '',
                    'date': date_elem.get_text(strip=True) if date_elem else '',
                    'description': desc_elem.get_text(strip=True) if desc_elem else '',
                    'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                if vacancy['url'] and not vacancy['url'].startswith('http'):
                    vacancy['url'] = university_config.base_url + vacancy['url']
                
                vacancies.append(vacancy)
            except Exception as e:
                logger.error(f"Error parsing vacancy: {e}")
                continue
        
        return vacancies
    
    def get_south_african_universities(self) -> List[Dict]:
        """Scrape list of South African universities from Wikipedia"""
        url = "https://en.wikipedia.org/wiki/List_of_universities_in_South_Africa"
        html = self.fetch_page(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        universities = []
        
        # Find the table with universities
        table = soup.find('table', {'class': 'wikitable'})
        if not table:
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                website = cols[2].find('a')
                if website and website.get('href'):
                    site_url = website['href']
                    if not site_url.startswith('http'):
                        site_url = 'https:' + site_url
                    
                    universities.append({
                        'name': name,
                        'base_url': site_url,
                        'news_url': site_url + '/news',
                        'applications_url': site_url + '/apply',
                        'vacancies_url': site_url + '/vacancies',
                        'selectors': {
                            'news_articles': 'article',
                            'news_title': 'h2, h3',
                            'news_date': '.date, time',
                            'news_content': 'p',
                            'application_deadlines': 'table tr',
                            'vacancies': 'article, .vacancy',
                            'vacancy_title': 'h3, h2, a',
                            'vacancy_date': '.date, time',
                            'vacancy_desc': 'p'
                        }
                    })
        
        return universities