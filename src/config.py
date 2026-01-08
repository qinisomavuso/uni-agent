import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Dict
import json

load_dotenv()

@dataclass
class UniversityConfig:
    name: str
    base_url: str
    news_url: str
    applications_url: str
    selectors: Dict  # CSS selectors for scraping
    
class Config:
    # Database
    DATABASE_URL = "sqlite:///data/university_data.db"
    
    # Notification
    EMAIL_ENABLED = False
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    # Scraping
    REQUEST_TIMEOUT = 10
    USER_AGENT = "UniversityAgent/1.0 (+https://github.com/yourusername/uni-agent)"
    
    # Universities to monitor (we'll populate this)
    UNIVERSITIES: List[UniversityConfig] = []
    
import json

def load_universities_config():
    """Load university configurations from JSON file"""
    with open('data/universities.json', 'r') as f:
        data = json.load(f)
    
    Config.UNIVERSITIES = []
    for uni_data in data['universities']:
        uni = UniversityConfig(**uni_data)
        Config.UNIVERSITIES.append(uni)
    
    return Config.UNIVERSITIES