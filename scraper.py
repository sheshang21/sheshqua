import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def parse_value(value_str):
    """Parse numeric values, handle None/empty"""
    if not value_str or value_str.strip() == '' or value_str == 'None':
        return None
    try:
        # Remove ₹ symbol and commas
        cleaned = value_str.replace('₹', '').replace(',', '').strip()
        return float(cleaned)
    except:
        return None

def parse_yoy(yoy_str):
    """Extract YOY percentage"""
    if not yoy_str:
        return None
    match = re.search(r'([⇡⇣])\s*(\d+)%', yoy_str)
    if match:
        direction, value = match.groups()
        return float(value) if direction == '⇡' else -float(value)
    return None

def scrape_page(page_num):
    """Scrape single page"""
    url = f"https://www.screener.in/results/latest/?p={page_num}" if page_num > 1 else "https://www.screener.in/results/latest/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"Fetching URL: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    print(f"Got response: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    companies = []
    
    # Find all company blocks
    blocks = soup.find_all('div', class_='flex-row flex-space-between flex-align-center margin-top-32')
    print(f"Found {len(blocks)} company blocks")
    
    for idx, block in enumerate(blocks):
        try:
            company_data = {}
            
            # Company name
            company_link = block.find('a', class_='font-weight-500')
            if company_link:
                company_data['Company'] = company_link.find('span').text.strip()
                print(f"  {idx+1}. {company_data['Company']}")
            
            # Price, Market Cap, PE
            price_span = block.find('span', string='Price')
            if price_span:
                price_value = price_span.find_next('span', class_='strong')
                if price_value:
                    company_data['Price'] = parse_value(price_value.text)
            
            mcap_span = block.find('span', attrs={'data-mcap': ''})
            if mcap_span:
                mcap_value = mcap_span.find('span', class_='strong')
                if mcap_value:
                    company_data['Market_Cap'] = parse_value(mcap_value.text)
            
            pe_spans = block.find_all('span', class_='sub')
            for span in pe_spans:
                if 'PE' in span.get_text():
                    pe_value = span.find('span', class_='strong')
                    if pe_value:
                        company_data['PE'] = parse_value(pe_value.text)
            
            # Find corresponding table
            table = block.find_next('table', class_='data-table')
            if table:
                rows = table.find('tbody').find_all('tr')
                
                # Sales row
                sales_row = rows[0]
                cells = sales_row.find_all('td')
                company_data['Sales_YOY'] = parse_yoy(cells[1].text)
                company_data['Sales_Dec25'] = parse_value(cells[2].text)
                company_data['Sales_Sep25'] = parse_value(cells[3].text)
                company_data['Sales_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
                
                # EBIDT row
                ebidt_row = rows[1]
                cells = ebidt_row.find_all('td')
                company_data['EBIDT_YOY'] = parse_yoy(cells[1].text)
                company_data['EBIDT_Dec25'] = parse_value(cells[2].text)
                company_data['EBIDT_Sep25'] = parse_value(cells[3].text)
                company_data['EBIDT_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
                
                # Net Profit row
                profit_row = rows[2]
                cells = profit_row.find_all('td')
                company_data['NetProfit_YOY'] = parse_yoy(cells[1].text)
                company_data['NetProfit_Dec25'] = parse_value(cells[2].text)
                company_data['NetProfit_Sep25'] = parse_value(cells[3].text)
                company_data['NetProfit_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
                
                # EPS row
                eps_row = rows[3]
                cells = eps_row.find_all('td')
                company_data['EPS_YOY'] = parse_yoy(cells[1].text)
                company_data['EPS_Dec25'] = parse_value(cells[2].text)
                company_data['EPS_Sep25'] = parse_value(cells[3].text)
                company_data['EPS_Dec24'] = parse_value(cells[4].text) if len(cells) > 4 else None
            
            companies.append(company_data)
        except Exception as e:
            print(f"Error parsing company {idx+1}: {e}")
            continue
    
    print(f"Successfully parsed {len(companies)} companies")
    return companies

def scrape_all_pages(pages_list=None, progress_callback=None):
    """Scrape specified pages with rate limiting"""
    if pages_list is None:
        pages_list = list(range(1, 81))  # Default: all pages
    
    all_data = []
    total_pages = len(pages_list)
    
    for idx, page_num in enumerate(pages_list, 1):
        try:
            print(f"Scraping page {page_num} ({idx}/{total_pages})...")
            companies = scrape_page(page_num)
            all_data.extend(companies)
            
            if progress_callback:
                progress_callback(idx, total_pages)
            
            # Rate limiting: 5 seconds between requests (strict)
            if idx < total_pages:
                time.sleep(5)
                
        except Exception as e:
            print(f"Error on page {page_num}: {e}")
            if '429' in str(e):
                print("Rate limited - waiting 30 seconds...")
                time.sleep(30)  # Long wait for rate limit
            else:
                time.sleep(10)  # Longer wait on other errors
            continue
    
    return pd.DataFrame(all_data)

if __name__ == "__main__":
    # Test with specific pages
    df = scrape_all_pages(pages_list=[1, 2, 3])
    print(df.head())
    print(f"Total companies: {len(df)}")
