"""
Convert HTML articles to PDF
"""
import logging
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from config import FONTS_DIR, PDF_CACHE_DIR

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.font_path = os.path.join(FONTS_DIR, 'NotoSansGujarati-Regular.ttf')
    
    def get_styled_html(self, article_html, article_url):
        """Wrap article HTML with print-friendly styling"""
        css = f"""
        <style>
            @font-face {{
                font-family: 'Gujarati';
                src: url('file:///{self.font_path.replace(chr(92), "/")}') format('truetype');
            }}
            
            body {{
                font-family: 'Gujarati', sans-serif;
                margin: 20px;
                padding: 20px;
                background: white;
                color: #333;
                line-height: 1.6;
                font-size: 12pt;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                font-family: 'Gujarati', sans-serif;
                margin: 15px 0 10px 0;
            }}
            
            p {{
                margin: 10px 0;
                text-align: justify;
            }}
            
            a {{
                color: #0066cc;
                text-decoration: none;
            }}
            
            img {{
                max-width: 100%;
                height: auto;
                margin: 10px 0;
            }}
            
            .article-footer {{
                margin-top: 30px;
                border-top: 1px solid #ccc;
                padding-top: 10px;
                font-size: 10pt;
                color: #666;
            }}
            
            .page-break {{
                page-break-after: always;
            }}
        </style>
        """
        
        footer = f"""
        <div class="article-footer">
            <p>Source: <a href="{article_url}">{article_url}</a></p>
            <p>Archived: OpIndia Gujarati News Archive</p>
        </div>
        <div class="page-break"></div>
        """
        
        return f"""
        <!DOCTYPE html>
        <html lang="gu">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {css}
        </head>
        <body>
            {article_html}
            {footer}
        </body>
        </html>
        """
    
    async def html_to_pdf(self, html_content, output_pdf_path, article_url):
        """Convert HTML to PDF using Playwright"""
        try:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            
            styled_html = self.get_styled_html(html_content, article_url)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                await page.set_content(styled_html, wait_until='networkidle')
                await page.pdf(
                    path=output_pdf_path,
                    format='A4',
                    margin={'top': '10mm', 'bottom': '10mm', 'left': '10mm', 'right': '10mm'},
                    print_background=True
                )
                
                await browser.close()
                logger.info(f"✓ Generated PDF: {output_pdf_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return False
    
    def convert_sync(self, html_content, output_pdf_path, article_url):
        """Synchronous wrapper for HTML to PDF conversion"""
        try:
            asyncio.run(self.html_to_pdf(html_content, output_pdf_path, article_url))
            return True
        except Exception as e:
            logger.error(f"Error in PDF conversion: {e}")
            return False

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    import glob
    from html_cleaner import HTMLCleaner
    
    logger.info("Generating PDFs from cleaned HTML files...")
    cleaner = HTMLCleaner()
    generator = PDFGenerator()
    
    # Find all cleaned HTML files
    html_files = glob.glob(os.path.join(PDF_CACHE_DIR, '**', '*.html'), recursive=True)
    logger.info(f"Found {len(html_files)} HTML files to convert...")
    
    logger.info("PDF generation ready. Call from scraper.py for full batch processing.")

if __name__ == '__main__':
    main()
