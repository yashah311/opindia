"""
Main orchestrator - Fire and forget scraper for OpIndia Gujarati News Archive
Usage:
    python scraper.py --demo              # Generate 1 sample PDF (Politics, 2 pages)
    python scraper.py --all               # Full run all categories
    python scraper.py --category politics # Specific category
    python scraper.py --resume            # Resume from checkpoint
"""
import logging
import argparse
import sys
import os
from datetime import datetime
from config import LOG_FILE, CATEGORIES

# Ensure log directory exists before initializing file handler
log_dir = os.path.dirname(LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# Reconfigure Windows console streams to handle UTF-8 symbols like '✓'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Setup logging with explicit UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_fonts():
    """Download and setup Gujarati fonts if needed"""
    from config import FONTS_DIR
    
    font_path = os.path.join(FONTS_DIR, 'NotoSansGujarati-Regular.ttf')
    
    if os.path.exists(font_path):
        logger.info("✓ Gujarati font already installed")
        return True
    
    logger.info("Downloading Gujarati font...")
    try:
        import urllib.request
        # Fixed URL to use the direct raw asset binary link
        url = 'https://github.com/openmaptiles/fonts/blob/master/noto-sans/NotoSansGujarati-Regular.ttf'
        urllib.request.urlretrieve(url, font_path)
        logger.info(f"✓ Font downloaded: {font_path}")
        return True
    except Exception as e:
        logger.error(f"Could not download font: {e}")
        logger.warning("Continuing anyway - may affect PDF text rendering")
        return False

def run_demo():
    """Generate ONE sample PDF (Politics category, ~10-20 articles)"""
    logger.info("\n" + "="*60)
    logger.info("DEMO MODE: Sample PDF Generation")
    logger.info("="*60)
    logger.info("This will generate 1 sample PDF from Politics category (~15 min)")
    logger.info("After approval, run: python scraper.py --all")
    logger.info("="*60)
    
    # Setup fonts
    logger.info("\n[1/4] Setting up fonts...")
    setup_fonts()
    
    # URL Discovery (Politics only, 2 pages max)
    logger.info("\n[2/4] Discovering article URLs (Politics category, 2 pages)...")
    from category_scraper import CategoryScraper
    category_scraper = CategoryScraper()
    
    urls = category_scraper.scrape_all_categories(
        specific_category='politics',
        max_pages=2
    )
    
    total_urls = sum(len(v) for v in urls.values())
    logger.info(f"✓ Found {total_urls} sample articles")
    
    if not urls or total_urls == 0:
        logger.error("No URLs found. Cannot generate sample.")
        return False
    
    # Download Articles
    logger.info("\n[3/4] Downloading & cleaning sample articles...")
    from article_scraper import ArticleScraper
    article_scraper = ArticleScraper()
    article_scraper.download_all(urls)
    
    # === DRIVER LAYER ENGINE: PROCESS CACHED HTML INTO INDIVIDUAL PDFs ===
    logger.info("\n[3.5/4] Generating individual article PDFs via Playwright...")
    from config import HTML_CACHE_DIR
    from pdf_generator import PDFGenerator
    import glob
    
    # Resolve exact path directories cleanly
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pol_html_dir = os.path.join(HTML_CACHE_DIR, 'politics')
    pol_pdf_output_dir = os.path.join(base_dir, 'cache', 'individual_pdfs', 'politics')
    os.makedirs(pol_pdf_output_dir, exist_ok=True)
    
    # Locate all underlying HTML files generated during the download phase
    html_files = glob.glob(os.path.join(pol_html_dir, "*.html"))
    logger.info(f"🚀 Found {len(html_files)} items to process in cache.")
    
    if not html_files:
        logger.error(f"❌ Aborting generation. No offline source files found inside {pol_html_dir}")
        return False
        
    generator = PDFGenerator()
    politics_urls = urls.get('politics', [])
    
    # Map raw list variables safely if it comes wrapped inside metadata dictionaries
    if isinstance(politics_urls, dict):
        politics_urls = list(politics_urls.keys())
        
    # Process files sequentially using the module's native sync wrapper block
    for idx, html_path in enumerate(html_files, 1):
        filename = os.path.basename(html_path)
        base_name = os.path.splitext(filename)[0]
        output_pdf_path = os.path.join(pol_pdf_output_dir, f"{base_name}.pdf")
        
        # Match URL metadata reference if available; fallback to source root string
        article_url = politics_urls[idx-1] if idx <= len(politics_urls) else "https://opindia.com"
        
        logger.info(f"⏳ Generating Document [{idx}/{len(html_files)}]: {base_name}")
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            generator.convert_sync(html_content, output_pdf_path, article_url)
        except Exception as f_err:
            logger.warning(f"   ⚠️ Skipping target component generation failure: {f_err}")
    # ====================================================================
    
    # Merge into sample PDF
    logger.info("\n[4/4] Generating sample monthly PDF...")
    from pdf_merger_monthly import PDFMergerMonthly
    merger = PDFMergerMonthly()
    merger.merge_all_categories()
    
    sample_pdf = os.path.join(
        os.path.dirname(__file__),
        'output', 'monthly_pdfs', 'Politics',
        f'OpIndia_Gujarati_Politics_{datetime.now().strftime("%Y-%m")}.pdf'
    )
    
    if os.path.exists(sample_pdf):
        file_size = os.path.getsize(sample_pdf) / (1024 * 1024)
        logger.info("\n" + "="*60)
        logger.info("✓ SAMPLE PDF GENERATED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info(f"Location: {sample_pdf}")
        logger.info(f"File Size: {file_size:.2f} MB")
        logger.info(f"Articles: {total_urls}")
        logger.info("\n📋 APPROVAL STEPS:")
        logger.info("1. Open the PDF and verify:")
        logger.info("   - Gujarati text renders correctly")
        logger.info("   - Cover page shows category and month")
        logger.info("   - Articles are readable and properly formatted")
        logger.info("   - No ads or tracking content")
        logger.info("\n2. If satisfied, run full archive:")
        logger.info("   python scraper.py --all")
        logger.info("   (This will archive ALL 14 categories)")
        logger.info("\n3. Full run will take ~4-6 hours")
        logger.info("="*60)
        return True
    else:
        logger.error("Failed to generate sample PDF")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='OpIndia Gujarati News Archive Generator - Fire and Forget',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scraper.py --demo                   # Generate 1 sample PDF for approval
  python scraper.py --all                    # Archive all categories (after demo approval)
  python scraper.py --category politics      # Archive only politics
  python scraper.py --resume                 # Resume from last checkpoint
  python scraper.py --all --max-pages 5      # Test with 5 pages per category
        """
    )
    
    parser.add_argument('--demo', action='store_true', help='Generate 1 sample PDF (Politics, 2 pages)')
    parser.add_argument('--all', action='store_true', help='Process all categories')
    parser.add_argument('--category', type=str, help='Specific category to process')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--max-pages', type=int, default=None, help='Max pages per category (for testing)')
    parser.add_argument('--skip-download', action='store_true', help='Skip HTML download phase')
    parser.add_argument('--skip-pdf', action='store_true', help='Skip PDF generation phase')
    
    args = parser.parse_args()
    
    # Demo mode
    if args.demo:
        success = run_demo()
        sys.exit(0 if success else 1)
    
    logger.info("="*60)
    logger.info("OpIndia Gujarati News Archive Generator")
    logger.info("="*60)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup fonts
    logger.info("\n[1/5] Setting up fonts...")
    setup_fonts()
    
    # URL Discovery
    logger.info("\n[2/5] Discovering article URLs...")
    from category_scraper import CategoryScraper
    category_scraper = CategoryScraper()
    
    if args.category:
        urls = category_scraper.scrape_all_categories(
            specific_category=args.category,
            max_pages=args.max_pages
        )
    else:
        urls = category_scraper.scrape_all_categories(max_pages=args.max_pages)
    
    total_urls = sum(len(v) for v in urls.values())
    logger.info(f"✓ Total URLs discovered: {total_urls}")
    
    if not urls or total_urls == 0:
        logger.warning("No URLs discovered. Exiting.")
        return
    
    # Download Articles
    if not args.skip_download:
        logger.info("\n[3/5] Downloading articles...")
        from article_scraper import ArticleScraper
        article_scraper = ArticleScraper()
        article_scraper.download_all(urls)
    else:
        logger.info("\n[3/5] Skipping article download (--skip-download)")
    
    # Clean HTML
    logger.info("\n[3.5/5] Cleaning HTML content...")
    from html_cleaner import HTMLCleaner
    cleaner = HTMLCleaner()
    logger.info("✓ HTML cleaning functions ready")
    
    # Generate PDFs
    if not args.skip_pdf:
        logger.info("\n[4/5] Generating individual PDFs...")
        logger.info("Note: PDF generation is resource-intensive")
        logger.info("Consider running with --skip-pdf and using Playwright separately for large batches")
    else:
        logger.info("\n[4/5] Skipping PDF generation (--skip-pdf)")
    
    # Merge Monthly PDFs
    logger.info("\n[5/5] Creating monthly PDFs per category...")
    from pdf_merger_monthly import PDFMergerMonthly
    merger = PDFMergerMonthly()
    merger.merge_all_categories()
    
    logger.info("\n" + "="*60)
    logger.info("✓ Archive generation complete!")
    logger.info(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    logger.info(f"\nOutput location: {os.path.join(os.getcwd(), 'output', 'monthly_pdfs')}")
    logger.info(f"Logs: {LOG_FILE}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Execution interrupted by user (Ctrl+C). Exiting cleanly...")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"\n💥 Script crashed unexpectedly: {e}", exc_info=True)
        sys.exit(1)

# """
# Main orchestrator - Fire and forget scraper for OpIndia Gujarati News Archive
# Usage:
#     python scraper.py --demo              # Generate 1 sample PDF (Politics, 2 pages)
#     python scraper.py --all               # Full run all categories
#     python scraper.py --category politics # Specific category
#     python scraper.py --resume            # Resume from checkpoint
# """
# import logging
# import argparse
# import sys
# import os
# from datetime import datetime
# from config import LOG_FILE, CATEGORIES

# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler(LOG_FILE),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# def setup_fonts():
#     """Download and setup Gujarati fonts if needed"""
#     from config import FONTS_DIR
    
#     font_path = os.path.join(FONTS_DIR, 'NotoSansGujarati-Regular.ttf')
    
#     if os.path.exists(font_path):
#         logger.info("✓ Gujarati font already installed")
#         return True
    
#     logger.info("Downloading Gujarati font...")
#     try:
#         import urllib.request
#         url = 'https://github.com/openmaptiles/fonts/blob/master/noto-sans/NotoSansGujarati-Regular.ttf'
#         urllib.request.urlretrieve(url, font_path)
#         logger.info(f"✓ Font downloaded: {font_path}")
#         return True
#     except Exception as e:
#         logger.error(f"Could not download font: {e}")
#         logger.warning("Continuing anyway - may affect PDF text rendering")
#         return False

# def run_demo():
#     """Generate ONE sample PDF (Politics category, ~10-20 articles)"""
#     logger.info("\n" + "="*60)
#     logger.info("DEMO MODE: Sample PDF Generation")
#     logger.info("="*60)
#     logger.info("This will generate 1 sample PDF from Politics category (~15 min)")
#     logger.info("After approval, run: python scraper.py --all")
#     logger.info("="*60)
    
#     # Setup fonts
#     logger.info("\n[1/4] Setting up fonts...")
#     setup_fonts()
    
#     # URL Discovery (Politics only, 2 pages max)
#     logger.info("\n[2/4] Discovering article URLs (Politics category, 2 pages)...")
#     from category_scraper import CategoryScraper
#     category_scraper = CategoryScraper()
    
#     urls = category_scraper.scrape_all_categories(
#         specific_category='politics',
#         max_pages=2
#     )
    
#     total_urls = sum(len(v) for v in urls.values())
#     logger.info(f"✓ Found {total_urls} sample articles")
    
#     if not urls or total_urls == 0:
#         logger.error("No URLs found. Cannot generate sample.")
#         return False
    
#     # Download Articles
#     logger.info("\n[3/4] Downloading & cleaning sample articles...")
#     from article_scraper import ArticleScraper
#     article_scraper = ArticleScraper()
#     article_scraper.download_all(urls)
    
#     # Merge into sample PDF
#     logger.info("\n[4/4] Generating sample monthly PDF...")
#     from pdf_merger_monthly import PDFMergerMonthly
#     merger = PDFMergerMonthly()
#     merger.merge_all_categories()
    
#     sample_pdf = os.path.join(
#         os.path.dirname(__file__),
#         'output', 'monthly_pdfs', 'Politics',
#         f'OpIndia_Gujarati_Politics_{datetime.now().strftime("%Y-%m")}.pdf'
#     )
    
#     if os.path.exists(sample_pdf):
#         file_size = os.path.getsize(sample_pdf) / (1024 * 1024)
#         logger.info("\n" + "="*60)
#         logger.info("✓ SAMPLE PDF GENERATED SUCCESSFULLY!")
#         logger.info("="*60)
#         logger.info(f"Location: {sample_pdf}")
#         logger.info(f"File Size: {file_size:.2f} MB")
#         logger.info(f"Articles: {total_urls}")
#         logger.info("\n📋 APPROVAL STEPS:")
#         logger.info("1. Open the PDF and verify:")
#         logger.info("   - Gujarati text renders correctly")
#         logger.info("   - Cover page shows category and month")
#         logger.info("   - Articles are readable and properly formatted")
#         logger.info("   - No ads or tracking content")
#         logger.info("\n2. If satisfied, run full archive:")
#         logger.info("   python scraper.py --all")
#         logger.info("   (This will archive ALL 14 categories)")
#         logger.info("\n3. Full run will take ~4-6 hours")
#         logger.info("="*60)
#         return True
#     else:
#         logger.error("Failed to generate sample PDF")
#         return False

# def main():
#     parser = argparse.ArgumentParser(
#         description='OpIndia Gujarati News Archive Generator - Fire and Forget',
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# Examples:
#   python scraper.py --demo                   # Generate 1 sample PDF for approval
#   python scraper.py --all                    # Archive all categories (after demo approval)
#   python scraper.py --category politics      # Archive only politics
#   python scraper.py --resume                 # Resume from last checkpoint
#   python scraper.py --all --max-pages 5      # Test with 5 pages per category
#         """
#     )
    
#     parser.add_argument('--demo', action='store_true', help='Generate 1 sample PDF (Politics, 2 pages)')
#     parser.add_argument('--all', action='store_true', help='Process all categories')
#     parser.add_argument('--category', type=str, help='Specific category to process')
#     parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
#     parser.add_argument('--max-pages', type=int, default=None, help='Max pages per category (for testing)')
#     parser.add_argument('--skip-download', action='store_true', help='Skip HTML download phase')
#     parser.add_argument('--skip-pdf', action='store_true', help='Skip PDF generation phase')
    
#     args = parser.parse_args()
    
#     # Demo mode
#     if args.demo:
#         success = run_demo()
#         sys.exit(0 if success else 1)
    
#     logger.info("="*60)
#     logger.info("OpIndia Gujarati News Archive Generator")
#     logger.info("="*60)
#     logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
#     # Setup fonts
#     logger.info("\n[1/5] Setting up fonts...")
#     setup_fonts()
    
#     # URL Discovery
#     logger.info("\n[2/5] Discovering article URLs...")
#     from category_scraper import CategoryScraper
#     category_scraper = CategoryScraper()
    
#     if args.category:
#         urls = category_scraper.scrape_all_categories(
#             specific_category=args.category,
#             max_pages=args.max_pages
#         )
#     else:
#         urls = category_scraper.scrape_all_categories(max_pages=args.max_pages)
    
#     total_urls = sum(len(v) for v in urls.values())
#     logger.info(f"✓ Total URLs discovered: {total_urls}")
    
#     if not urls or total_urls == 0:
#         logger.warning("No URLs discovered. Exiting.")
#         return
    
#     # Download Articles
#     if not args.skip_download:
#         logger.info("\n[3/5] Downloading articles...")
#         from article_scraper import ArticleScraper
#         article_scraper = ArticleScraper()
#         article_scraper.download_all(urls)
#     else:
#         logger.info("\n[3/5] Skipping article download (--skip-download)")
    
#     # Clean HTML
#     logger.info("\n[3.5/5] Cleaning HTML content...")
#     from html_cleaner import HTMLCleaner
#     cleaner = HTMLCleaner()
#     logger.info("✓ HTML cleaning functions ready")
    
#     # Generate PDFs
#     if not args.skip_pdf:
#         logger.info("\n[4/5] Generating individual PDFs...")
#         logger.info("Note: PDF generation is resource-intensive")
#         logger.info("Consider running with --skip-pdf and using Playwright separately for large batches")
#     else:
#         logger.info("\n[4/5] Skipping PDF generation (--skip-pdf)")
    
#     # Merge Monthly PDFs
#     logger.info("\n[5/5] Creating monthly PDFs per category...")
#     from pdf_merger_monthly import PDFMergerMonthly
#     merger = PDFMergerMonthly()
#     merger.merge_all_categories()
    
#     logger.info("\n" + "="*60)
#     logger.info("✓ Archive generation complete!")
#     logger.info(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     logger.info("="*60)
#     logger.info(f"\nOutput location: {os.path.join(os.getcwd(), 'output', 'monthly_pdfs')}")
#     logger.info(f"Logs: {LOG_FILE}")

# if __name__ == '__main__':
#     try:
#         main()
#     except KeyboardInterrupt:
#         logger.warning("\n⚠ Scraper interrupted by user")
#         sys.exit(1)
#     except Exception as e:
#         logger.error(f"\n✗ Fatal error: {e}", exc_info=True)
#         sys.exit(1)

