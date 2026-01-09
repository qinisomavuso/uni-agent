from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import hashlib

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True)
    article_hash = Column(String(64), unique=True, index=True)
    university = Column(String(100))
    title = Column(String(500))
    url = Column(String(1000))
    date = Column(String(100))
    content = Column(Text)
    scraped_at = Column(DateTime)
    is_new = Column(Integer, default=1)  # 1 = new, 0 = seen
    
    @staticmethod
    def generate_hash(title: str, university: str) -> str:
        """Generate unique hash for article"""
        content = f"{title}_{university}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()

class ApplicationDeadline(Base):
    __tablename__ = 'application_deadlines'
    
    id = Column(Integer, primary_key=True)
    deadline_hash = Column(String(64), unique=True, index=True)
    university = Column(String(100))
    info = Column(Text)
    scraped_at = Column(DateTime)
    is_new = Column(Integer, default=1)

class Vacancy(Base):
    __tablename__ = 'vacancies'
    
    id = Column(Integer, primary_key=True)
    vacancy_hash = Column(String(64), unique=True, index=True)
    university = Column(String(100))
    title = Column(String(500))
    url = Column(String(1000))
    date = Column(String(100))
    description = Column(Text)
    scraped_at = Column(DateTime)
    is_new = Column(Integer, default=1)  # 1 = new, 0 = seen

class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///data/university_data.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_news_articles(self, articles: list) -> list:
        """Save news articles, return only new ones"""
        session = self.Session()
        new_articles = []
        
        for article in articles:
            article_hash = NewsArticle.generate_hash(article['title'], article['university'])
            
            # Check if article already exists
            existing = session.query(NewsArticle).filter_by(article_hash=article_hash).first()
            
            if not existing:
                db_article = NewsArticle(
                    article_hash=article_hash,
                    university=article['university'],
                    title=article['title'],
                    url=article['url'],
                    date=article['date'],
                    content=article['content'],
                    scraped_at=datetime.strptime(article['scraped_at'], '%Y-%m-%d %H:%M:%S')
                )
                session.add(db_article)
                new_articles.append(article)
        
        session.commit()
        session.close()
        return new_articles
    
    def save_deadlines(self, deadlines: list) -> list:
        """Save application deadlines, return only new ones"""
        session = self.Session()
        new_deadlines = []
        
        for deadline in deadlines:
            deadline_hash = hashlib.sha256(
                f"{deadline['info']}_{deadline['university']}".encode('utf-8')
            ).hexdigest()
            
            existing = session.query(ApplicationDeadline).filter_by(deadline_hash=deadline_hash).first()
            
            if not existing:
                db_deadline = ApplicationDeadline(
                    deadline_hash=deadline_hash,
                    university=deadline['university'],
                    info=deadline['info'],
                    scraped_at=datetime.strptime(deadline['scraped_at'], '%Y-%m-%d %H:%M:%S')
                )
                session.add(db_deadline)
                new_deadlines.append(deadline)
        
        session.commit()
        session.close()
        return new_deadlines
    
    def save_vacancies(self, vacancies: list) -> list:
        """Save job vacancies, return only new ones"""
        session = self.Session()
        new_vacancies = []
        
        for vacancy in vacancies:
            vacancy_hash = hashlib.sha256(
                f"{vacancy['title']}_{vacancy['university']}".encode('utf-8')
            ).hexdigest()
            
            existing = session.query(Vacancy).filter_by(vacancy_hash=vacancy_hash).first()
            
            if not existing:
                db_vacancy = Vacancy(
                    vacancy_hash=vacancy_hash,
                    university=vacancy['university'],
                    title=vacancy['title'],
                    url=vacancy['url'],
                    date=vacancy['date'],
                    description=vacancy['description'],
                    scraped_at=datetime.strptime(vacancy['scraped_at'], '%Y-%m-%d %H:%M:%S')
                )
                session.add(db_vacancy)
                new_vacancies.append(vacancy)
        
        session.commit()
        session.close()
        return new_vacancies
    
    def get_recent_news(self, limit: int = 20, university: str = None):
        """Get recent news articles"""
        session = self.Session()
        query = session.query(NewsArticle).order_by(NewsArticle.scraped_at.desc())
        
        if university:
            query = query.filter_by(university=university)
        
        results = query.limit(limit).all()
        session.close()
        return results
    
    def get_recent_vacancies(self, limit: int = 20, university: str = None):
        """Get recent job vacancies"""
        session = self.Session()
        query = session.query(Vacancy).order_by(Vacancy.scraped_at.desc())
        
        if university:
            query = query.filter_by(university=university)
        
        results = query.limit(limit).all()
        session.close()
        return results
    
    def mark_as_seen(self, article_id: int):
        """Mark article as seen/read"""
        session = self.Session()
        article = session.query(NewsArticle).filter_by(id=article_id).first()
        if article:
            article.is_new = 0
            session.commit()
        session.close()