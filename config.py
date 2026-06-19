"""
Configuration for OpIndia Gujarati News Archive PDF Generator
"""
import os
from datetime import datetime

# ==== PROJECT PATHS ====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
FONTS_DIR = os.path.join(BASE_DIR, 'fonts')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
for dir_path in [CACHE_DIR, OUTPUT_DIR, FONTS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

HTML_CACHE_DIR = os.path.join(CACHE_DIR, 'html_cache')
PDF_CACHE_DIR = os.path.join(CACHE_DIR, 'individual_pdfs')
MONTHLY_PDF_DIR = os.path.join(OUTPUT_DIR, 'monthly_pdfs')
METADATA_DIR = os.path.join(OUTPUT_DIR, 'metadata')

for dir_path in [HTML_CACHE_DIR, PDF_CACHE_DIR, MONTHLY_PDF_DIR, METADATA_DIR]:
    os.makedirs(dir_path, exist_ok=True)

PROGRESS_FILE = os.path.join(CACHE_DIR, 'progress.json')

# ==== WEBSITE CONFIG ====
BASE_URL = 'https://gujarati.opindia.com'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
REQUEST_TIMEOUT = 15

# ==== SCRAPING CONFIG ====
RATE_LIMIT_DELAY = 2  # seconds between requests
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5

# ==== CATEGORIES ====
CATEGORIES = {
    'politics': {
        'name_gujarati': 'રાજકારણ',
        'name_english': 'Politics',
        'url': '/category/politics/'
    },
    'world': {
        'name_gujarati': 'દુનિયા',
        'name_english': 'World',
        'url': '/category/world/'
    },
    'crime': {
        'name_gujarati': 'ક્રાઈમ',
        'name_english': 'Crime',
        'url': '/category/crime/'
    },
    'reports': {
        'name_gujarati': 'ન્યૂઝ રિપોર્ટ',
        'name_english': 'Reports',
        'url': '/category/reports/'
    },
    'gujarat': {
        'name_gujarati': 'ગુજરાત',
        'name_english': 'Gujarat',
        'url': '/category/gujarat/'
    },
    'explainer': {
        'name_gujarati': 'એક્સપ્લેઇનર',
        'name_english': 'Explainer',
        'url': '/category/explainer/'
    },
    'india': {
        'name_gujarati': 'દેશ',
        'name_english': 'India',
        'url': '/category/india/'
    },
    'factcheck': {
        'name_gujarati': 'ફેક્ટ-ચેક',
        'name_english': 'FactCheck',
        'url': '/category/fact-check/'
    },
    'media': {
        'name_gujarati': 'મિડિયા',
        'name_english': 'Media',
        'url': '/category/media/'
    },
    'religion': {
        'name_gujarati': 'ધર્મ/સંસ્કૃતિ',
        'name_english': 'Religion',
        'url': '/category/misc/religion-and-culture/'
    },
    'entertainment': {
        'name_gujarati': 'મનોરંજન',
        'name_english': 'Entertainment',
        'url': '/category/misc/entertainment/'
    },
    'sports': {
        'name_gujarati': 'સ્પોર્ટ્સ',
        'name_english': 'Sports',
        'url': '/category/misc/sports/'
    },
    'satire': {
        'name_gujarati': 'કટાક્ષ',
        'name_english': 'Satire',
        'url': '/category/misc/satire/'
    },
    'misc': {
        'name_gujarati': 'વગેરે',
        'name_english': 'Miscellaneous',
        'url': '/category/misc/'
    }
}

# ==== FONTS ====
FONT_PATH = os.path.join(FONTS_DIR, 'NotoSansGujarati-Regular.ttf')
FONT_BOLD_PATH = os.path.join(FONTS_DIR, 'NotoSansGujarati-Bold.ttf')

# ==== LOGGING ====
LOG_FILE = os.path.join(LOGS_DIR, f'archive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# ==== PDF CONFIG ====
PDF_TITLE = 'OpIndia Gujarati News Archive'
PDF_AUTHOR = 'OpIndia'
PDF_CREATOR = 'OpIndia Archive Generator'
