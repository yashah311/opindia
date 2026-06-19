"""
Clean HTML: extract article content and remove ads/tracking
"""
import logging
import os
from trafilatura import extract
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HTMLCleaner:
    @staticmethod
    def clean_html(html_content, url):
        """
        Extract article content using Trafilatura
        Returns cleaned HTML with article content only
        """
        try:
            # Use trafilatura to extract main content
            extracted = extract(html_content, output_format='html', include_comments=False)
            
            if not extracted:
                logger.warning(f"Could not extract content from {url}")
                return None
            
            # Parse with BeautifulSoup for additional cleaning
            soup = BeautifulSoup(extracted, 'html.parser')
            
            # Remove unwanted tags
            for tag in soup.find_all(['script', 'style', 'meta', 'link', 'noscript']):
                tag.decompose()
            
            # Remove inline scripts and event handlers
            for tag in soup.find_all(True):
                for attr in ['onclick', 'onerror', 'onload', 'onmouseover']:
                    if tag.get(attr):
                        del tag[attr]
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Error cleaning HTML from {url}: {e}")
            return None
    
    @staticmethod
    def read_cached_html(cache_path):
        """Read cached HTML file"""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {cache_path}: {e}")
            return None
    
    @staticmethod
    def save_cleaned_html(cleaned_html, output_path):
        """Save cleaned HTML"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_html)
            logger.debug(f"Saved cleaned HTML: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving cleaned HTML: {e}")
            return False

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    from config import HTML_CACHE_DIR
    import glob
    
    cleaner = HTMLCleaner()
    
    # Process all cached HTML files
    html_files = glob.glob(os.path.join(HTML_CACHE_DIR, '**', '*.html'), recursive=True)
    logger.info(f"Cleaning {len(html_files)} HTML files...")
    
    for i, html_file in enumerate(html_files, 1):
        logger.info(f"[{i}/{len(html_files)}] Processing {html_file}")
        html_content = cleaner.read_cached_html(html_file)
        if html_content:
            cleaned = cleaner.clean_html(html_content, html_file)
            if cleaned:
                cleaner.save_cleaned_html(cleaned, html_file)

if __name__ == '__main__':
    main()
