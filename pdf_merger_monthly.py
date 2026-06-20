"""
Group articles by publication month and merge into monthly PDFs per category continuously (Infinite Scroll)
"""
import logging
import os
import csv
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from PyPDF2 import PdfWriter, PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from config import PDF_CACHE_DIR, MONTHLY_PDF_DIR, METADATA_DIR, CATEGORIES, HTML_CACHE_DIR, PROGRESS_FILE

logger = logging.getLogger(__name__)

class PDFMergerMonthly:
    def __init__(self):
        self.metadata = []
    
    def create_cover_page(self, category_key, month_str, article_count):
        """Create cover page for monthly PDF"""
        try:
            category_info = CATEGORIES.get(category_key, {})
            category_name_english = category_info.get('name_english', category_key)
            
            output_dir = os.path.join(MONTHLY_PDF_DIR, category_name_english)
            os.makedirs(output_dir, exist_ok=True)
            
            cover_path = os.path.join(output_dir, f'cover_{month_str}.pdf')
            
            doc = SimpleDocTemplate(
                cover_path,
                pagesize=A4,
                rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
            )
            
            styles = getSampleStyleSheet()
            custom_style = ParagraphStyle(
                'CoverTitle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=18,
                textColor='#111111',
                spaceAfter=25,
                alignment=TA_CENTER
            )
            
            story = []
            story.append(Spacer(1, 2.5*inch))
            story.append(Paragraph("OpIndia Gujarati News Archive", custom_style))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(f"Category: {category_name_english}", custom_style))
            story.append(Paragraph(f"Month: {month_str}", custom_style))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(f"Total Articles: {article_count}", custom_style))
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(
                f"Archived on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ParagraphStyle('Footer1', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
            ))
            
            doc.build(story)
            return cover_path
        except Exception as e:
            logger.error(f"Error creating cover page: {e}")
            return None
    def merge_by_month(self, category_key):
        """Processes and compiles every file found in the category cache folder chronologically into a single layout"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            html_dir = os.path.join(HTML_CACHE_DIR, category_key.lower())
            
            # Setup final unified output path directories
            category_info = CATEGORIES.get(category_key, {})
            category_name_english = category_info.get('name_english', category_key)
            month_str = "2026-06"
            output_filename = f'OpIndia_Gujarati_{category_name_english}_{month_str}.pdf'
            output_path = os.path.join(MONTHLY_PDF_DIR, category_name_english, output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Load the pristine title and playlist dictionary array mapping states from progress data JSON
            ordered_articles_meta = []
            try:
                if os.path.exists(PROGRESS_FILE):
                    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    
                    discovered_list = progress_data.get('discovered_urls', {}).get(category_key, [])
                    if not discovered_list and category_key in progress_data:
                        discovered_list = progress_data[category_key]
                    if not discovered_list and 'politics' in progress_data:
                        discovered_list = progress_data['politics']
                        
                    for item in discovered_list:
                        if isinstance(item, dict):
                            url_str = item.get('url', '')
                            title_str = item.get('title', 'ઑપઇન્ડિયા લેખ')
                            if url_str:
                                url_hash = hashlib.md5(url_str.encode('utf-8')).hexdigest()[:8]
                                ordered_articles_meta.append({
                                    'hash': url_hash,
                                    'title': title_str,
                                    'url': url_str
                                })
            except Exception as p_err:
                logger.warning(f"Could not extract structural index mapping arrays: {p_err}")

            if not ordered_articles_meta:
                logger.error("❌ No discovered URL tracks found in progress data. Run category_scraper first.")
                return 0

            # === STITCHING ENGINE: GENERATE CONTINUOUS INFINITE SCROLL CANVAS HTML ===
            master_html_payload = ""
            valid_article_count = 0
            
            from pdf_generator import PDFGenerator
            generator = PDFGenerator()
            
            logger.info(f"🚀 Infinite Scroll Matrix: Compiling {len(ordered_articles_meta)} items into a single text flow layout...")
            
            for idx, meta in enumerate(ordered_urls_meta := ordered_articles_meta):
                html_path = os.path.join(html_dir, f"{meta['hash']}.html")
                
                if not os.path.exists(html_path):
                    continue
                    
                with open(html_path, 'r', encoding='utf-8') as f:
                    raw_html = f.read()
                
                # Strip metadata loops to clean up text channels
                clean_html_text = re.sub(r'<[^>]+>', ' ', raw_html)
                clean_html_text = ' '.join(clean_text := clean_html_text.split())
                
                # Highly flexible regex matching pattern to isolate the author and date strings from cleaned segments
                author_name = "ઑપઇન્ડિયા સ્ટાફ"
                pub_date = "June 2026"
                
                meta_match = re.search(r'(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})\s*[\s\u2502\u007c:-]\s*([A-Za-z\s]+)', clean_html_text)
                if not meta_match:
                    meta_match = re.search(r'([A-Za-z\s]+)\s*-\s*(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})', clean_html_text)
                    
                if meta_match:
                    if ',' in meta_match.group(1):
                        pub_date = meta_match.group(1).strip()
                        author_name = meta_match.group(2).strip()
                    else:
                        author_name = meta_match.group(1).strip()
                        pub_date = meta_match.group(2).strip()
                
                # Inject the clean custom title metadata header rows right inside the continuous text stream canvas
                article_header_block = f"""
                <div class="article-header-block" style="margin-top: 35px; margin-bottom: 20px; border-bottom: 2px solid #111; padding-bottom: 10px; page-break-inside: avoid;">
                    <div class="article-main-title" style="font-size: 16pt !important; font-weight: bold !important; color: #000 !important; text-align: left !important;">Article Title: {meta['title']}</div>
                    <div class="meta-row" style="font-size: 10.5pt; color: #222; margin: 3px 0; text-align: left !important;"><span style="font-weight: bold;">Author:</span> {author_name}</div>
                    <div class="meta-row" style="font-size: 10.5pt; color: #222; margin: 3px 0; text-align: left !important;"><span style="font-weight: bold;">Date:</span> {pub_date}</div>
                </div>
                """
                
                # Parse with BeautifulSoup to strip out duplicated header nodes or residual web elements safely
                soup = BeautifulSoup(raw_html, 'html.parser')
                for h1_tag in soup.find_all('h1'):
                    h1_tag.decompose()
                for bad_meta in soup.find_all(class_=re.compile(r'meta|author|date|sharing|crumbs', re.I)):
                    bad_meta.decompose()
                    
                clean_body_segment = str(soup)
                
                # Append the clean header block and body segment continuously
                master_html_payload += f"\n{article_header_block}\n{clean_body_segment}\n"
                valid_article_count += 1

            if valid_article_count == 0:
                logger.error("❌ No individual article HTML files found to compile.")
                return 0

            # Construct the complete master HTML layout string context
            full_wrapped_html = f"""
            <!DOCTYPE html>
            <html lang="gu">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Gujarati', sans-serif; margin: 25px; background: white; color: #111; line-height: 1.6; font-size: 11pt; width: 100%; }}
                    p {{ margin: 12px 0 !important; text-align: left !important; word-wrap: break-word !important; width: 100% !important; display: block !important; }}
                    h2, h3 {{ margin: 18px 0 8px 0 !important; text-align: left !important; width: 100% !important; }}
                    img, svg, video, figure, .article-footer, .metadata_footer {{ display: none !important; height: 0 !important; opacity: 0 !important; }}
                </style>
            </head>
            <body>
                {master_html_payload}
            </body>
            </html>
            """
            
            # 1. Render and generate the single infinite-scroll text body document
            temp_body_pdf = os.path.join(os.path.dirname(output_path), "temp_body.pdf")
            generator.convert_sync(full_wrapped_html, temp_body_pdf, "https://opindia.com")
            
            # 2. Render the single cover page document cleanly
            cover_pdf_path = self.create_cover_page(category_key, month_str, valid_article_count)
            
            # 3. Stitch them together cleanly into ONE SINGLE PDF
            pdf_writer = PdfWriter()
            
            if cover_pdf_path and os.path.exists(cover_pdf_path):
                cover_reader = PdfReader(cover_path := cover_pdf_path)
                for page in cover_reader.pages:
                    pdf_writer.add_page(page)
                    
            if os.path.exists(temp_body_pdf):
                body_reader = PdfReader(temp_body_pdf)
                for page in body_reader.pages:
                    pdf_writer.add_page(page)
            
            # Save the final consolidated archive document
            with open(output_path, 'wb') as f:
                pdf_writer.write(f)
                
            # Clean up temporary layout sheets
            for temp_sheet in [cover_pdf_path, temp_body_pdf]:
                if temp_sheet and os.path.exists(temp_sheet):
                    try: os.remove(temp_sheet)
                    except Exception: pass
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✓ Created Unified Infinite-Scroll PDF: {output_path} ({file_size_mb:.2f} MB)")
            
            self.metadata.append({
                'category': category_name_english,
                'month': month_str,
                'article_count': valid_article_count,
                'file_size_mb': f"{file_size_mb:.2f}",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return valid_article_count
            
        except Exception as e:
            logger.error(f"Error executing infinite scroll compiling loop for {category_key}: {e}")
            return 0

    def merge_all_categories(self):
        """Orchestrate merge process across all active categories"""
        logger.info("Starting monthly PDF merge...")
        total_merged = 0
        
        for cat_key in CATEGORIES.keys():
            total_merged += self.merge_by_month(cat_key)
            
        logger.info(f"✓ Total articles merged: {total_merged}")
        
        if self.metadata:        
            os.makedirs(METADATA_DIR, exist_ok=True)
            metadata_file = os.path.join(METADATA_DIR, 'archive_metadata.csv')
            try:
                with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['category', 'month', 'article_count', 'file_size_mb', 'timestamp']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.metadata)
                logger.info(f"✓ Metadata saved: {metadata_file}")
            except Exception as e:
                logger.error(f"Failed to save metadata log file: {e}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    merger = PDFMergerMonthly()
    merger.merge_all_categories()


if __name__ == '__main__':
    main()
