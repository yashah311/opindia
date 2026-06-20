"""
Convert HTML to PDF using Playwright with optimized persistent browser contexts
"""
import logging
import os
import html
import base64
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from config import FONTS_DIR

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.font_path = os.path.join(FONTS_DIR, 'NotoSansGujarati-Regular.ttf')
        self._font_base64 = None
        self.playwright_context = None
        self.browser = None

    async def start_browser(self):
        if not self.browser:
            self.playwright_context = await async_playwright().start()
            self.browser = await self.playwright_context.chromium.launch(
                args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            logger.info("🤖 Shared Headless Chromium Session Context Active.")

    async def close_browser(self):
        if self.browser:
            await self.browser.close()
            await self.playwright_context.stop()
            self.browser = None
            self.playwright_context = None
            logger.info("🛑 Shared Headless Chromium Session Context Closed.")

    def _get_font_base64(self) -> str:
        if self._font_base64 is None:
            if os.path.exists(self.font_path):
                with open(self.font_path, "rb") as font_file:
                    encoded = base64.b64encode(font_file.read()).decode('utf-8')
                    self._font_base64 = f"data:font/ttf;charset=utf-8;base64,{encoded}"
            else:
                self._font_base64 = ""
        return self._font_base64
    def get_styled_html(self, article_html, article_url):
        soup = BeautifulSoup(article_html, 'html.parser')
        author_name, pub_date = "ઑપઇન્ડિયા સ્ટાફ", "June 2026"
        
        author_elem = soup.find(class_=re.compile(r'td-post-author-name|author', re.I))
        if author_elem:
            extracted_author = author_elem.get_text(strip=True)
            if extracted_author and len(extracted_author) < 50:
                author_name = extracted_author
                
        date_elem = soup.find('time') or soup.find(class_=re.compile(r'td-post-date|entry-date', re.I))
        if date_elem:
            pub_date = date_elem.get_text(strip=True)
        
        article_title = "ઑપઇન્ડિયા આર્કાઇવ લેખ"
        h1_tag = soup.find('h1')
        if h1_tag:
            article_title = h1_tag.get_text(strip=True)

        content_container = soup.find(class_=re.compile(r'td-post-content|entry-content|article-body|td-ss-main-content', re.I))
        paragraphs_html = []
        search_scope = content_container if content_container else soup
        
        for p_tag in search_scope.find_all(['p', 'h2', 'h3', 'h4']):
            p_text = p_tag.get_text(strip=True)
            if not p_text or any(word in p_text for word in ['- Advertisement -', 'જાહેરાત', 'जाहरात', 'Photo:', 'Source:']):
                continue
            safe_text = html.escape(p_text)
            if p_tag.name in ['h2', 'h3', 'h4']:
                paragraphs_html.append(f"<h2>{safe_text}</h2>")
            else:
                paragraphs_html.append(f"<p>{safe_text}</p>")

        clean_story_body = "\n".join(paragraphs_html)
        font_src = self._get_font_base64()
            
        css = f"""
        <style>
            @font-face {{ font-family: 'Gujarati'; src: url('{font_src}') format('truetype'); }}
            body {{ font-family: 'Gujarati', sans-serif; margin: 0; padding: 0; background: white; color: #111; line-height: 1.6; font-size: 11pt; }}
            .article-header-block {{ margin-bottom: 22px; border-bottom: 2px solid #111; padding-bottom: 10px; }}
            .article-main-title {{ font-size: 16pt !important; font-weight: bold !important; color: #000 !important; }}
            .meta-row {{ font-size: 10.5pt; color: #222; margin: 4px 0; }}
            h2, h3, h4 {{ font-family: 'Gujarati', sans-serif; margin: 18px 0 8px 0 !important; color: #000; page-break-after: avoid; break-inside: avoid; }}
            p {{ margin: 12px 0 !important; word-wrap: break-word !important; display: block !important; }}
        </style>
        """
        return f"""<!DOCTYPE html><html lang="gu"><head><meta charset="UTF-8">{css}</head>
        <body>
            <div class="article-header-block">
                <div class="article-main-title">Article Title: {html.escape(article_title)}</div>
                <div class="meta-row"><b>Author:</b> {html.escape(author_name)}</div>
                <div class="meta-row"><b>Date:</b> {html.escape(pub_date)}</div>
            </div>
            {clean_story_body}
        </body></html>"""

    async def html_to_pdf(self, html_content, output_pdf_path, article_url):
        try:
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
            styled_html = self.get_styled_html(html_content, article_url)
            
            if not self.browser:
                await self.start_browser()
                
            page = await self.browser.new_page()
            await page.set_content(styled_html, wait_until='domcontentloaded')
            await page.pdf(
                path=output_pdf_path, format='A4',
                margin={'top': '15mm', 'bottom': '15mm', 'left': '15mm', 'right': '15mm'},
                print_background=True
            )
            await page.close()
            return True
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return False
    
    def convert_sync(self, html_content, output_pdf_path, article_url):
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.html_to_pdf(html_content, output_pdf_path, article_url), loop)
            return future.result()
        return loop.run_until_complete(self.html_to_pdf(html_content, output_pdf_path, article_url))
