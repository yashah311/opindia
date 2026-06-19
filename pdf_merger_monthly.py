"""
Group articles by publication month and merge into monthly PDFs per category chronologically
"""
import logging
import os
import csv
import re
from datetime import datetime
from pathlib import Path
from PyPDF2 import PdfWriter, PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from config import PDF_CACHE_DIR, MONTHLY_PDF_DIR, METADATA_DIR, CATEGORIES, HTML_CACHE_DIR

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
                rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72
            )
            
            styles = getSampleStyleSheet()
            custom_style = ParagraphStyle(
                'CoverTitle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=18,
                textColor='#333333',
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            story = []
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph("OpIndia Gujarati News Archive", custom_style))
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(f"Category: {category_name_english}", custom_style))
            story.append(Paragraph(f"Month: {month_str}", custom_style))
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(f"Total Articles: {article_count}", custom_style))
            story.append(Spacer(1, 1*inch))
            story.append(Paragraph(
                f"Archived on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ParagraphStyle('Footer1', parent=styles['Normal'], fontSize=10)
            ))
            story.append(Paragraph(
                "For personal research and archival purposes only.",
                ParagraphStyle('Footer2', parent=styles['Normal'], fontSize=9, textColor='#666666')
            ))
            
            doc.build(story)
            return cover_path
        except Exception as e:
            logger.error(f"Error creating cover page: {e}")
            return None
    
    def merge_pdfs_for_month(self, pdf_paths, output_path, category_key, month_str, article_count):
        """Merge multiple PDFs into one safely"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cover_path = self.create_cover_page(category_key, month_str, article_count)
            pdf_writer = PdfWriter()
            
            if cover_path and os.path.exists(cover_path):
                cover_reader = PdfReader(cover_path)
                for page in cover_reader.pages:
                    pdf_writer.add_page(page)
            
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    try:
                        reader = PdfReader(pdf_path)
                        for page in reader.pages:
                            pdf_writer.add_page(page)
                    except Exception as e:
                        logger.warning(f"Could not add {pdf_path}: {e}")
            
            with open(output_path, 'wb') as f:
                pdf_writer.write(f)
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✓ Merged Chronological PDF: {output_path} ({file_size_mb:.2f} MB)")
            
            if cover_path and os.path.exists(cover_path):
                try: os.remove(cover_path)
                except Exception: pass
                
            return output_path
        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            return None

    def extract_published_date_from_html(self, html_path):
        """Surgically extracts real publishing date string even with stylized typographic dividers"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                raw_html = f.read()
            
            # Clean elements out to eliminate clutter layers
            text = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL)
            text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            clean_text = ' '.join(text.split())
            
            # === CRITICAL RE-MAPPING: Capture both keyboard '|' and typographical '|' unicode variants ===
            date_match = re.search(r'([A-Z][a-z]+ \d{1,2}, \d{4})\s*[\s\u2502\u007c:-]\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', clean_text)
            
            if date_match:
                date_str = date_match.group(1).strip()
                time_str = date_match.group(2).strip().upper()
                return datetime.strptime(f"{date_str} {time_str}", "%B %d, %Y %I:%M %p")
                
            # Secondary fallback search if time segment string expression drops
            fallback_match = re.search(r'([A-Z][a-z]+ \d{1,2}, \d{4})', clean_text)
            if fallback_match:
                return datetime.strptime(fallback_match.group(1).strip(), "%B %d, %Y")
                
        except Exception as e:
            logger.debug(f"Regex processing exception: {e}")
        return None

    def merge_by_month(self, category_key):
        """Filters, sorts, and clusters files chronologically based on real internal data values"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            html_dir = os.path.join(HTML_CACHE_DIR, category_key.lower())
            pdf_dir = os.path.join(base_dir, 'cache', 'individual_pdfs', category_key.lower())
            
            if not os.path.exists(pdf_dir):
                return 0
                
            pdf_files = list(Path(pdf_dir).glob('*.pdf'))
            if not pdf_files:
                return 0
                
            dated_pdfs = []
            logger.info(f"🔍 Timeline Scanning: Processing historical values for {category_key}...")
            
            for p_path in pdf_files:
                base_name = p_path.stem
                matching_html = os.path.join(html_dir, f"{base_name}.html")
                
                pub_date = None
                if os.path.exists(matching_html):
                    pub_date = self.extract_published_date_from_html(matching_html)
                
                # Fallback to filesystem modified timestamp if HTML parsing skips
                if not pub_date:
                    pub_date = datetime.fromtimestamp(os.path.getmtime(p_path))
                
                # Target Layer Constraint: Isolate June 2026 articles exclusively
                if pub_date.year == 2026 and pub_date.month == 6:
                    dated_pdfs.append({
                        'date': pub_date,
                        'path': str(p_path),
                        'name': base_name
                    })
            
            if not dated_pdfs:
                logger.info(f"No valid June 2026 documents found for {category_key}")
                return 0
                
            # === CHRONOLOGICAL ORDERING FIX: Sort entries Descending (June 19 -> June 1) ===
            dated_pdfs.sort(key=lambda x: x['date'], reverse=True)
            
            # Print sorting trace log to console window for visual confirmation
            logger.info(f"📋 Chronological Order Map for {category_key}:")
            for idx, item in enumerate(dated_pdfs[:5], 1):
                logger.info(f"   [{idx}] {item['name']}.pdf ➔ {item['date'].strftime('%Y-%m-%d %I:%M %p')}")
            if len(dated_pdfs) > 5:
                logger.info(f"   ... [{len(dated_pdfs) - 5} additional documents sorted below] ...")
                
            sorted_pdf_paths = [item['path'] for item in dated_pdfs]
            # ===============================================================================
            
            category_info = CATEGORIES.get(category_key, {})
            category_name_english = category_info.get('name_english', category_key)
            
            month_str = "2026-06"
            output_filename = f'OpIndia_Gujarati_{category_name_english}_{month_str}.pdf'
            output_path = os.path.join(MONTHLY_PDF_DIR, category_name_english, output_filename)
            
            merged_pdf = self.merge_pdfs_for_month(
                pdf_paths=sorted_pdf_paths,
                output_path=output_path,
                category_key=category_key,
                month_str=month_str,
                article_count=len(sorted_pdf_paths)
            )
            
            if merged_pdf:
                self.metadata.append({
                    'category': category_name_english,
                    'month': month_str,
                    'article_count': len(sorted_pdf_paths),
                    'file_size_mb': f"{os.path.getsize(output_path)/(1024*1024):.2f}",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                return len(sorted_pdf_paths)
            return 0
        except Exception as e:
            logger.error(f"Error sorting/merging {category_key}: {e}")
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
                    writer = csv.DictWriter(f, fieldnames=self.metadata.keys())
                    writer.writeheader()
                    writer.writerows(self.metadata)
                logger.info(f"✓ Metadata saved: {metadata_file}")
            except Exception as e:
                logger.error(f"Failed to save metadata metrics log file: {e}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    merger = PDFMergerMonthly()
    merger.merge_all_categories()

if __name__ == '__main__':
    main()
