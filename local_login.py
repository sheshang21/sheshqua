"""
LOCAL LOGIN SCRIPT - Run this locally to generate cookies
This script will NOT work on Streamlit Cloud (requires GUI browser)
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pickle
import time
from bs4 import BeautifulSoup

COOKIES_FILE = 'screener_cookies.pkl'

def check_login_status(driver):
    """Check if user is logged in"""
    driver.get("https://www.screener.in/results/latest/")
    time.sleep(3)
    
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

def save_cookies(driver):
    """Save cookies to file"""
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(cookies, f)
    print(f"✅ Cookies saved to {COOKIES_FILE}")

def load_cookies(driver):
    """Load cookies from file"""
    try:
        with open(COOKIES_FILE, 'rb') as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        print(f"✅ Cookies loaded from {COOKIES_FILE}")
        return True
    except:
        return False

def manual_login():
    """Open browser for manual login"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1200,900')
    
    print("🚀 Starting Chrome browser...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Check existing cookies
        driver.get("https://www.screener.in")
        time.sleep(2)
        
        if load_cookies(driver):
            driver.refresh()
            time.sleep(3)
            if check_login_status(driver):
                print("✅ Already logged in with saved cookies!")
                save_cookies(driver)
                driver.quit()
                return True
        
        # Need manual login
        print("🔐 Opening login page...")
        driver.get("https://www.screener.in/login/")
        
        print("\n" + "="*60)
        print("PLEASE LOGIN TO SCREENER.IN IN THE BROWSER")
        print("="*60)
        print("1. Enter your email/username and password")
        print("2. Click 'Login'")
        print("3. Wait until you see the main page")
        print("4. Browser will close automatically once login is detected")
        print("="*60 + "\n")
        
        # Wait for login
        for i in range(60):
            time.sleep(5)
            if check_login_status(driver):
                print("✅ Login successful!")
                save_cookies(driver)
                driver.quit()
                print(f"\n✅ Cookies saved to {COOKIES_FILE}")
                print("📤 Upload this file to your GitHub repository")
                print("🔄 Redeploy on Streamlit Cloud")
                return True
            print(f"⏳ Waiting for login... ({i*5}s)")
        
        print("❌ Login timeout. Please try again.")
        driver.quit()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        driver.quit()
        return False

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     SCREENER.IN LOGIN - LOCAL COOKIE GENERATOR         ║
    ╚════════════════════════════════════════════════════════╝
    
    This script will:
    1. Open a Chrome browser
    2. Let you login to Screener.in
    3. Save cookies to screener_cookies.pkl
    4. You can then upload this file to GitHub for Streamlit Cloud
    
    Press Ctrl+C to cancel
    """)
    
    input("Press ENTER to start...")
    
    if manual_login():
        print("\n✅ SUCCESS! Next steps:")
        print("1. Find 'screener_cookies.pkl' in this directory")
        print("2. Add it to your GitHub repository")
        print("3. Push to GitHub: git add screener_cookies.pkl && git commit -m 'Add cookies' && git push")
        print("4. Streamlit Cloud will automatically redeploy")
    else:
        print("\n❌ Login failed. Please try again.")
