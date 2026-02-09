from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import pickle
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

COOKIES_FILE = 'screener_cookies.pkl'
progress_lock = Lock()

def parse_value(value_str):
    if not value_str or value_str.strip() == '' or value_str == 'None':
        return None
    try:
        cleaned = value_str.replace('₹', '').replace(',', '').strip()
        return float(cleaned)
    except:
        return None

def parse_yoy(yoy_str):
    if not yoy_str:
        return None
    match = re.search(r'([⇡⇣])\s*(\d+)%', yoy_str)
    if match:
        direction, value = match.groups()
        return float(value) if direction == '⇡' else -float(value)
    return None

def save_cookies(driver):
    """Save cookies to file"""
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(cookies, f)
    print(f"✅ Cookies saved to {COOKIES_FILE}")

def load_cookies(driver):
    """Load cookies from file"""
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, 'rb') as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        print(f"✅ Cookies loaded from {COOKIES_FILE}")
        return True
    return False

def check_login_status(driver, force_reload=False):
    """Check if user is logged in by visiting the results page"""
    if force_reload or 'screener.in' not in driver.current_url:
        driver.get("https://www.screener.in/results/latest/")
        time.sleep(3)
    else:
        time.sleep(1)
    
    if '/register/' in driver.current_url or '/login/' in driver.current_url:
        return False
    
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table', class_='data-table')
        if len(tables) > 0:
            return True
    except:
        pass
    
    return False

def get_chrome_options():
    """Get Chrome options configured for Streamlit Cloud"""
    chrome_options = Options()
    
    # Essential headless flags
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    
    # Additional stability flags
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Memory optimization
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--disable-setuid-sandbox')
    
    return chrome_options

def init_driver(headless=True):
    """Initialize driver with proper configuration for Streamlit Cloud"""
    chrome_options = get_chrome_options()
    
    try:
        # Try using webdriver-manager first
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"WebDriver Manager failed: {e}")
        try:
            # Fallback: try system chromium-driver
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e2:
            print(f"System chromedriver failed: {e2}")
            # Last resort: let selenium find it
            driver = webdriver.Chrome(options=chrome_options)
    
    # Load cookies if they exist
    driver.get("https://www.screener.in")
    time.sleep(2)
    load_cookies(driver)
    
    return driver

def verify_login():
    """Verify if we have valid login cookies"""
    if not os.path.exists(COOKIES_FILE):
        return False
    
    try:
        driver = init_driver(headless=True)
        is_logged_in = check_login_status(driver, force_reload=True)
        driver.quit()
        return is_logged_in
    except Exception as e:
        print(f"Login verification error: {e}")
        return False

def scrape_page(driver, page_num, delay=5):
    url = f"https://www.screener.in/results/latest/?p={page_num}" if page_num > 1 else "https://www.screener.in/results/latest/"
    
    print(f"Fetching: {url}")
    driver.get(url)
    time.sleep(8)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    companies = []
    
    tables = soup.find_all('table', class_='data-table')
    print(f"Found {len(tables)} tables")
    
    if len(tables) == 0:
        print(f"NO TABLES FOUND on page {page_num}")
        return []
    
    for idx, table in enumerate(tables):
        try:
            company_data = {}
            
            prev_element = table.find_previous('a', class_='font-weight-500')
            if prev_element:
                span = prev_element.find('span')
                if span:
                    company_data['Company'] = span.text.strip()
                    print(f"  {idx+1}. {company_data['Company']}")
            
            metrics_div = table.find_previous('div', class_='font-size-14')
            if metrics_div:
                spans = metrics_div.find_all('span', class_='sub')
                for span in spans:
                    text = span.get_text()
                    strong = span.find('span', class_='strong')
                    if strong:
                        if 'Price' in text:
                            company_data['Price'] = parse_value(strong.text)
                        elif 'M.Cap' in text:
                            company_data['Market_Cap'] = parse_value(strong.text)
                        elif 'PE' in text:
                            company_data['PE'] = parse_value(strong.text)
            
            rows = table.find('tbody').find_all('tr')
            if len(rows) < 4:
                continue
            
            # Sales
            cells = rows[0].find_all('td')
            company_data['Sales_YOY'] = parse_yoy(cells[1].text)
            company_data['Sales_Dec25'] = parse_value(cells[2].text)
            company_data['Sales_Sep25'] = parse_value(cells[3].text)
            company_data['Sales_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
            
            # EBIDT
            cells = rows[1].find_all('td')
            company_data['EBIDT_YOY'] = parse_yoy(cells[1].text)
            company_data['EBIDT_Dec25'] = parse_value(cells[2].text)
            company_data['EBIDT_Sep25'] = parse_value(cells[3].text)
            company_data['EBIDT_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
            
            # Net Profit
            cells = rows[2].find_all('td')
            company_data['NetProfit_YOY'] = parse_yoy(cells[1].text)
            company_data['NetProfit_Dec25'] = parse_value(cells[2].text)
            company_data['NetProfit_Sep25'] = parse_value(cells[3].text)
            company_data['NetProfit_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
            
            # EPS
            cells = rows[3].find_all('td')
            company_data['EPS_YOY'] = parse_yoy(cells[1].text)
            company_data['EPS_Dec25'] = parse_value(cells[2].text)
            company_data['EPS_Sep25'] = parse_value(cells[3].text)
            company_data['EPS_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
            
            companies.append(company_data)
            
        except Exception as e:
            print(f"Error on table {idx}: {e}")
            continue
    
    print(f"Parsed {len(companies)} companies")
    time.sleep(delay)
    return companies

def worker_scrape_pages(worker_id, pages_to_scrape, delay, progress_callback=None, total_pages=0):
    """Worker function to scrape assigned pages"""
    driver = init_driver(headless=True)
    worker_data = []
    
    try:
        for idx, page_num in enumerate(pages_to_scrape, 1):
            try:
                print(f"[Worker {worker_id}] Page {page_num}")
                companies = scrape_page(driver, page_num, delay=delay)
                worker_data.extend(companies)
                
                if progress_callback:
                    with progress_lock:
                        progress_callback(1, total_pages)
                    
            except Exception as e:
                print(f"[Worker {worker_id}] Error on page {page_num}: {e}")
                time.sleep(10)
                continue
    finally:
        driver.quit()
    
    return worker_data

def scrape_all_pages(pages_list=None, progress_callback=None, num_workers=1, delay=5):
    """
    Scrape pages with parallel workers
    
    Args:
        pages_list: List of page numbers to scrape
        progress_callback: Callback function(completed, total)
        num_workers: Number of parallel workers (1-5 recommended)
        delay: Delay in seconds between page requests
    """
    if pages_list is None:
        pages_list = list(range(1, 81))
    
    total_pages = len(pages_list)
    
    if num_workers == 1:
        driver = init_driver()
        all_data = []
        
        try:
            for idx, page_num in enumerate(pages_list, 1):
                try:
                    print(f"\nPage {page_num} ({idx}/{total_pages})")
                    companies = scrape_page(driver, page_num, delay=delay)
                    all_data.extend(companies)
                    
                    if progress_callback:
                        progress_callback(idx, total_pages)
                        
                except Exception as e:
                    print(f"Error on page {page_num}: {e}")
                    time.sleep(10)
                    continue
        finally:
            driver.quit()
        
        return pd.DataFrame(all_data)
    
    else:
        print(f"\n🚀 Starting {num_workers} parallel workers...")
        
        chunk_size = max(1, len(pages_list) // num_workers)
        remainder = len(pages_list) % num_workers
        
        worker_pages = []
        start_idx = 0
        
        for i in range(num_workers):
            current_chunk_size = chunk_size + (1 if i < remainder else 0)
            end_idx = start_idx + current_chunk_size
            
            if start_idx < len(pages_list):
                worker_pages.append(pages_list[start_idx:end_idx])
            else:
                worker_pages.append([])
            
            start_idx = end_idx
        
        for i, pages in enumerate(worker_pages, 1):
            if pages:
                print(f"Worker {i}: {len(pages)} pages - {pages[:5]}{'...' if len(pages) > 5 else ''}")
        
        all_data = []
        completed_pages = [0]
        
        def update_progress(increment, total):
            completed_pages[0] += increment
            if progress_callback:
                progress_callback(completed_pages[0], total)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for worker_id, pages in enumerate(worker_pages, 1):
                if pages:
                    future = executor.submit(
                        worker_scrape_pages, 
                        worker_id, 
                        pages, 
                        delay,
                        update_progress,
                        total_pages
                    )
                    futures.append(future)
            
            for future in as_completed(futures):
                try:
                    worker_data = future.result()
                    all_data.extend(worker_data)
                except Exception as e:
                    print(f"Worker failed: {e}")
        
        print(f"\n✅ All workers completed. Total companies: {len(all_data)}")
        return pd.DataFrame(all_data)

if __name__ == "__main__":
    df = scrape_all_pages(pages_list=[1])
    print(df.head())
    print(f"Total: {len(df)}")
