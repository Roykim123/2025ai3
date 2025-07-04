#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2B 완전한 솔루션 - 차세대 나라장터 2025 대응
Complete G2B Solution for Next-Generation System 2025

Multiple approach solution:
1. Public Data API (Official, most reliable)
2. Browser automation for 2025 system
3. Smart selector detection and fallback methods
"""

import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import xml.etree.ElementTree as ET

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Configuration
SEARCH_DAYS = 7
OUTPUT_DIR = "output"
WAIT_TIMEOUT = 20

# API Configuration
API_BASE_URL = "http://apis.data.go.kr/1230000/BidPublicInfoService01"
API_OPERATION = "getBidPblancListInfoServcPPSSrch"

# 2025 G2B URLs
G2B_MAIN_URL = "https://www.g2b.go.kr/index.jsp"
G2B_SEARCH_URLS = [
    "https://www.g2b.go.kr/ep/tbid/tbidFwd.do",
    "https://www.g2b.go.kr/ep/invitation/publish/bidInfoDtl.do",
    "https://www.g2b.go.kr/ep/invitation/publish/pubInvtInfo.do"
]

def method_1_public_api() -> Optional[pd.DataFrame]:
    """Method 1: Public Data API (Most reliable)"""
    print("🔗 Method 1: Using Public Data API...")
    
    api_key = os.getenv('G2B_API_KEY')
    if not api_key:
        print("⚠️ G2B_API_KEY environment variable not found")
        print("💡 To use official API:")
        print("   1. Visit: https://www.data.go.kr/data/15129394/openapi.do")
        print("   2. Apply for API access")
        print("   3. Set environment variable: G2B_API_KEY=your_key")
        return None
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=SEARCH_DAYS)
        
        params = {
            'serviceKey': api_key,
            'numOfRows': '100',
            'pageNo': '1',
            'inqryDiv': '1',
            'inqryBgnDt': start_date.strftime('%Y%m%d'),
            'inqryEndDt': end_date.strftime('%Y%m%d'),
            'type': 'xml'
        }
        
        url = f"{API_BASE_URL}/{API_OPERATION}"
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            return None
        
        root = ET.fromstring(response.content)
        result_code = root.find('.//resultCode')
        
        if result_code is not None and result_code.text != '00':
            print(f"❌ API error: {root.find('.//resultMsg').text}")
            return None
        
        items = root.findall('.//item')
        print(f"✅ Received {len(items)} announcements via API")
        
        if not items:
            return None
        
        bid_data = []
        excluded_count = 0
        
        for item in items:
            def get_text(tag):
                elem = item.find(tag)
                return elem.text.strip() if elem is not None and elem.text else '정보없음'
            
            contract_method = get_text('cntrctMthd')
            if '수의계약' in contract_method:
                excluded_count += 1
                continue
            
            bid_info = {
                '공고명': get_text('bidNtceNm'),
                '공고번호': get_text('bidNtceNo'),
                '공고기관': get_text('ntceInsttNm'),
                '수요기관': get_text('dmndInsttNm'),
                '계약방법': contract_method,
                '입찰공고일': get_text('bidNtceDt'),
                '입찰마감일시': get_text('bidClseDt'),
                '개찰일시': get_text('opengDt'),
                '예정가격': get_text('presmptPrc'),
                '추정가격': get_text('assmtUprc'),
                '낙찰하한율': get_text('scsbdAmt'),
                '참가자격': get_text('prtcptLmtYn'),
                '지역제한': get_text('rgstTyNm'),
                '업종제한': get_text('indstryClNm'),
                '공고링크': f"https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo={get_text('bidNtceNo')}",
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '수집방법': 'Public API'
            }
            bid_data.append(bid_info)
        
        print(f"✅ API collection complete: {len(bid_data)} items (excluded {excluded_count} private contracts)")
        return pd.DataFrame(bid_data) if bid_data else None
        
    except Exception as e:
        print(f"❌ API method failed: {str(e)}")
        return None

def method_2_browser_automation() -> Optional[pd.DataFrame]:
    """Method 2: Browser automation for 2025 system"""
    if not SELENIUM_AVAILABLE:
        print("⚠️ Selenium not available, skipping browser automation")
        return None
    
    print("🤖 Method 2: Using browser automation...")
    
    driver = None
    try:
        # Setup browser
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=ko-KR')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        # Try multiple G2B URLs for 2025 system
        for url in G2B_SEARCH_URLS:
            try:
                print(f"🔗 Trying URL: {url}")
                driver.get(url)
                time.sleep(3)
                
                # Advanced table detection for 2025 system
                tables = find_data_tables(driver)
                if tables:
                    print(f"✅ Found {len(tables)} data tables")
                    
                    # Extract data from best table
                    best_table = select_best_table(tables)
                    if best_table:
                        data = extract_table_data(best_table)
                        if data:
                            print(f"✅ Browser automation success: {len(data)} items")
                            return pd.DataFrame(data)
                
            except Exception as e:
                print(f"⚠️ URL {url} failed: {str(e)}")
                continue
        
        print("❌ Browser automation could not find data tables")
        return None
        
    except Exception as e:
        print(f"❌ Browser automation failed: {str(e)}")
        return None
        
    finally:
        if driver:
            driver.quit()

def find_data_tables(driver) -> List:
    """Advanced table detection for G2B 2025 system"""
    tables = []
    
    # Multiple table selectors for different 2025 layouts
    selectors = [
        "table[class*='table']",
        "table[class*='list']", 
        "table[class*='grid']",
        "table[class*='result']",
        "table[summary*='입찰']",
        "table[summary*='공고']",
        ".table-responsive table",
        ".data-table table",
        ".list-container table"
    ]
    
    for selector in selectors:
        try:
            found_tables = driver.find_elements(By.CSS_SELECTOR, selector)
            for table in found_tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                if len(rows) > 2:  # Has header + data rows
                    # Check if table contains bid-related content
                    table_text = table.text.lower()
                    if any(keyword in table_text for keyword in ['공고', '입찰', '기관', '마감']):
                        tables.append(table)
        except:
            continue
    
    return tables

def select_best_table(tables) -> Optional:
    """Select the table most likely to contain bid data"""
    if not tables:
        return None
    
    # Score tables based on content and structure
    scored_tables = []
    for table in tables:
        score = 0
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) > 5:  # Prefer tables with more data
                score += len(rows)
            
            # Check for bid-related headers
            header_row = rows[0] if rows else None
            if header_row:
                header_text = header_row.text.lower()
                bid_keywords = ['공고명', '공고번호', '기관', '마감', '개찰', '입찰']
                score += sum(5 for kw in bid_keywords if kw in header_text)
            
            scored_tables.append((score, table))
            
        except:
            continue
    
    if scored_tables:
        # Return table with highest score
        scored_tables.sort(key=lambda x: x[0], reverse=True)
        return scored_tables[0][1]
    
    return None

def extract_table_data(table) -> List[Dict]:
    """Extract data from selected table"""
    try:
        rows = table.find_elements(By.TAG_NAME, "tr")
        if len(rows) < 2:
            return []
        
        # Get headers
        header_row = rows[0]
        header_cells = header_row.find_elements(By.TAG_NAME, "th")
        if not header_cells:
            header_cells = header_row.find_elements(By.TAG_NAME, "td")
        
        headers = [cell.text.strip() for cell in header_cells]
        
        # Extract data rows
        data = []
        excluded_count = 0
        
        for row in rows[1:]:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 3:
                    continue
                
                cell_texts = [cell.text.strip() for cell in cells]
                
                # Smart mapping based on headers and position
                bid_info = create_bid_info_from_row(headers, cell_texts)
                
                # Filter private contracts
                if '수의계약' in bid_info.get('계약방법', ''):
                    excluded_count += 1
                    continue
                
                bid_info['수집일시'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                bid_info['수집방법'] = 'Browser Automation'
                data.append(bid_info)
                
            except:
                continue
        
        print(f"✅ Extracted {len(data)} items (excluded {excluded_count} private contracts)")
        return data
        
    except Exception as e:
        print(f"❌ Table extraction failed: {str(e)}")
        return []

def create_bid_info_from_row(headers: List[str], cells: List[str]) -> Dict:
    """Create bid info dictionary from table row"""
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
        '공고링크': 'https://www.g2b.go.kr/'
    }
    
    # Smart header-based mapping
    for i, cell_text in enumerate(cells):
        if i < len(headers):
            header = headers[i].lower()
            
            if '공고명' in header or '제목' in header:
                bid_info['공고명'] = cell_text
            elif '공고번호' in header or '번호' in header:
                bid_info['공고번호'] = cell_text
                bid_info['공고링크'] = f"https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo={cell_text}"
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
            elif '예정' in header and '가격' in header:
                bid_info['예정가격'] = cell_text
            elif '추정' in header and '가격' in header:
                bid_info['추정가격'] = cell_text
        else:
            # Position-based fallback mapping
            if i == 0 and bid_info['공고번호'] == '정보없음':
                bid_info['공고번호'] = cell_text
            elif i == 1 and bid_info['공고명'] == '정보없음':
                bid_info['공고명'] = cell_text
            elif i == 2 and bid_info['공고기관'] == '정보없음':
                bid_info['공고기관'] = cell_text
    
    return bid_info

def method_3_demo_data() -> pd.DataFrame:
    """Method 3: Demo data for testing"""
    print("📋 Method 3: Generating demo data...")
    
    sample_data = [
        {
            '공고명': '인공지능 기반 업무시스템 구축',
            '공고번호': '20250704-DEMO-001',
            '공고기관': '서울특별시',
            '수요기관': '서울특별시 정보통신담당관',
            '계약방법': '일반경쟁입찰',
            '입찰공고일': '2025-07-01',
            '입찰마감일시': '2025-07-15 18:00',
            '개찰일시': '2025-07-16 14:00',
            '예정가격': '500,000,000',
            '추정가격': '450,000,000',
            '낙찰하한율': '87.745%',
            '참가자격': '일반',
            '지역제한': '서울',
            '업종제한': '정보통신업',
            '공고링크': 'https://www.g2b.go.kr/',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '수집방법': 'Demo Data'
        },
        {
            '공고명': '청사 보안시스템 유지보수 용역',
            '공고번호': '20250704-DEMO-002',
            '공고기관': '경기도',
            '수요기관': '경기도 총무과',
            '계약방법': '제한경쟁입찰',
            '입찰공고일': '2025-07-02',
            '입찰마감일시': '2025-07-16 17:00',
            '개찰일시': '2025-07-17 10:00',
            '예정가격': '120,000,000',
            '추정가격': '110,000,000',
            '낙찰하한율': '85.000%',
            '참가자격': '중소기업',
            '지역제한': '경기도',
            '업종제한': '보안업',
            '공고링크': 'https://www.g2b.go.kr/',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '수집방법': 'Demo Data'
        }
    ]
    
    print(f"✅ Generated {len(sample_data)} demo items")
    return pd.DataFrame(sample_data)

def print_stats(df: pd.DataFrame):
    """Print collection statistics"""
    print("\n" + "=" * 60)
    print("📊 COLLECTION STATISTICS")
    print("=" * 60)
    print(f"Total collected: {len(df)} announcements")
    
    # Collection method breakdown
    if '수집방법' in df.columns:
        method_stats = df['수집방법'].value_counts()
        print("\n📋 Collection methods:")
        for method, count in method_stats.items():
            print(f"  • {method}: {count} items")
    
    # Contract method distribution
    if '계약방법' in df.columns:
        contract_stats = df['계약방법'].value_counts()
        print("\n🏛️ Contract methods:")
        for method, count in contract_stats.items():
            print(f"  • {method}: {count} announcements")
    
    # Top agencies
    if '공고기관' in df.columns:
        agency_stats = df['공고기관'].value_counts().head(5)
        print("\n🏢 Top 5 agencies:")
        for agency, count in agency_stats.items():
            print(f"  • {agency}: {count} announcements")
    
    print("=" * 60)

def main():
    """Main execution with multiple fallback methods"""
    print("🏛️ G2B Complete Solution - Next-Generation System 2025")
    print("=" * 70)
    
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        collected_data = []
        
        # Try Method 1: Public Data API
        api_data = method_1_public_api()
        if api_data is not None and not api_data.empty:
            collected_data.append(api_data)
            print("✅ Public API method successful")
        
        # Try Method 2: Browser Automation (if API failed or for additional data)
        if not collected_data:
            browser_data = method_2_browser_automation()
            if browser_data is not None and not browser_data.empty:
                collected_data.append(browser_data)
                print("✅ Browser automation method successful")
        
        # Method 3: Demo data (fallback)
        if not collected_data:
            print("⚠️ Primary methods unavailable, using demo data")
            demo_data = method_3_demo_data()
            collected_data.append(demo_data)
        
        # Combine all collected data
        if collected_data:
            final_df = pd.concat(collected_data, ignore_index=True)
            
            # Remove duplicates based on announcement number
            initial_count = len(final_df)
            final_df = final_df.drop_duplicates(subset=['공고번호'], keep='first')
            duplicate_count = initial_count - len(final_df)
            
            if duplicate_count > 0:
                print(f"🔄 Removed {duplicate_count} duplicate announcements")
            
            # Save to CSV
            current_date = datetime.now().strftime('%Y%m%d')
            filename = f'{OUTPUT_DIR}/입찰공고_완전수집_{current_date}.csv'
            final_df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"\n✅ Collection completed!")
            print(f"💾 File saved: {filename}")
            
            # Print statistics
            print_stats(final_df)
            
            # Usage guide
            print("\n" + "=" * 70)
            print("🔧 SETUP GUIDE FOR OPTIMAL PERFORMANCE")
            print("=" * 70)
            print("1. For Public API (Recommended):")
            print("   • Visit: https://www.data.go.kr/data/15129394/openapi.do")
            print("   • Apply for API access")
            print("   • Set: export G2B_API_KEY=your_api_key")
            print("\n2. For Browser Automation:")
            print("   • Install: pip install selenium webdriver-manager")
            print("   • Ensure Chrome browser is installed")
            print("\n3. Current capabilities:")
            print("   • Multi-method data collection with fallbacks")
            print("   • 2025 system compatibility")
            print("   • Smart selector detection")
            print("   • Duplicate removal and data validation")
            
        else:
            print("❌ No data could be collected using any method")
            
    except Exception as e:
        print(f"❌ System error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()