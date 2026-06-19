"""
Convert HTML articles to PDF with zero content loss, full A4 formatting, and hidden web UI
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
        """Inject clean full-width CSS styles while hiding specific web remnants to keep text safe"""
        
        soup = BeautifulSoup(article_html, 'html.parser')
        
        # આર્ટિકલના ટાઇટલ (H1) ને શોધો અને સાચવો
        article_title = "ઑપઇન્ડિયા આર્કાઇવ લેખ"
        h1_tag = soup.find('h1')
        if h1_tag:
            article_title = h1_tag.get_text(strip=True)
            
        clean_text = soup.get_text(' ')
        
        # મૂળભૂત ડિફોલ્ટ વેલ્યુ સેટ કરો
        author_name = "ઑપઇન્ડિયા સ્ટાફ"
        pub_date = "June 2026"
        
        # ગુજરાતી તારીખ અને અંગ્રેજી લેખકના નામની સચોટ પેટર્ન પકડો
        meta_match = re.search(r'(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})\s*(?:\n|\s)*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', clean_text)
        if meta_match:
            pub_date = meta_match.group(1).strip()
            author_name = meta_match.group(2).strip()
        else:
            secondary_match = re.search(r'([A-Za-z\s]+)\s*-\s*(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})', clean_text)
            if secondary_match:
                author_name = secondary_match.group(1).strip()
                pub_date = secondary_match.group(2).strip()

        # લખાણ સુરક્ષિત રાખવા માટે આખી બોડી ટ્રીને સ્ટ્રિંગમાં કન્વર્ટ કરો
        pure_body_content = str(soup)
            
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
                margin-bottom: 25px;
                border-bottom: 2px solid #222;
                padding-bottom: 12px;
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
                color: #333;
                margin: 4px 0;
                text-align: left !important;
            }}
            
            .meta-label {{
                font-weight: bold;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                font-family: 'Gujarati', sans-serif;
                margin: 20px 0 10px 0 !important;
                line-height: 1.4 !important;
                color: #000;
                text-align: left !important;
                width: 100% !important;
            }}
            
            p {{
                margin: 12px 0 !important;
                padding: 0 !important;
                text-align: left !important; /* ફૂલ-પેજ લેફ્ટ અલાઈન જેથી કટિંગ પ્રશ્નો ન થાય */
                word-wrap: break-word !important;
                width: 100% !important;
                display: block !important;
            }}
            
            /* === CSS ઇન્જેક્શન ફિક્સ: લખાણ ડિલીટ કર્યા વગર માત્ર વેબ બેનર્સને હાઇડ કરો === */
            img, svg, video, figure, header, footer, hr,
            .td-header-menu-wrap, .td-crumbs, .td-post-sharing, .td-category-pills,
            [class*="sharing"], [class*="crumbs"], [class*="advertisement"] {{
                display: none !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                visibility: hidden !important;
                opacity: 0 !important;
            }}
            
            .article-footer {{
                margin-top: 35px;
                border-top: 1px dashed #aaa;
                padding-top: 10px;
                font-size: 9pt;
                color: #555;
                width: 100%;
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
        
        footer = f"""
        <div class="article-footer">
            <p>Archived: OpIndia Gujarati News Archive</p>
        </div>
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
            {meta_html}
            {pure_body_content}
            {footer}
        </body>
        </html>
        """
    async def html_to_pdf(self, html_content, output_pdf_path, article_url):
        """Convert HTML to PDF using Playwright with optimized full-canvas printable margins"""
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
                    # આર્કાઇવ પ્રિન્ટિંગ માટે સ્ટાન્ડર્ડ માર્જિન સેટઅપ
                    margin={'top': '15mm', 'bottom': '15mm', 'left': '15mm', 'right': '15mm'},
                    print_background=True
                )
                
                await browser.close()
                logger.info(f"✓ Generated Full-Canvas Text PDF: {output_pdf_path}")
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
