"""
Group articles by publication month and merge into monthly PDFs per category continuously (Infinite Scroll)
"""
import logging
import os
import csv
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
        """Processes and merges individual article PDFs chronologically matching the site grid list"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            pdf_dir = os.path.join(base_dir, 'cache', 'individual_pdfs', category_key.lower())
            
            if not os.path.exists(pdf_dir):
                return 0
                
            pdf_files = list(Path(pdf_dir).glob('*.pdf'))
            if not pdf_files:
                return 0

            # Load the original ordered URL string array directly from your JSON progress file
            discovery_order = []
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
                        url_str = ""
                        if isinstance(item, dict):
                            url_str = item.get('url', '')
                        elif isinstance(item, str):
                            url_str = item
                        
                        if url_str:
                            url_hash = hashlib.md5(url_str.encode('utf-8')).hexdigest()[:8]
                            discovery_order.append(url_hash)
            except Exception as p_err:
                logger.warning(f"Could not calculate index arrays from progress tracking state: {p_err}")

            dated_pdfs = []
            for p_path in pdf_files:
                base_name = p_path.stem
                
                # Match priority position directly from the discovery tracking list sequence array
                sort_priority = discovery_order.index(base_name) if base_name in discovery_order else 999
                mtime_date = datetime.fromtimestamp(os.path.getmtime(p_path))
                
                dated_pdfs.append({
                    'date': mtime_date,
                    'priority': sort_priority,
                    'path': str(p_path),
                    'name': base_name
                })
            
            # Sort directly by live page stream positions (0, 1, 2...)
            dated_pdfs.sort(key=lambda x: x['priority'])
            
            logger.info(f"📋 Stream Grid Sequence Verification for {category_key}:")
            for idx, item in enumerate(dated_pdfs[:5], 1):
                logger.info(f"   [{idx}] {item['name']}.pdf ➔ Position: {item['priority']}")
            if len(dated_pdfs) > 5:
                logger.info(f"   ... [{len(dated_pdfs) - 5} additional documents sorted cleanly below] ...")
                
            sorted_pdf_paths = [item['path'] for item in dated_pdfs]
            
            # Setup final output directories
            category_info = CATEGORIES.get(category_key, {})
            category_name_english = category_info.get('name_english', category_key)
            month_str = "2026-06"
            output_filename = f'OpIndia_Gujarati_{category_name_english}_{month_str}.pdf'
            output_path = os.path.join(MONTHLY_PDF_DIR, category_name_english, output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Stitch files together page-by-page continuously into ONE SINGLE PDF
            pdf_writer = PdfWriter()
            
            cover_pdf_path = self.create_cover_page(category_key, month_str, len(sorted_pdf_paths))
            if cover_pdf_path and os.path.exists(cover_pdf_path):
                cover_reader = PdfReader(cover_pdf_path)
                for page in cover_reader.pages:
                    pdf_writer.add_page(page)
            
            for pdf_path in sorted_pdf_paths:
                if os.path.exists(pdf_path):
                    try:
                        reader = PdfReader(pdf_path)
                        for page in reader.pages:
                            pdf_writer.add_page(page)
                    except Exception as e:
                        logger.warning(f"Could not add {pdf_path}: {e}")
            
            with open(output_path, 'wb') as f:
                pdf_writer.write(f)
                
            if cover_pdf_path and os.path.exists(cover_pdf_path):
                try: os.remove(cover_pdf_path)
                except Exception: pass
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✓ Merged Continuous PDF: {output_path} ({file_size_mb:.2f} MB)")
            
            self.metadata.append({
                'category': category_name_english,
                'month': month_str,
                'article_count': len(sorted_pdf_paths),
                'file_size_mb': f"{file_size_mb:.2f}",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return len(sorted_pdf_paths)
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
                    fieldnames = ['category', 'month', 'article_count', 'file_size_mb', 'timestamp']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.metadata)
                logger.info(f"✓ Metadata saved: {metadata_file}")
            except Exception as e:
                logger.error(f"Failed to save metadata log file: {e}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    merger = PDFMergerMonthly()
    merger.merge_all_categories()

if __name__ == '__main__':
    main()
