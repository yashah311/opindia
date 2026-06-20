"""
Group articles by publication month and merge into monthly PDFs per category continuously (Infinite Scroll)
"""
import logging
import os
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
from config import MONTHLY_PDF_DIR, CATEGORIES, PROGRESS_FILE

logger = logging.getLogger(__name__)

class PDFMergerMonthly:
    def __init__(self):
        self.metadata = []
    
    def create_cover_page(self, category_key, month_str, article_count):
        try:
            category_name_english = category_key.capitalize()
            for k, v in CATEGORIES.items():
                if k.lower() == category_key.lower():
                    category_name_english = v.get('name_english', k.capitalize())
                    break
                    
            output_dir = os.path.join(MONTHLY_PDF_DIR, category_name_english)
            os.makedirs(output_dir, exist_ok=True)
            cover_path = os.path.join(output_dir, f'cover_{month_str}.pdf')
            
            doc = SimpleDocTemplate(cover_path, pagesize=A4, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
            styles = getSampleStyleSheet()
            custom_style = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=18, textColor='#111111', spaceAfter=25, alignment=TA_CENTER)
            
            story = [
                Spacer(1, 2.5*inch),
                Paragraph("OpIndia Gujarati News Archive", custom_style),
                Spacer(1, 0.3*inch),
                Paragraph(f"Category: {category_name_english}", custom_style),
                Paragraph(f"Month: {month_str}", custom_style),
                Spacer(1, 0.3*inch),
                Paragraph(f"Total Articles: {article_count}", custom_style),
                Spacer(1, 0.5*inch),
                Paragraph(f"Archived on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ParagraphStyle('Footer1', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER))
            ]
            doc.build(story)
            return cover_path
        except Exception as e:
            logger.error(f"Error creating cover page: {e}")
            return None
    def merge_by_month(self, category_key):
        """Processes and merges individual article PDFs chronologically into dynamic folders"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            pdf_dir = os.path.join(base_dir, 'cache', 'individual_pdfs', category_key.lower())
            
            if not os.path.exists(pdf_dir):
                logger.warning(f"Target directory missing: {pdf_dir}")
                return 0
                
            pdf_files = list(Path(pdf_dir).glob('*.pdf'))
            if not pdf_files:
                logger.warning(f"No PDFs located in path: {pdf_dir}")
                return 0

            discovery_order = []
            if os.path.exists(PROGRESS_FILE):
                try:
                    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    
                    discovered_list = progress_data.get('discovered_urls', {}).get(category_key.lower(), [])
                    if not discovered_list and category_key.lower() in progress_data:
                        discovered_list = progress_data[category_key.lower()]
                        
                    if isinstance(discovered_list, dict):
                        discovered_list = list(discovered_list.keys())
                        
                    for item in discovered_list:
                        url_str = item.get('url', '') if isinstance(item, dict) else item
                        if url_str:
                            url_hash = hashlib.md5(url_str.encode('utf-8')).hexdigest()[:8]
                            discovery_order.append(url_hash)
                except Exception as p_err:
                    logger.warning(f"Error reading progress indices: {p_err}")

            dated_pdfs = []
            for p_path in pdf_files:
                base_name = p_path.stem
                if ".html" in base_name:
                    base_name = base_name.replace(".html", "")
                base_name = base_name.replace("('", "").replace("',", "").strip()
                
                sort_priority = discovery_order.index(base_name) if base_name in discovery_order else 999
                mtime_date = datetime.fromtimestamp(os.path.getmtime(p_path))
                
                dated_pdfs.append({
                    'date': mtime_date, 'priority': sort_priority, 'path': str(p_path), 'name': base_name
                })
            
            dated_pdfs.sort(key=lambda x: (x['priority'], x['date']))
            sorted_pdf_paths = [item['path'] for item in dated_pdfs]
            
            category_name_english = category_key.capitalize()
            for key, val in CATEGORIES.items():
                if key.lower() == category_key.lower():
                    category_name_english = val.get('name_english', key.capitalize())
                    break
                    
            month_str = datetime.now().strftime("%Y-%m")
            output_filename = f'OpIndia_Gujarati_{category_name_english}_{month_str}.pdf'
            output_path = os.path.join(MONTHLY_PDF_DIR, category_name_english, output_filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            pdf_writer = PdfWriter()
            cover_pdf_path = self.create_cover_page(category_key, month_str, len(sorted_pdf_paths))
            
            if cover_pdf_path and os.path.exists(cover_pdf_path):
                cover_reader = PdfReader(cover_pdf_path)
                for page in cover_reader.pages:
                    pdf_writer.add_page(page)
            
            merged_count = 0
            for pdf_path in sorted_pdf_paths:
                if os.path.exists(pdf_path):
                    try:
                        reader = PdfReader(pdf_path)
                        for page in reader.pages:
                            pdf_writer.add_page(page)
                        merged_count += 1
                    except Exception as e:
                        logger.warning(f"Could not add {pdf_path}: {e}")
            
            if merged_count == 0:
                logger.error("❌ No elements successfully compiled into the output writer.")
                return 0

            with open(output_path, 'wb') as f:
                pdf_writer.write(f)
                
            if cover_pdf_path and os.path.exists(cover_pdf_path):
                try: os.remove(cover_pdf_path)
                except Exception: pass
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✓ Merged Continuous PDF: {output_path} ({file_size_mb:.2f} MB)")
            return merged_count
        except Exception as e:
            logger.error(f"Critical error during monthly merge: {e}", exc_info=True)
            return 0
