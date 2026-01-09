import argparse
import sys
from tabulate import tabulate
import json
from src.config import load_universities_config, Config
from src.scraper import UniversityScraper
from src.database import DatabaseManager
from src.notifier import Notifier
from src.agent import UniversityAgent

def setup_cli():
    """Set up command line interface"""
    parser = argparse.ArgumentParser(description="South African University News Agent")
    
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the agent once"
    )
    
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a daemon with scheduled scraping"
    )
    
    parser.add_argument(
        "--show-news",
        type=int,
        nargs="?",
        const=10,
        help="Show recent news (optional: number of articles)"
    )
    
    parser.add_argument(
        "--university",
        type=str,
        help="Filter by university name"
    )
    
    parser.add_argument(
        "--show-deadlines",
        action="store_true",
        help="Show application deadlines"
    )
    
    parser.add_argument(
        "--update-universities",
        action="store_true",
        help="Update the list of universities from Wikipedia"
    )
    
    return parser.parse_args()

def show_recent_news(db_manager, limit=10, university=None):
    """Display recent news articles"""
    articles = db_manager.get_recent_news(limit, university)
    
    if not articles:
        print("No news articles found.")
        return
    
    table_data = []
    for article in articles:
        table_data.append([
            article.id,
            article.university[:20],
            article.title[:50] + "..." if len(article.title) > 50 else article.title,
            article.date[:10] if article.date else "",
            "🆕" if article.is_new else "👁️"
        ])
    
    headers = ["ID", "University", "Title", "Date", "Status"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    if len(articles) == limit:
        print(f"\nShowing {limit} most recent articles. Use --show-news N for more.")

def show_recent_vacancies(db_manager, limit=10, university=None):
    """Display recent job vacancies with links"""
    vacancies = db_manager.get_recent_vacancies(limit, university)
    
    if not vacancies:
        print("No vacancies found.")
        return
    
    print("\n" + "="*100)
    print("🏢 AVAILABLE UNIVERSITY VACANCIES")
    print("="*100 + "\n")
    
    for idx, vacancy in enumerate(vacancies, 1):
        print(f"{idx}. {vacancy.university}")
        print(f"   📌 Title: {vacancy.title}")
        if vacancy.date:
            print(f"   📅 Date: {vacancy.date}")
        if vacancy.description:
            desc = vacancy.description[:200] + "..." if len(vacancy.description) > 200 else vacancy.description
            print(f"   📝 Description: {desc}")
        if vacancy.url:
            print(f"   🔗 Apply Here: {vacancy.url}")
        print()
    
    if len(vacancies) == limit:
        print(f"Showing {limit} most recent vacancies. Use --show-vacancies N for more.")

def main_cli():
    """CLI entry point"""
    args = setup_cli()
    
    # Initialize components
    universities = load_universities_config()
    scraper = UniversityScraper(Config)
    db_manager = DatabaseManager(Config.DATABASE_URL)
    notifier = Notifier(Config)
    agent = UniversityAgent(scraper, db_manager, notifier)
    agent.load_universities(universities)
    
    if args.run:
        print("Running single scraping cycle...")
        new_items = agent.run_scraping_cycle()
        print(f"Found {new_items} new items.")
    
    elif args.daemon:
        print("Starting agent as daemon...")
        agent.run_continuously()
    
    elif args.show_news:
        show_recent_news(db_manager, args.show_news, args.university)
    
    elif args.show_vacancies:
        show_recent_vacancies(db_manager, args.show_vacancies, args.university)
    
    elif args.update_universities:
        print("Updating universities list from Wikipedia...")
        scraper = UniversityScraper(Config)
        universities = scraper.get_south_african_universities()
        # Save to json
        import json
        with open('data/universities.json', 'w') as f:
            json.dump({'universities': universities}, f, indent=4)
        print(f"Updated {len(universities)} universities.")
    
    elif args.show_deadlines:
        # Similar function for deadlines
        pass
    
    elif args.stats:
        # Show statistics
        pass
    
    else:
        print("University Agent - South African Universities Monitor")
        print("\nCommands:")
        print("  --run           : Run scraping once")
        print("  --daemon        : Run continuously")
        print("  --show-news N   : Show N recent articles")
        print("  --show-vacancies N : Show N recent vacancies with application links")
        print("  --update-universities : Update universities list from Wikipedia")
        print("  --university X  : Filter by university")
        print("  --stats         : Show statistics")

if __name__ == "__main__":
    main_cli()