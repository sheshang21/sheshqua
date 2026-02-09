QUARTERLY RESULTS SCREENER - SETUP GUIDE
=========================================

INSTALLATION:
1. Install dependencies:
   pip install -r requirements.txt

2. Run the app:
   streamlit run app.py

AUTHENTICATION:
🔐 NEW: Login Required!
- Screener.in now requires authentication
- First time: App will open a browser window for you to login
- Your session is saved in 'screener_cookies.pkl'
- Subsequent runs will use saved session (no re-login needed)
- Session expires after some time - just re-login when prompted
- Browser won't reload during login check anymore!

FEATURES:
- Scrapes all 1,986 companies from Screener.in
- Smart cookie-based authentication (login once, use many times)
- Headless scraping after initial login
- ⚡ NEW: Parallel workers (1-5 workers) for faster scraping
- ⚙️ NEW: Configurable delay (1-10 seconds) between page requests
- Intelligent page distribution (no overlaps or skips)
- Filters: Company name, Price, Market Cap, YOY metrics
- Sortable columns (click headers)
- CSV download

PERFORMANCE:
- 1 worker, 5s delay: ~7 minutes (safe, recommended)
- 2 workers, 3s delay: ~2 minutes (balanced)
- 3 workers, 2s delay: ~1.5 minutes (fast)
- 5 workers, 1s delay: ~1 minute (fastest, may hit rate limits)

DATA COLUMNS (20 total):
- Company, Price, Market Cap, PE
- Sales (Dec25, Sep25, Dec24, YOY%)
- EBIDT (Dec25, Sep25, Dec24, YOY%)
- Net Profit (Dec25, Sep25, Dec24, YOY%)
- EPS (Dec25, Sep25, Dec24, YOY%)

USAGE:
1. Run 'streamlit run app.py'
2. First time: Click "Login to Screener.in" and login in browser window
3. Select pages to scrape (All 1-80 or Custom)
4. Configure workers (1-5) and delay (1-10s)
5. Click "Fetch Quarterly Results" button
6. Wait for scraping to complete
7. Use filters to narrow results
8. Click column headers to sort
9. Download filtered data as CSV

NOTES:
- Data stored in session (resets on reload)
- Cookies saved in 'screener_cookies.pkl' (persistent across runs)
- Parallel workers distribute pages evenly (no overlap/skip)
- Error handling: 10s retry on failures
- Login session typically lasts for days/weeks
- Recommended: 2-3 workers with 3-5s delay for optimal speed/safety balance
