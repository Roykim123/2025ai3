#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2B Debug Version - 차세대 나라장터 2025 시스템 분석용
디버깅 정보와 페이지 소스 저장에 중점을 둔 버전
"""

import os
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
OUTPUT_DIR = "output"
G2B_MAIN_URL = "https://www.g2b.go.kr/index.jsp"
WAIT_TIMEOUT = 15

def setup_debug_browser():
    """Setup Chrome browser for debugging"""
    chrome_options = Options()
    
    # Headless for Replit
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Korean language
    chrome_options.add_argument('--lang=ko-KR')
    chrome_options.add_experimental_option('prefs', {
        'intl.accept_languages': 'ko-KR,ko,en-US,en'
    })
    
    # User agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Browser started for debugging")
        return driver
    except Exception as e:
        print(f"❌ Browser setup error: {str(e)}")
        return None

def analyze_g2b_structure():
    """Analyze G2B 2025 structure and save debugging info"""
    print("🔍 Analyzing G2B 2025 structure...")
    
    driver = None
    try:
        driver = setup_debug_browser()
        if driver is None:
            return False
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Step 1: Access main page
        print("📄 Accessing G2B main page...")
        driver.get(G2B_MAIN_URL)
        time.sleep(5)
        
        # Save main page source
        with open(f"{OUTPUT_DIR}/main_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"💾 Main page source saved to {OUTPUT_DIR}/main_page_source.html")
        
        # Take screenshot
        try:
            driver.save_screenshot(f"{OUTPUT_DIR}/main_page_screenshot.png")
            print(f"📸 Main page screenshot saved to {OUTPUT_DIR}/main_page_screenshot.png")
        except:
            pass
        
        # Step 2: Look for navigation elements
        print("🔍 Analyzing navigation elements...")
        
        navigation_info = {
            "menus": [],
            "links": [],
            "forms": [],
            "frames": []
        }
        
        # Find all links
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links[:50]:  # Limit to first 50
            try:
                text = link.text.strip()
                href = link.get_attribute('href')
                if text and ('입찰' in text or '공고' in text or (href and 'bid' in href.lower())):
                    navigation_info["links"].append({
                        "text": text,
                        "href": href,
                        "class": link.get_attribute('class'),
                        "id": link.get_attribute('id')
                    })
            except:
                continue
        
        # Find all forms
        forms = driver.find_elements(By.TAG_NAME, "form")
        for form in forms:
            try:
                navigation_info["forms"].append({
                    "action": form.get_attribute('action'),
                    "method": form.get_attribute('method'),
                    "name": form.get_attribute('name'),
                    "id": form.get_attribute('id'),
                    "class": form.get_attribute('class')
                })
            except:
                continue
        
        # Find frames/iframes
        frames = driver.find_elements(By.TAG_NAME, "frame") + driver.find_elements(By.TAG_NAME, "iframe")
        for frame in frames:
            try:
                navigation_info["frames"].append({
                    "src": frame.get_attribute('src'),
                    "name": frame.get_attribute('name'),
                    "id": frame.get_attribute('id')
                })
            except:
                continue
        
        # Step 3: Try common bid-related URLs
        test_urls = [
            "https://www.g2b.go.kr/ep/tbid/tbidFwd.do",
            "https://www.g2b.go.kr/ep/invitation/publish/bidInfoDtl.do",
            "https://www.g2b.go.kr/ep/invitation/publish/pubInvtInfo.do",
            "https://www.g2b.go.kr/ep/invitation/publish/bidInfoSubPub.do"
        ]
        
        for url in test_urls:
            try:
                print(f"🔗 Testing URL: {url}")
                driver.get(url)
                time.sleep(3)
                
                # Save page source
                url_name = url.split('/')[-1].replace('.do', '')
                with open(f"{OUTPUT_DIR}/{url_name}_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"💾 Page source saved for {url_name}")
                
                # Check for tables, forms, search elements
                tables = driver.find_elements(By.TAG_NAME, "table")
                forms = driver.find_elements(By.TAG_NAME, "form")
                search_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search']")
                
                print(f"   Tables found: {len(tables)}")
                print(f"   Forms found: {len(forms)}")
                print(f"   Search inputs found: {len(search_inputs)}")
                
                # Look for bid-related text
                page_text = driver.page_source.lower()
                bid_keywords = ['입찰공고', '공고번호', '공고명', '입찰마감', '개찰일시']
                found_keywords = [kw for kw in bid_keywords if kw in page_text]
                print(f"   Bid keywords found: {found_keywords}")
                
            except Exception as e:
                print(f"   ❌ Error accessing {url}: {str(e)}")
                continue
        
        # Step 4: Save analysis results
        analysis_report = f"""
G2B 2025 Structure Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== NAVIGATION LINKS ===
Bid-related links found: {len(navigation_info['links'])}
"""
        
        for link in navigation_info['links']:
            analysis_report += f"- Text: '{link['text']}' | URL: {link['href']}\n"
        
        analysis_report += f"""
=== FORMS ===
Forms found: {len(navigation_info['forms'])}
"""
        
        for form in navigation_info['forms']:
            analysis_report += f"- Action: {form['action']} | Method: {form['method']} | Name: {form['name']}\n"
        
        analysis_report += f"""
=== FRAMES ===
Frames found: {len(navigation_info['frames'])}
"""
        
        for frame in navigation_info['frames']:
            analysis_report += f"- Src: {frame['src']} | Name: {frame['name']}\n"
        
        with open(f"{OUTPUT_DIR}/g2b_analysis_report.txt", "w", encoding="utf-8") as f:
            f.write(analysis_report)
        
        print(f"✅ Analysis complete! Report saved to {OUTPUT_DIR}/g2b_analysis_report.txt")
        print(f"📁 Check the {OUTPUT_DIR} folder for all debugging files")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
                print("✓ Browser closed")
            except:
                pass

def main():
    """Main execution for debugging"""
    print("🔍 G2B 2025 Structure Debugging Tool")
    print("=" * 50)
    
    success = analyze_g2b_structure()
    
    if success:
        print("\n✅ Debugging completed successfully!")
        print("\n📋 Files generated:")
        print("- main_page_source.html: Main page HTML source")
        print("- main_page_screenshot.png: Screenshot of main page")
        print("- *_source.html: Page sources from tested URLs")
        print("- g2b_analysis_report.txt: Detailed analysis report")
        print("\n💡 Use these files to identify correct selectors and navigation paths")
    else:
        print("\n❌ Debugging failed. Check error messages above.")

if __name__ == "__main__":
    main()