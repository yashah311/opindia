"""
Main entry point orchestrator - OpIndia Gujarati News Archive Scraper
"""
import logging
import argparse
import sys
import os
import glob
import asyncio
from datetime import datetime
from config import LOG_FILE, CATEGORIES, HTML_CACHE_DIR, PDF_CACHE_DIR

# Ensure log directory exists before initializing file handler
log_dir = os.path.dirname(LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_fonts():
    """Download and setup true raw binary Gujarati fonts if missing"""
    from config import FONTS_DIR
    font_path = os.path.join(FONTS_DIR, 'NotoSansGujarati-Regular.ttf')
    os.makedirs(FONTS_DIR, exist_ok=True)
    
    if os.path.exists(font_path) and os.path.getsize(font_path) > 10000:
        logger.info("✓ Gujarati font already installed and validated.")
        return True
    
    logger.info("Downloading raw Gujarati font binary from GitHub repositories...")
    try:
        import urllib.request
        url = 'https://github.com'
        urllib.request.urlretrieve(url, font_path)
        logger.info(f"✓ Font downloaded successfully: {font_path}")
        return True
    except Exception as e:
        logger.error(f"Could not download font asset: {e}")
        return False

def run_workflow(target_category='politics', max_pages=2):
    """Executes discovery, download, and conversion steps per category cleanly"""
    logger.info("\n" + "="*60)
    logger.info(f"PROCESSING LIFECYCLE: Category [{target_category.upper()}]")
    logger.info("="*60)
    
    setup_fonts()
    
    # 1. Discovery URLs
    from category_scraper import CategoryScraper
    category_scraper = CategoryScraper()
    urls = category_scraper.scrape_all_categories(specific_category=target_category.lower(), max_pages=max_pages)
    
    # Pack nested content parameters out of the scraper module data mappings
    target_dict = urls.get('discovered_urls', urls) if 'discovered_urls' in urls else urls
    active_urls = target_dict.get(target_category.lower(), [])
    if isinstance(active_urls, dict): active_urls = list(active_urls.keys())
    
    if not active_urls:
        logger.warning(f"No URLs returned for execution tier: {target_category}")
        return False
        
    # 2. Download Articles
    from article_scraper import ArticleScraper
    article_scraper = ArticleScraper()
    article_scraper.download_all(urls)
    
    # 3. Clean and Isolate HTML
    from html_cleaner import HTMLCleaner
    cleaner = HTMLCleaner()
    category_html_dir = os.path.join(HTML_CACHE_DIR, target_category.lower())
    html_files = glob.glob(os.path.join(category_html_dir, "*.html"))
    
    logger.info(f"Refining HTML structures inside cache path: {category_html_dir}")
    for html_path in html_files:
        content = cleaner.read_cached_html(html_path)
        if content and "<html" not in content.lower(): # Double-clean protection rule
            cleaned = cleaner.clean_html(content, html_path)
            if cleaned: cleaner.save_cleaned_html(cleaned, html_path)

    # 4. Convert Cached HTML items into Individual PDFs via Persistent Browser
    from pdf_generator import PDFGenerator
    category_pdf_output_dir = os.path.join(PDF_CACHE_DIR, target_category.lower())
    os.makedirs(category_pdf_output_dir, exist_ok=True)
    
    generator = PDFGenerator()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        asyncio.run_coroutine_threadsafe(generator.start_browser(), loop).result()
    else:
        loop.run_until_complete(generator.start_browser())
        
    try:
        for idx, html_path in enumerate(html_files, 1):
            filename = os.path.basename(html_path)
            
            # FIX: Extract only the string name by adding [0] index boundary rules
            base_name = os.path.splitext(filename)[0]
            output_pdf_path = os.path.join(category_pdf_output_dir, f"{base_name}.pdf")
            
            article_url = active_urls[idx-1].get('url', 'https://opindia.com') if isinstance(active_urls[idx-1], dict) else active_urls[idx-1]
            
            logger.info(f"⏳ Generating Document [{idx}/{len(html_files)}]: {base_name}.pdf")
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            generator.convert_sync(html_content, output_pdf_path, article_url)

    finally:
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(generator.close_browser(), loop).result()
        else:
            loop.run_until_complete(generator.close_browser())
            
    # 5. Merge into Monthly PDF Booklet Compilation
    from pdf_merger_monthly import PDFMergerMonthly
    merger = PDFMergerMonthly()
    merger.merge_by_month(target_category.lower())
    return True

def main():
    parser = argparse.ArgumentParser(description='OpIndia Gujarati News Archive Generator - Fire and Forget')
    parser.add_argument('--demo', action='store_true', help='Generate 1 sample PDF (Gujarat, 2 pages)')
    parser.add_argument('--all', action='store_true', help='Process all categories sequentially')
    parser.add_argument('--category', type=str, help='Specific category tag to process (e.g. gujarat, politics)')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--max-pages', type=int, default=2, help='Max pages to grab during loops')

    args = parser.parse_args()
    
    if args.demo:
        run_workflow(target_category='gujarat', max_pages=2)
    elif args.category:
        run_workflow(target_category=args.category.lower(), max_pages=args.max_pages)
    elif args.all:
        for cat in CATEGORIES.keys():
            run_workflow(target_category=cat.lower(), max_pages=args.max_pages)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
