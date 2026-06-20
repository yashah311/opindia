# OpIndia Gujarati News Archive Generator

A production-ready, fire-and-forget web scraper that automatically archives all articles from **gujarati.opindia.com** across 14 news categories into organized monthly PDF files.

## Features

✅ **All 14 Categories** - Politics, World, Crime, Reports, Gujarat, Explainer, India, FactCheck, Media, Religion, Entertainment, Sports, Satire, Miscellaneous  
✅ **~17,000-22,000 Articles** - Full historical archive  
✅ **Monthly PDFs** - Organized by category and month (e.g., `OpIndia_Gujarati_Politics_2026-06.pdf`)  
✅ **Ad-Free** - Removes all ads, tracking, scripts  
✅ **Gujarati Font Support** - Proper rendering of Gujarati text  
✅ **Resumable** - Checkpoint system for interrupted runs  
✅ **Production-Ready** - Error handling, retries, logging  
✅ **Demo Mode First** - Generate sample PDF before bulk archive  

## Quick Start

### Prerequisites

- **Python 3.9+** installed
- **~1GB disk space** for cache and output files
- **Internet connection** (for scraping)

### Installation (5 minutes)

```bash
# 1. Navigate to project folder
cd "Desktop\project\opindia"

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium
```

### Generate Sample PDF First (15 minutes)

```bash
python scraper.py --demo
```

This generates ONE sample PDF from Politics category (~10-20 articles) for approval.

**Output**: `output/monthly_pdfs/Politics/OpIndia_Gujarati_Politics_2026-06.pdf`

**Check the sample PDF for:**
- Gujarati text renders correctly (not boxes/garbled)
- Cover page shows category name and month
- Articles are readable and properly formatted
- No ads or tracking content
- File size ~2-5 MB for 10-20 articles

### After Approval: Generate Full Archive

```bash
# Full archive (all 14 categories, ~4-6 hours)
python scraper.py --all

# Or test with smaller sample first
python scraper.py --all --max-pages 5    # 5 pages per category (~30 min)
```

## Usage

### Demo Mode (Recommended First Run)
```bash
python scraper.py --demo
```
Generates 1 sample PDF for approval before bulk generation.

### Full Archive (All Categories)
```bash
python scraper.py --all
```

### Single Category
```bash
python scraper.py --category politics
python scraper.py --category world
python scraper.py --category gujarat
```

### Resume Previous Run
```bash
python scraper.py --resume
```

### Test Run (Small Sample)
```bash
python scraper.py --all --max-pages 2
```

### Skip Phases
```bash
python scraper.py --all --skip-download   # Skip HTML download, use cache
python scraper.py --all --skip-pdf        # Skip PDF generation
```
## Core Operational Commands

### 1. Pre-Flight Demo Mode
**Always run this first.** It performs URL discovery, cleans up structural formatting, and outputs a validation document for the **Gujarat** category to verify system fonts and page layouts.
```bash
python scraper.py --demo
```
* **Output Location**: `output/monthly_pdfs/Gujarat/OpIndia_Gujarati_Gujarat_2026-06.pdf`

### 2. Full Archive Bulk Pipeline
Launches the background workers across all 14 configured database segments sequentially (takes ~4–6 hours first run).
```bash
python scraper.py --all
```

### 3. Targeted Category & Page Extraction Controls
Use the `--category` routing string paired with the `--max-pages` integer parameter to execute precise extraction tasks:

```bash
# Test a category layout with a 2-page pagination deep-check
python scraper.py --category politics --max-pages 2

# Limit data parsing down to a single page index window
python scraper.py --category politics --max-pages 1
python scraper.py --category crime --max-pages 1

# Extract nested category items safely using case-insensitive dictionary routing keys
python scraper.py --category religion --max-pages 1
python scraper.py --category entertainment --max-pages 1
python scraper.py --category sports --max-pages 1
python scraper.py --category satire --max-pages 1
```

---

## Output Quality Verification Checklist

Open newly generated compilation files and check for the following properties:
1. **Font Integrity**: Text reads organically in standard Gujarati characters (no blank boxes, squares, or overlapping lettering).
2. **Heading Separation**: Elements like `<h1>` and `<h2>` use `break-inside: avoid;` print directives so titles never truncate at footer lines.
3. **No Character Bloat**: Banners and escaped string tokens are neutralized; no unexpected repeating text strings (`& & & &`) display on section breaks.

---

## Workspace Directory Tree

```text
opindia/
├── cache/
│   ├── html_cache/         <- Structured offline text backups
│   ├── individual_pdfs/    <- Intermediary single-article compiled documents
│   └── progress.json       <- Tracking checkpoints and state map indices
├── fonts/
│   └── NotoSansGujarati-Regular.ttf <- Localized script validation asset
├── logs/
│   └── archive_YYYYMMDD_HHMMSS.log  <- Execution trace logs
└── output/
    ├── metadata/           <- Compilation runtime statistics CSV files
    └── monthly_pdfs/       <- Categorized final products
        ├── Crime/
        ├── Gujarat/
        ├── Politics/
        └── Religion/       <- Nested sub-category URLs map cleanly here
```

---

## Configuration Tuning

To change engine performance, adjust property definitions inside **`config.py`**:

```python
RATE_LIMIT_DELAY = 2   # Request cooldown padding between HTTP actions (be polite!)
MAX_RETRIES = 3        # Connection attempt limits before throwing errors
REQUEST_TIMEOUT = 15   # Network socket wait threshold boundaries (seconds)
```

---

## Real-Time Process Monitoring

To track background operations across your Windows PowerShell environment, run the following live tracking tail string block:

```powershell
Get-Content -Path logs/archive_*.log -Wait -Tail 30
```

---

## Execution Timeline

| Phase | Task | Est. Time |
|-------|------|-----------|
| Demo | Setup + sample PDF | 15 min |
| Full Archive: | | |
| 1 | Setup (fonts, dirs) | 5 min |
| 2 | URL Discovery | 40-50 min |
| 3 | HTML Download & Clean | 2-3 hours |
| 4 | PDF Generation | 1-2 hours |
| 5 | Monthly Merge | 30 min |
| **Total (Full)** | | **~4-6 hours** |

**First-time run takes longest due to download and processing. Resumable from checkpoints.**

## What Gets Archived

- **All article URLs** from each category
- **Article HTML** (cleaned, ads removed)
- **Individual PDFs** for each article
- **Monthly consolidated PDFs** grouped by category
- **Metadata CSV** with archive statistics

## Configuration

Edit `config.py` to customize:

```python
RATE_LIMIT_DELAY = 2              # Seconds between requests (be respectful!)
MAX_RETRIES = 3                   # Failed request retries
REQUEST_TIMEOUT = 15              # HTTP request timeout
```

## Logging

All operations logged to `logs/archive_YYYYMMDD_HHMMSS.log`

View live logs while running:
```bash
# PowerShell
Get-Content -Path logs/archive_*.log -Wait -Tail 20

# Or check after completion
cat logs/archive_*.log
```

## Key Files

| File | Purpose |
|------|---------|
| `config.py` | All settings, categories, paths |
| `scraper.py` | Main entry point with CLI |
| `category_scraper.py` | Discover URLs from categories |
| `article_scraper.py` | Download HTML articles |
| `html_cleaner.py` | Clean content (remove ads) |
| `pdf_generator.py` | Convert HTML to PDF |
| `pdf_merger_monthly.py` | Merge into monthly PDFs |
| `requirements.txt` | Dependencies |

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
playwright install chromium
```

### Gujarati text not rendering in PDFs
Ensure Noto Sans Gujarati font is downloaded:
- Script will auto-download on first run
- Or manually place in `fonts/` folder

### Out of disk space
Delete cache folder after successful run:
```bash
rmdir /s cache\
```
**Note**: Final PDFs remain in `output/monthly_pdfs/`

### Scraper too slow
Reduce rate limiting in `config.py`:
```python
RATE_LIMIT_DELAY = 1  # From 2 (faster, less respectful)
```

### Network timeouts
Increase timeout in `config.py`:
```python
REQUEST_TIMEOUT = 30  # From 15
```

### Memory issues
Run with `--skip-pdf` to skip PDF generation phase, then process separately.

## Tips for Running

1. **Run overnight** - Full archive takes 4-6 hours
2. **Start with `--demo`** - Test sample before full run
3. **Test with `--max-pages 2` first** - Quick validation
4. **Check logs** - Monitor progress in `logs/` folder
5. **Keep `cache/`** - Speeds up reruns; delete only if space needed
6. **Backup output** - Copy final PDFs to external drive after completion

## For Developers

To extend or modify:

- Add categories in `config.py` under `CATEGORIES` dict
- Customize PDF styling in `pdf_generator.py` (CSS section)
- Modify HTML cleaning rules in `html_cleaner.py`
- Add post-processing logic in `pdf_merger_monthly.py`

## Legal / Usage

- **Personal research & archival** use case
- For news preservation and offline access
- Respects `robots.txt` and rate limiting (2 sec/request)
- Archive attribution included in PDF cover pages
- Fair use under Indian copyright law for archival purposes

## Performance Notes

- **Network-bound**: Most time spent downloading articles
- **CPU-bound**: PDF generation is resource-intensive
- **Disk-bound**: Final PDFs ~200-300MB total
- **Can be interrupted and resumed** from checkpoints

## Support

If issues occur:
1. Check `logs/` folder for error messages
2. Verify internet connection is stable
3. Ensure Python 3.9+ and all dependencies installed
4. Try `python scraper.py --resume` to continue from checkpoint
5. Run with `--max-pages 2` for testing before full run

## FAQ

**Q: How long does full archive take?**  
A: ~4-6 hours first time. Resumable from checkpoints if interrupted.

**Q: How much disk space needed?**  
A: ~600MB-1GB (cache + output). Can delete cache after completion.

**Q: Can I run multiple categories in parallel?**  
A: Not currently. Sequential design respects rate limits.

**Q: Will it re-download if I run again?**  
A: No. Cached articles are skipped. Use `--resume` to continue from last checkpoint.

**Q: Can I modify categories?**  
A: Yes. Edit `CATEGORIES` dict in `config.py`.

**Q: Is this legal?**  
A: Personal archival is fair use. Respects robots.txt and rate limiting.

---

**Created**: 2026-06-19  
**Archive Coverage**: All gujarati.opindia.com categories (14 total)  
**Estimated Total Articles**: 17,000-22,000  
**License**: For personal research use
