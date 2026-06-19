"""
Discover categories and extract all article URLs directly from the primary chronological grid feed
"""
import json
import time
import logging
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from config import (
    BASE_URL, USER_AGENT, RATE_LIMIT_DELAY, REQUEST_TIMEOUT,
    CATEGORIES, PROGRESS_FILE
)

logger = logging.getLogger(__name__)

class CategoryScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.articles = {}
        
    def load_progress(self):
        """Load previous scraping progress"""
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_progress(self, progress):
        """Save scraping progress"""
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def scrape_category(self, category_key, category_info, max_pages=None, is_demo_mode=False):
        """Scrape literal chronological stream articles from the primary layout grid column, ignoring featured carousels"""
        logger.info(f"Starting URL discovery for {category_key} ({category_info['name_english']})...")
        
        category_url = urljoin(BASE_URL, category_info['url'])
        articles = []
        page = 1
        consecutive_errors = 0
        
        while True:
            try:
                # Build pagination URL
                if page == 1:
                    url = category_url
                else:
                    url = f"{category_url}page/{page}/"
                
                logger.info(f"  Fetching page {page}: {url}")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.encoding = 'utf-8'
                
                if response.status_code != 200:
                    logger.warning(f"  Page {page} returned status {response.status_code}")
                    consecutive_errors += 1
                    if consecutive_errors > 3:
                        break
                    time.sleep(RATE_LIMIT_DELAY)
                    page += 1
                    continue
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # === SURGICAL SELECTOR: TARGET ONLY THE PRIMARY CHRONOLOGICAL CHANNELS ===
                # Step 1: Decompose entire header layout dropdown containers completely
                for header_menu in soup.find_all(class_=['td-header-menu-wrap', 'td-header-sp-container', 'td-mobile-nav']):
                    header_menu.decompose()
                
                # Step 2: Target the unique primary vertical layout element hosting the page content feed grid
                # This systematically ignores upper sliding hero widgets, trending carousels, and sidebars.
                main_grid = soup.find('div', class_='td-main-content-wrap')
                
                # Dynamic structural recovery fallback boundary check
                search_scope = main_grid if main_grid else soup
                
                article_links = search_scope.find_all('h3')
                if not article_links:
                    logger.info(f"  No more grid articles found. Stopping at page {page}")
                    break
                
                page_articles = 0
                for link_elem in article_links:
                    a_tag = link_elem.find('a')
                    if not a_tag or not a_tag.get('href'):
                        continue
                    
                    initial_url = a_tag.get('href')
                    article_title = a_tag.get_text(strip=True)
                    
                    # Prevent link duplicates within page collection operations
                    if any(item['url'] == initial_url for item in articles):
                        continue
                        
                    articles.append({
                        'url': initial_url,
                        'title': article_title,
                        'category': category_key,
                        'scraped_date': datetime.now().isoformat()
                    })
                    page_articles += 1
                    
                    # Cap page collections to literal grid length if container structure balloons
                    if page_articles >= 10:
                        break
                
                logger.info(f"  Page {page}: Found exactly {page_articles} real stream feed articles")
                consecutive_errors = 0
                
                time.sleep(RATE_LIMIT_DELAY)
                page += 1
                
                if max_pages and page > max_pages:
                    logger.info(f"  Reached max_pages limit ({max_pages})")
                    break
                    
            except Exception as e:
                logger.error(f"  Error on page {page}: {e}")
                consecutive_errors += 1
                if consecutive_errors > 3:
                    logger.warning(f"  Too many errors. Stopping category {category_key}")
                    break
                time.sleep(RATE_LIMIT_DELAY * 2)
                page += 1
        
        logger.info(f"✓ {category_key}: Found {len(articles)} total stream elements")
        return articles
    
    def scrape_all_categories(self, specific_category=None, max_pages=None):
        """Scrape all categories or a specific one"""
        progress = self.load_progress()
        categories_to_scrape = [specific_category] if specific_category else CATEGORIES.keys()
        
        for category_key in categories_to_scrape:
            if category_key not in CATEGORIES:
                logger.error(f"Unknown category: {category_key}")
                continue
            
            if progress.get(f'{category_key}_completed') and not specific_category:
                logger.info(f"Skipping {category_key} (already completed)")
                continue
            
            category_info = CATEGORIES[category_key]
            articles = self.scrape_category(category_key, category_info, max_pages, is_demo_mode=bool(specific_category))
            
            self.articles[category_key] = articles
            progress[f'{category_key}_completed'] = True
            progress[f'{category_key}_count'] = len(articles)
            progress['last_updated'] = datetime.now().isoformat()
            
            self.save_progress(progress)
        
        return self.articles

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = CategoryScraper()
    articles = scraper.scrape_all_categories()
    
    print(f"\n✓ Total articles discovered: {sum(len(v) for v in articles.values())}")
    for cat, arts in articles.items():
        print(f"  {cat}: {len(arts)} articles")

if __name__ == '__main__':
    main()
