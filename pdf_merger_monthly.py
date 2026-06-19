"""
Group articles by month and merge into monthly PDFs per category
"""
import logging
import os
import json
from datetime import datetime
from pathlib import Path
import csv
from PyPDF2 import PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from config import PDF_CACHE_DIR, MONTHLY_PDF_DIR, METADATA_DIR, CATEGORIES

logger = logging.getLogger(__name__)

class PDFMergerMonthly:
    def __init__(self):
        self.metadata = []
    
    def create_cover_page(self, category_key, month_str, article_count):
        """Create cover page for monthly PDF"""
        try:
            category_info = CATEGORIES.get(category_key, {})
            category_name_gujarati = category_info.get('name_gujarati', category_key)
            category_name_english = category_info.get('name_english', category_key)
            
            output_dir = os.path.join(MONTHLY_PDF_DIR, category_name_english)
            os.makedirs(output_dir, exist_ok=True)
            
            cover_path = os.path.join(output_dir, f'cover_{month_str}.pdf')
            
            doc = SimpleDocTemplate(
                cover_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            styles = getSampleStyleSheet()
            custom_style = ParagraphStyle(
                'Custom',
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
                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10)
            ))
            story.append(Paragraph(
                "For personal research and archival purposes only.",
                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor='#666666')
            ))
            
            doc.build(story)
            logger.info(f"✓ Created cover page: {cover_path}")
            return cover_path
            
        except Exception as e:
            logger.error(f"Error creating cover page: {e}")
            return None
    
    def merge_pdfs_for_month(self, pdf_paths, output_path, category_key, month_str, article_count):
        """Merge multiple PDFs into one"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create cover page
            cover_path = self.create_cover_page(category_key, month_str, article_count)
            
            pdf_writer = PdfWriter()
            
            # Add cover page first
            if cover_path and os.path.exists(cover_path):
                with open(cover_path, 'rb') as f:
                    cover_pdf = PdfWriter()
                    cover_pdf.read(f)
                    for page_num in range(len(cover_pdf.pages)):
                        pdf_writer.add_page(cover_pdf.pages[page_num])
            
            # Add article PDFs
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    try:
                        with open(pdf_path, 'rb') as f:
                            reader = PdfWriter()
                            reader.read(f)
                            for page_num in range(len(reader.pages)):
                                pdf_writer.add_page(reader.pages[page_num])
                    except Exception as e:
                        logger.warning(f"Could not add {pdf_path}: {e}")
            
            # Write merged PDF
            with open(output_path, 'wb') as f:
                pdf_writer.write(f)
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✓ Merged PDF: {output_path} ({file_size_mb:.2f} MB)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            return None
    
    def merge_by_month(self, category_key):
        """Group articles by month and create monthly PDFs"""
        try:
            category_dir = os.path.join(PDF_CACHE_DIR, category_key)
            if not os.path.exists(category_dir):
                logger.warning(f"No PDF directory for {category_key}")
                return 0
            
            # This is simplified - in full implementation, would parse article dates
            # For now, create single monthly PDF with all available articles
            pdf_files = list(Path(category_dir).glob('*.pdf'))
            
            if not pdf_files:
                logger.info(f"No PDFs found for {category_key}")
                return 0
            
            category_info = CATEGORIES.get(category_key, {})
            category_name_english = category_info.get('name_english', category_key)
            
            month_str = datetime.now().strftime('%Y-%m')
            output_filename = f'OpIndia_Gujarati_{category_name_english}_{month_str}.pdf'
            output_path = os.path.join(MONTHLY_PDF_DIR, category_name_english, output_filename)
            
            pdf_paths = [str(f) for f in pdf_files]
            self.merge_pdfs_for_month(pdf_paths, output_path, category_key, month_str, len(pdf_files))
            
            # Record metadata
            self.metadata.append({
                'category': category_name_english,
                'month': month_str,
                'article_count': len(pdf_files),
                'file_path': output_path,
                'file_size_mb': os.path.getsize(output_path) / (1024 * 1024) if os.path.exists(output_path) else 0,
                'created_date': datetime.now().isoformat()
            })
            
            return len(pdf_files)
            
        except Exception as e:
            logger.error(f"Error merging {category_key}: {e}")
            return 0
    
    def merge_all_categories(self):
        """Merge all categories"""
        from config import CATEGORIES
        
        logger.info("Starting monthly PDF merge...")
        total_articles = 0
        
        for category_key in CATEGORIES.keys():
            count = self.merge_by_month(category_key)
            total_articles += count
        
        # Save metadata
        metadata_file = os.path.join(METADATA_DIR, 'archive_metadata.csv')
        os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
        
        with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
            if self.metadata:
                writer = csv.DictWriter(f, fieldnames=self.metadata[0].keys())
                writer.writeheader()
                writer.writerows(self.metadata)
        
        logger.info(f"✓ Total articles merged: {total_articles}")
        logger.info(f"✓ Metadata saved: {metadata_file}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    merger = PDFMergerMonthly()
    merger.merge_all_categories()

if __name__ == '__main__':
    main()
