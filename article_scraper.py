"""
Download and cache article HTML with metadata tagging capabilities
"""
import json
import time
import logging
import os
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from config import (
    BASE_URL, USER_AGENT, RATE_LIMIT_DELAY, REQUEST_TIMEOUT,
    MAX_RETRIES, RETRY_BACKOFF, HTML_CACHE_DIR, PROGRESS_FILE
)

logger = logging.getLogger(__name__)

class ArticleScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    def get_cache_path(self, url, category):
        """Generate cache file path from URL"""
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        category_dir = os.path.join(HTML_CACHE_DIR, category)
        os.makedirs(category_dir, exist_ok=True)
        return os.path.join(category_dir, f"{url_hash}.html")
    
    def cache_exists(self, url, category):
        """Check if article is already cached"""
        return os.path.exists(self.get_cache_path(url, category))
    
    def download_article(self, url, category, retry_count=0):
        """Download and cache article HTML with injected meta layout rows"""
        try:
            if self.cache_exists(url, category):
                logger.debug(f"Using cached: {url}")
                return True
            
            logger.info(f"Downloading: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                if retry_count < MAX_RETRIES:
                    wait_time = RATE_LIMIT_DELAY * (RETRY_BACKOFF ** retry_count)
                    logger.warning(f"Status {response.status_code}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    return self.download_article(url, category, retry_count + 1)
                else:
                    logger.error(f"Failed after {MAX_RETRIES} retries: {url}")
                    return False
            
            # === CRITICAL ENGINE IMPLEMENTATION: TAG SOURCE METADATA ===
            # Injecting a distinct tracking paragraph string at the very bottom of the page content tree
            raw_html = response.text
            meta_payload = {
                'url': url,
                'category': category,
                'scraped_date': datetime.now().isoformat()
            }
            tagged_html = f"{raw_html}\n<p class=\"metadata_footer\">Source: {repr(meta_payload)}</p>"
            # ==========================================================
            
            # Save to cache
            cache_path = self.get_cache_path(url, category)
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(tagged_html)
            
            logger.info(f"✓ Cached: {cache_path}")
            time.sleep(RATE_LIMIT_DELAY)
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            if retry_count < MAX_RETRIES:
                wait_time = RATE_LIMIT_DELAY * (RETRY_BACKOFF ** retry_count)
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self.download_article(url, category, retry_count + 1)
            return False
    def download_category(self, urls_by_category, category_key):
        """Download all articles for a category"""
        if category_key not in urls_by_category:
            logger.error(f"Category {category_key} not found in URLs")
            return 0
        
        urls = urls_by_category[category_key]
        logger.info(f"Downloading {len(urls)} articles for {category_key}...")
        
        success_count = 0
        for i, article in enumerate(urls, 1):
            url = article.get('url') if isinstance(article, dict) else article
            if not url:
                continue
            
            logger.info(f"[{i}/{len(urls)}] {url}")
            if self.download_article(url, category_key):
                success_count += 1
        
        logger.info(f"✓ Downloaded {success_count}/{len(urls)} articles for {category_key}")
        return success_count
    
    def download_all(self, urls_by_category):
        """Download all articles from all categories"""
        total_success = 0
        for category in urls_by_category.keys():
            count = self.download_category(urls_by_category, category)
            total_success += count
        
        logger.info(f"\n✓ Total downloaded: {total_success}")
        return total_success

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load discovered URLs from category_scraper.py
    from category_scraper import CategoryScraper
    category_scraper = CategoryScraper()
    urls_by_category = category_scraper.scrape_all_categories()
    
    # Download all
    scraper = ArticleScraper()
    scraper.download_all(urls_by_category)

if __name__ == '__main__':
    main()
