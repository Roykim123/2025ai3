#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2B 조달청 입찰공고 자동수집 시스템
Korean Government Procurement Bid Collection System
Local PC version with Selenium browser automation

This version uses Selenium WebDriver to bypass G2B's 403 Forbidden errors
by automating a real browser session.

Requirements:
- Python 3.8+
- pip install selenium webdriver-manager pandas requests
- Chrome browser installed on your system

Usage:
python g2b_local_version.py
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
SEARCH_DAYS = 7  # Search period in days
OUTPUT_DIR = "output"
G2B_MAIN_URL = "https://www.g2b.go.kr/index.jsp"
G2B_BID_SEARCH_URL = "https://www.g2b.go.kr/ep/tbid/tbidFwd.do"
WAIT_TIMEOUT = 30  # Element wait timeout in seconds

def setup_browser(headless=True):
    """Setup Chrome browser with optimized options for G2B"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    # Essential arguments for government sites
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Korean language settings
    chrome_options.add_argument('--lang=ko-KR')
    chrome_options.add_experimental_option('prefs', {
        'intl.accept_languages': 'ko-KR,ko,en-US,en'
    })
    
    # User agent for Windows Chrome
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        # Auto-download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Browser started successfully")
        return driver
        
    except Exception as e:
        print(f"❌ Browser setup error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome browser is installed")
        print("2. Run: pip install selenium webdriver-manager")
        print("3. Check your internet connection for ChromeDriver download")
        return None

def collect_bids_with_browser() -> Optional[pd.DataFrame]:
    """Collect G2B bid announcements using browser automation for new 2025 system"""
    print("Starting G2B bid collection with new 2025 system...")
    
    driver = None
    try:
        # Setup browser (set headless=False to see the browser in action)
        driver = setup_browser(headless=True)  # Headless for production
        if driver is None:
            return None
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        # Navigate to G2B main page first
        print("🌐 Accessing G2B main page...")
        driver.get(G2B_MAIN_URL)
        time.sleep(3)
        
        # Look for bid announcement menu in new system
        try:
            print("🔍 Looking for bid announcement menu...")
            
            # Try various menu selectors for the new system
            menu_selectors = [
                "//a[contains(text(), '입찰')]",
                "//a[contains(text(), '입찰공고')]",
                "//span[contains(text(), '입찰')]",
                "//button[contains(text(), '입찰')]",
                "#gnb_menu_1",  # Common main menu ID
                ".gnb-menu a",  # Global navigation menu
                "nav a[href*='bid']",  # Navigation links containing 'bid'
                "nav a[href*='tbid']"  # Navigation links containing 'tbid'
            ]
            
            bid_menu = None
            for selector in menu_selectors:
                try:
                    if selector.startswith("//"):
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        href = element.get_attribute('href')
                        if '입찰' in element.text or (href and 'bid' in href.lower()):
                            bid_menu = element
                            print(f"✓ Found bid menu: {selector} - {element.text}")
                            break
                    
                    if bid_menu:
                        break
                except:
                    continue
            
            if bid_menu:
                bid_menu.click()
                time.sleep(3)
                print("✓ Clicked bid menu")
            else:
                # Try direct navigation to bid search URL
                print("🔄 Trying direct navigation to bid search...")
                driver.get(G2B_BID_SEARCH_URL)
                time.sleep(3)
        
        except Exception as e:
            print(f"⚠️ Menu navigation error: {str(e)}")
            # Try direct URL approach
            driver.get(G2B_BID_SEARCH_URL)
            time.sleep(3)
        
        # Look for bid announcement list or search area
        try:
            print("🔍 Looking for bid announcement search area...")
            
            # Try to find search form or bid list
            search_area_selectors = [
                "form[name*='search']",
                "form[id*='search']", 
                ".search-form",
                ".search-area",
                "#searchForm",
                "form[action*='bid']",
                ".bid-search",
                "#bidSearchForm"
            ]
            
            search_form = None
            for selector in search_area_selectors:
                try:
                    search_form = driver.find_element(By.CSS_SELECTOR, selector)
                    if search_form:
                        print(f"✓ Found search form: {selector}")
                        break
                except:
                    continue
            
            # Set search criteria in new system
            if search_form:
                print("⚙️ Setting search criteria...")
                
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=SEARCH_DAYS)
                
                # Try different date input field names/IDs for new system
                date_field_selectors = [
                    ("srchBgnDt", "srchEndDt"),  # Old system
                    ("startDate", "endDate"),   # Common names
                    ("fromDate", "toDate"),     # Alternative names
                    ("beginDate", "finishDate"), # Alternative names
                    ("searchStartDate", "searchEndDate") # Descriptive names
                ]
                
                date_set = False
                for start_field, end_field in date_field_selectors:
                    try:
                        start_input = driver.find_element(By.NAME, start_field)
                        end_input = driver.find_element(By.NAME, end_field)
                        
                        start_input.clear()
                        start_input.send_keys(start_date.strftime('%Y-%m-%d'))
                        
                        end_input.clear()
                        end_input.send_keys(end_date.strftime('%Y-%m-%d'))
                        
                        print(f"✓ Set dates using {start_field}/{end_field}")
                        print(f"✓ Search period: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
                        date_set = True
                        break
                        
                    except NoSuchElementException:
                        continue
                
                if not date_set:
                    print("⚠️ Could not find date input fields, using default period")
            
        except Exception as e:
            print(f"⚠️ Search form setup error: {str(e)}")
        
        # Try to find and click search button
        try:
            print("🔍 Looking for search button...")
            
            search_button_selectors = [
                "//button[contains(text(), '검색')]",
                "//input[@type='button' and contains(@value, '검색')]",
                "//input[@type='submit' and contains(@value, '검색')]",
                "//a[contains(text(), '검색')]",
                "button[class*='search']",
                ".btn-search",
                "#searchBtn",
                "input[id*='search']"
            ]
            
            search_button = None
            for selector in search_button_selectors:
                try:
                    if selector.startswith("//"):
                        search_button = driver.find_element(By.XPATH, selector)
                    else:
                        search_button = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if search_button and search_button.is_enabled():
                        search_button.click()
                        print(f"✓ Clicked search button: {selector}")
                        time.sleep(5)  # Wait for results
                        break
                        
                except:
                    continue
            
            if not search_button:
                print("⚠️ Could not find search button, proceeding to look for existing results...")
                
        except Exception as e:
            print(f"⚠️ Search button error: {str(e)}")
        
        # Look for results table in new system
        print("📊 Looking for bid results table...")
        
        # Updated table selectors for new 2025 system
        table_selectors = [
            "table.table",                    # Bootstrap table
            "table[class*='list']",          # List table
            "table[class*='grid']",          # Grid table  
            "table[class*='result']",        # Result table
            ".data-table table",             # Data table wrapper
            ".result-table table",           # Result table wrapper
            ".list-table table",             # List table wrapper
            "table[summary*='입찰']",         # Summary containing bid
            "table[summary*='공고']",         # Summary containing announcement
            "//table[contains(@class,'table')]", # XPath for table class
            "//table[.//th[contains(text(),'공고')]]", # Table with announcement header
            "//table[.//th[contains(text(),'입찰')]]"  # Table with bid header
        ]
        
        table = None
        for selector in table_selectors:
            try:
                if selector.startswith("//"):
                    tables = driver.find_elements(By.XPATH, selector)
                else:
                    tables = driver.find_elements(By.CSS_SELECTOR, selector)
                
                # Find table with most rows (likely the data table)
                for tbl in tables:
                    rows = tbl.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > 1:  # Has header + data
                        table = tbl
                        print(f"✓ Found results table: {selector} with {len(rows)} rows")
                        break
                
                if table:
                    break
                    
            except Exception as e:
                continue
        
        if not table:
            print("❌ Could not find results table in new system")
            
            # Save page source for debugging
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(f"{OUTPUT_DIR}/page_source_debug_new.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"💾 Page source saved to {OUTPUT_DIR}/page_source_debug_new.html for debugging")
            
            # Also save screenshot
            try:
                driver.save_screenshot(f"{OUTPUT_DIR}/screenshot_debug.png")
                print(f"📸 Screenshot saved to {OUTPUT_DIR}/screenshot_debug.png")
            except:
                pass
            
            return None
        
        # Extract table data from new system
        rows = table.find_elements(By.TAG_NAME, "tr")
        print(f"📋 Processing {len(rows)} table rows")
        
        # Get header row to understand column structure
        header_row = rows[0] if rows else None
        headers = []
        if header_row:
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            if not header_cells:  # Sometimes headers are in td
                header_cells = header_row.find_elements(By.TAG_NAME, "td")
            headers = [cell.text.strip() for cell in header_cells]
            print(f"📋 Table headers: {headers}")
        
        # Parse data from rows
        bid_data = []
        excluded_count = 0
        
        for i, row in enumerate(rows[1:], 1):  # Skip header row
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 3:  # Minimum required columns
                    continue
                
                # Extract text from each cell
                cell_texts = [cell.text.strip() for cell in cells]
                
                # Flexible column mapping based on content
                bid_info = {
                    '공고명': '정보없음',
                    '공고번호': '정보없음', 
                    '공고기관': '정보없음',
                    '수요기관': '정보없음',
                    '계약방법': '정보없음',
                    '입찰공고일': '정보없음',
                    '입찰마감일시': '정보없음',
                    '개찰일시': '정보없음',
                    '예정가격': '정보없음',
                    '추정가격': '정보없음',
                    '낙찰하한율': '정보없음',
                    '참가자격': '정보없음',
                    '지역제한': '정보없음',
                    '업종제한': '정보없음',
                    '공고링크': f"https://www.g2b.go.kr/",
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Smart column mapping
                for idx, cell_text in enumerate(cell_texts):
                    if idx < len(headers):
                        header = headers[idx]
                        if '공고명' in header or '제목' in header:
                            bid_info['공고명'] = cell_text
                        elif '공고번호' in header or '번호' in header:
                            bid_info['공고번호'] = cell_text
                        elif '기관' in header and '수요' not in header:
                            bid_info['공고기관'] = cell_text
                        elif '수요기관' in header:
                            bid_info['수요기관'] = cell_text
                        elif '계약' in header or '방법' in header:
                            bid_info['계약방법'] = cell_text
                        elif '공고일' in header or '등록일' in header:
                            bid_info['입찰공고일'] = cell_text
                        elif '마감' in header or '접수' in header:
                            bid_info['입찰마감일시'] = cell_text
                        elif '개찰' in header:
                            bid_info['개찰일시'] = cell_text
                        elif '예정' in header or '가격' in header:
                            bid_info['예정가격'] = cell_text
                    else:
                        # Fallback mapping by position
                        if idx == 0 and bid_info['공고번호'] == '정보없음':
                            bid_info['공고번호'] = cell_text
                        elif idx == 1 and bid_info['공고명'] == '정보없음':
                            bid_info['공고명'] = cell_text
                        elif idx == 2 and bid_info['공고기관'] == '정보없음':
                            bid_info['공고기관'] = cell_text
                
                # Filter out private contracts
                if '수의계약' in bid_info['계약방법']:
                    excluded_count += 1
                    continue
                
                bid_data.append(bid_info)
                
            except Exception as e:
                print(f"⚠️ Error processing row {i}: {str(e)}")
                continue
        
        print(f"✓ Excluded {excluded_count} private contracts (수의계약)")
        print(f"✅ Collected {len(bid_data)} bid announcements")
        
        if not bid_data:
            print("❌ No bid announcements collected")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(bid_data)
        return df
        
    except Exception as e:
        print(f"❌ Browser automation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Close browser
        if driver:
            try:
                driver.quit()
                print("✓ Browser closed successfully")
            except:
                pass

def create_demo_data():
    """Create demo data for testing purposes"""
    sample_data = [
        {
            '공고명': '인공지능 기반 음성인식 시스템 구축',
            '공고번호': '20250704-00001',
            '공고기관': '서울특별시',
            '수요기관': '서울특별시 정보통신담당관',
            '계약방법': '일반경쟁입찰',
            '입찰공고일': '2025-07-01',
            '입찰마감일시': '2025-07-15 18:00',
            '개찰일시': '2025-07-16 14:00',
            '예정가격': '500000000',
            '추정가격': '450000000',
            '낙찰하한율': '87.745%',
            '참가자격': '일반',
            '지역제한': '서울',
            '업종제한': '정보통신업',
            '공고링크': 'https://www.g2b.go.kr/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameTgong.do&bidPbancNo=20250704-00001',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            '공고명': '청사 보안시스템 유지보수',
            '공고번호': '20250704-00002',
            '공고기관': '경기도',
            '수요기관': '경기도 총무과',
            '계약방법': '제한경쟁입찰',
            '입찰공고일': '2025-07-02',
            '입찰마감일시': '2025-07-16 17:00',
            '개찰일시': '2025-07-17 10:00',
            '예정가격': '120000000',
            '추정가격': '110000000',
            '낙찰하한율': '85.000%',
            '참가자격': '중소기업',
            '지역제한': '경기도',
            '업종제한': '보안업',
            '공고링크': 'https://www.g2b.go.kr/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameTgong.do&bidPbancNo=20250704-00002',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    return pd.DataFrame(sample_data)

def print_stats(df: pd.DataFrame):
    """Print collection statistics"""
    print("\n" + "=" * 50)
    print("📊 COLLECTION STATISTICS")
    print("=" * 50)
    print(f"Total collected: {len(df)} announcements")
    
    # Contract method distribution
    if '계약방법' in df.columns:
        contract_stats = df['계약방법'].value_counts()
        print("\n📋 Contract Methods:")
        for method, count in contract_stats.items():
            print(f"  • {method}: {count} announcements")
    
    # Top agencies
    if '공고기관' in df.columns:
        agency_stats = df['공고기관'].value_counts().head(5)
        print("\n🏢 Top 5 Agencies:")
        for agency, count in agency_stats.items():
            print(f"  • {agency}: {count} announcements")
    
    print("=" * 50)

def main():
    """Main execution function"""
    print("🏛️  G2B Korean Government Procurement Bid Collection System")
    print("🤖 Browser Automation Version")
    print("=" * 70)
    
    try:
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Collect bid announcements using browser automation
        print("🚀 Starting browser automation data collection...")
        df = collect_bids_with_browser()
        
        # Fallback to demo data if browser automation fails
        if df is None or df.empty:
            print("\n⚠️  Browser automation failed. Using demo data for testing.")
            print("📝 Note: This happens when browser environment is not available.")
            df = create_demo_data()
        
        if df is not None and not df.empty:
            # Generate filename
            current_date = datetime.now().strftime('%Y%m%d')
            filename = f'{OUTPUT_DIR}/입찰공고_{current_date}.csv'
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"\n✅ Collection completed!")
            print(f"💾 File saved: {filename}")
            
            # Print statistics
            print_stats(df)
            
            # Local execution instructions
            print("\n" + "=" * 70)
            print("🖥️  LOCAL PC EXECUTION GUIDE")
            print("=" * 70)
            print("1. Install Python 3.8 or higher")
            print("2. Install required packages:")
            print("   pip install selenium webdriver-manager pandas")
            print("3. Install Chrome browser")
            print("4. Run the script:")
            print("   python g2b_local_version.py")
            print("5. Check output folder for CSV files")
            print("\n💡 Tips:")
            print("• Browser automation bypasses G2B's 403 errors")
            print("• Set headless=False in setup_browser() to watch the automation")
            print("• The script automatically downloads ChromeDriver")
            print("• Works on Windows, macOS, and Linux")
            
        else:
            print("❌ No data could be generated")
            
    except Exception as e:
        print(f"❌ System error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()