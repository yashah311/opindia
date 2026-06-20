"""
Convert HTML articles to PDF with exact Date, Author, and Full-Canvas A4 Spacing
"""
import logging
import os
import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from config import FONTS_DIR, PDF_CACHE_DIR

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.font_path = os.path.join(FONTS_DIR, 'NotoSansGujarati-Regular.ttf')
    
    def get_styled_html(self, article_html, article_url):
        """Isolate core article body strings using precise text-only scraping boundaries"""
        
        soup = BeautifulSoup(article_html, 'html.parser')
        
        # 1. Surgically extract the true Author Name and Date strings from OpIndia's meta containers
        author_name = "ઑપઇન્ડિયા સ્ટાફ"
        pub_date = "June 2026"
        
        # Look for the explicit author name container classes used by the website template
        author_elem = soup.find(class_=re.compile(r'td-post-author-name|author', re.I))
        if author_elem:
            extracted_author = author_elem.get_text(strip=True)
            if extracted_author and len(extracted_author) < 50:
                author_name = extracted_author
                
        # Look for the explicit publication date container element metadata rows
        date_elem = soup.find('time', class_=re.compile(r'entry-date|updated|date', re.I))
        if not date_elem:
            date_elem = soup.find(class_=re.compile(r'td-post-date|entry-date', re.I))
            
        if date_elem:
            extracted_date = date_elem.get_text(strip=True)
            if extracted_date:
                pub_date = extracted_date
        
        # 2. Extract the true Article Title text string from the H1 tag element
        article_title = "ઑપઇન્ડિયા આર્કાઇવ લેખ"
        h1_tag = soup.find('h1')
        if h1_tag:
            article_title = h1_tag.get_text(strip=True)

        # 3. CRITICAL TEXT EXTRACTION FIX: Isolate ONLY the primary story content container wrapper
        # This bypasses all header menus, breadcrumbs, orange pills, calendar icons, and black boxes
        content_container = soup.find(class_=re.compile(r'td-post-content|entry-content|article-body', re.I))
        
        paragraphs_html = []
        if content_container:
            # Step through text paragraph tags inside the core content column grid container
            for p_tag in content_container.find_all(['p', 'h2', 'h3', 'h4']):
                p_text = p_tag.get_text(strip=True)
                
                # Drop blank lines and filter out boilerplate advertisement string phrases
                if not p_text or any(word in p_text for word in ['- Advertisement -', 'જાહેરાત', 'जाहरात', 'Photo:']):
                    continue
                    
                if p_tag.name in ['h2', 'h3', 'h4']:
                    paragraphs_html.append(f"<h2>{p_text}</h2>")
                else:
                    paragraphs_html.append(f"<p>{p_text}</p>")
        
        # Fallback to general loop text parsing checks if the primary container isn't resolved
        if not paragraphs_html:
            for p_tag in soup.find_all('p'):
                p_text = p_tag.get_text(strip=True)
                if p_text and not any(word in p_text for word in ['- Advertisement -', 'જાહેરાત', 'Source:']):
                    paragraphs_html.append(f"<p>{p_text}</p>")

        clean_story_body = "\n".join(paragraphs_html)
            
        css = f"""
        <style>
            @font-face {{
                font-family: 'Gujarati';
                src: url('file:///{self.font_path.replace(chr(92), "/")}') format('truetype');
            }}
            
            body {{
                font-family: 'Gujarati', sans-serif;
                margin: 0;
                padding: 0;
                background: white;
                color: #111;
                line-height: 1.6;
                font-size: 11pt;
                width: 100% !important;
            }}
            
            .article-header-block {{
                margin-bottom: 22px;
                border-bottom: 2px solid #111;
                padding-bottom: 10px;
                width: 100%;
            }}
            
            .article-main-title {{
                font-size: 16pt !important;
                font-weight: bold !important;
                line-height: 1.4 !important;
                margin: 0 0 10px 0 !important;
                color: #000 !important;
                text-align: left !important;
            }}
            
            .meta-row {{
                font-size: 10.5pt;
                color: #222;
                margin: 4px 0;
                text-align: left !important;
            }}
            
            .meta-label {{
                font-weight: bold;
            }}
            
            h2, h3, h4 {{
                font-family: 'Gujarati', sans-serif;
                margin: 18px 0 8px 0 !important;
                line-height: 1.4 !important;
                color: #000;
                text-align: left !important;
                width: 100% !important;
            }}
            
            p {{
                margin: 12px 0 !important;
                padding: 0 !important;
                text-align: left !important; /* Left alignment to prevent text cuts at margins */
                word-wrap: break-word !important;
                width: 100% !important;
                display: block !important;
            }}
        </style>
        """
        
        meta_html = f"""
        <div class="article-header-block">
            <div class="article-main-title">Article Title: {article_title}</div>
            <div class="meta-row"><span class="meta-label">Author:</span> {author_name}</div>
            <div class="meta-row"><span class="meta-label">Date:</span> {pub_date}</div>
        </div>
        """
        
        footer = ""
        
        return f"""
        <!DOCTYPE html>
        <html lang="gu">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {css}
        </head>
        <body>
            {meta_html}
            {clean_story_body}
            {footer}
        </body>
        </html>
        """
    async def html_to_pdf(self, html_content, output_pdf_path, article_url):
        """Convert HTML to PDF using Playwright with optimized A4 canvas margins"""
        try:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            styled_html = self.get_styled_html(html_content, article_url)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                await page.set_content(styled_html, wait_until='domcontentloaded')
                await page.pdf(
                    path=output_pdf_path,
                    format='A4',
                    margin={'top': '15mm', 'bottom': '15mm', 'left': '15mm', 'right': '15mm'},
                    print_background=True
                )
                
                await browser.close()
                logger.info(f"✓ Generated True Plain Text PDF: {output_pdf_path}")
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
