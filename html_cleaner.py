"""
Clean HTML: extract ONLY the pure text of the article and fully decouple from HTML UI
"""
import logging
import os
import re
from trafilatura import extract
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HTMLCleaner:
    @staticmethod
    def clean_html(html_content, url):
        """
        Decouple article text from all HTML structures and return pure text paragraphs
        """
        try:
            # પ્રગતિ ટ્રેકિંગ માટે ઓરિજિનલ મેટાડેટા લાઇન સાચવો
            meta_line = ""
            meta_match = re.search(r'(<p class="metadata_footer">Source:.*?</p>)', html_content)
            if meta_match:
                meta_line = meta_match.group(1)

            # ટ્રાફિલેતુરાનો ઉપયોગ કરીને મુખ્ય કન્ટેન્ટ એક્સટ્રેક્ટ કરો
            extracted = extract(html_content, output_format='html', include_comments=False)
            
            if not extracted:
                logger.warning(f"Could not extract content from {url}")
                return None
            
            # ટ્રાફિલેતુરાના અનિચ્છનીય એન્ટિટીઝ સાફ કરો
            extracted = re.sub(r'&\s*&\s*&\s*&\s*&\s*&', '', extracted)
            extracted = re.sub(r'&\s*&', '', extracted)
            extracted = re.sub(r'&amp;|\bamp\b|&quot;', '', extracted)
            
            soup = BeautifulSoup(extracted, 'html.parser')
            
            # === મોટો ફેરફાર: આખી વેબસાઇટનું HTML માળખું તોડી નાખો અને માત્ર ટેક્સ્ટ લો ===
            # હેડર મેનૂ અને જાહેરાતના ટેક્સ્ટ ફિલ્ટર આઉટ કરો
            lines = []
            for paragraph in soup.find_all(['p', 'h1', 'h2', 'h3', 'span', 'div']):
                text_line = paragraph.get_text(strip=True)
                
                # ફિલ્ટર: નકામી વેબ લિંક્સ, બેનર્સ અને એડવર્ટાઇઝમેન્ટ લાઇન સ્કીપ કરો
                if not text_line:
                    continue
                if any(word in text_line for word in ['હોમપેજ', 'દેશ', 'રાજકારણ', 'એક્સપ્લેઇનર', 'ધર્મ', 'સંસ્કૃતિ', 'વિશેષ', 'સંપાદકની પસંદ', 'મંતવ્ય', 'ગુજરાત', 'દુનિયા', 'Advertisement', 'जाहरात', 'જાહેરાત', 'Photo:']):
                    continue
                
                # ક્લીન થયેલી લાઇન જો પહેલેથી એડ ન થઈ હોય તો જ લો
                if text_line not in lines:
                    # જો તે હેડિંગ હોય તો તેને HTML ટૅગ આપો, બાકી નોર્મલ પેરેગ્રાફ સેટ કરો
                    if paragraph.name in ['h1', 'h2', 'h3']:
                        lines.append(f"<h2>{text_line}</h2>")
                    else:
                        lines.append(f"<p>{text_line}</p>")
            
            # શુદ્ધ કન્ટેન્ટને ભેગું કરો
            pure_text_body = "\n".join(lines)
            
            # મેટાડેટા ફૂટર લાઇન છેલ્લે જોડી દો
            if meta_line:
                pure_text_body += f"\n{meta_line}"
                
            return pure_text_body
            
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    from config import HTML_CACHE_DIR
    import glob
    
    cleaner = HTMLCleaner()
    html_files = glob.glob(os.path.join(HTML_CACHE_DIR, '**', '*.html'), recursive=True)
    logger.info(f"Cleaning {len(html_files)} HTML files...")
    
    for i, html_file in enumerate(html_files, 1):
        html_content = cleaner.read_cached_html(html_file)
        if html_content:
            cleaned = cleaner.clean_html(html_content, html_file)
            if cleaned:
                cleaner.save_cleaned_html(cleaned, html_file)

if __name__ == '__main__':
    main()
