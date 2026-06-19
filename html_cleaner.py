"""
Clean HTML: extract article content and remove ads/tracking/navigation elements
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
        Extract core article text and forcefully decompose navigation grids
        """
        try:
            # પ્રગતિ ટ્રેકિંગ માટે ઓરિજિનલ મેટાડેટા લાઇન સાચવો
            meta_line = ""
            meta_match = re.search(r'(<p class="metadata_footer">Source:.*?</p>)', html_content)
            if meta_match:
                meta_line = meta_match.group(1)

            # ટ્રાફિલેતુરાનો ઉપયોગ કરીને મુખ્ય ટેક્સ્ટ એક્સટ્રેક્ટ કરો
            extracted = extract(html_content, output_format='html', include_comments=False)
            
            if not extracted:
                logger.warning(f"Could not extract content from {url}")
                return None
            
            # ટ્રાફિલેતુરા દ્વારા છોડવામાં આવેલા અનિચ્છનીય કેરેક્ટર્સ સાફ કરો
            extracted = re.sub(r'&\s*&\s*&\s*&\s*&\s*&', '', extracted)
            extracted = re.sub(r'&\s*&', '', extracted)
            extracted = re.sub(r'&amp;|\bamp\b|&quot;', '', extracted)
            
            soup = BeautifulSoup(extracted, 'html.parser')
            
            # === સર્જિકલ ક્લીનઅપ: વેબસાઇટના મેનૂ, બ્રેડક્રમ્બ્સ અને સોશિયલ ટેગ્સ સંપૂર્ણ દૂર કરો ===
            # આનાથી 'એક્સપ્લેઇનર', 'દેશ', 'રાજકારણ' અને હોમપેજની લિંક્સ કાયમ માટે હટી જશે
            for bad_tag in ['img', 'figure', 'svg', 'header', 'footer', 'button', 'iframe', 'nav']:
                for elem in soup.find_all(bad_tag):
                    elem.decompose()
            
            # ટેક્સ્ટ લિંક્સ અને કેટેગરી પિલ્સને ટાર્ગેટ કરો
            for link in soup.find_all('a'):
                link_text = link.get_text(strip=True)
                # જો લિંકમાં હોમપેજ કે કેટેગરીના શબ્દો હોય તો તેને દૂર કરો
                if any(word in link_text for word in ['હોમપેજ', 'દેશ', 'રાજકારણ', 'એક્સપ્લેઇનર', 'ધર્મ', 'સંસ્કૃતિ', 'વિશેષ', 'સંપાદકની પસંદ']):
                    link.decompose()
            
            # તમામ અનિચ્છનીય સ્ક્રિપ્ટો અને ક્લાસ ડીકમ્પોઝ કરો
            for bad_pattern in ['logo', 'brand', 'header', 'nav', 'menu', 'breadcrumb', 'pills', 'tags', 'share', 'social', 'button']:
                for element in soup.find_all(class_=re.compile(bad_pattern, re.I)):
                    element.decompose()
                for element in soup.find_all(id_=re.compile(bad_pattern, re.I)):
                    element.decompose()
            
            # મૂળભૂત સફાઈ
            for tag in soup.find_all(['script', 'style', 'meta', 'link', 'noscript']):
                tag.decompose()
            
            cleaned_body = str(soup)
            
            # મેટાડેટા ફૂટર લાઇનને છેલ્લે ફરીથી ઉમેરો
            if meta_line:
                cleaned_body += f"\n{meta_line}"
                
            return cleaned_body
            
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
