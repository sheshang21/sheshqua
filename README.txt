QUARTERLY RESULTS SCREENER - SETUP GUIDE
=========================================

INSTALLATION:
1. Install dependencies:
   pip install -r requirements.txt

2. Run the app:
   streamlit run app.py

FEATURES:
- Scrapes all 1,986 companies from Screener.in
- 2-second delay between requests (strict rate limiting)
- Takes ~3 minutes to fetch all 80 pages
- Filters: Company name, Price, Market Cap, YOY metrics
- Sortable columns (click headers)
- CSV download

DATA COLUMNS (20 total):
- Company, Price, Market Cap, PE
- Sales (Dec25, Sep25, Dec24, YOY%)
- EBIDT (Dec25, Sep25, Dec24, YOY%)
- Net Profit (Dec25, Sep25, Dec24, YOY%)
- EPS (Dec25, Sep25, Dec24, YOY%)

USAGE:
1. Click "Fetch Quarterly Results" button
2. Wait for scraping to complete (~3 mins)
3. Use filters to narrow results
4. Click column headers to sort
5. Download filtered data as CSV

NOTES:
- Data stored in session (resets on reload)
- Rate limited: 2s between pages
- Error handling: 5s retry on failures
