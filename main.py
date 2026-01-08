import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import load_universities_config, Config
from src.scraper import UniversityScraper
from src.database import DatabaseManager
from src.notifier import Notifier
from src.agent import UniversityAgent
import logging

def setup_logging():
    """Configure logging"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/uni_agent.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configurations
        universities = load_universities_config()
        logger.info(f"Loaded {len(universities)} universities")
        
        # Initialize components
        scraper = UniversityScraper(Config)
        db_manager = DatabaseManager(Config.DATABASE_URL)
        notifier = Notifier(Config)
        
        # Create and run agent
        agent = UniversityAgent(scraper, db_manager, notifier)
        agent.load_universities(universities)
        
        # Choose mode
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            logger.info("Running single scraping cycle")
            agent.run_scraping_cycle()
        else:
            logger.info("Starting continuous agent")
            agent.run_continuously(interval_hours=6)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()