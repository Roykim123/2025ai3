#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2B 조달청 입찰공고 자동수집 시스템
Korean Government Procurement Bid Collection System
Browser automation version using Selenium
"""

import requests
import pandas as pd
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 기본 설정
SEARCH_DAYS = 7  # 검색 기간 (일)
OUTPUT_DIR = "output"
G2B_BASE_URL = "https://www.g2b.go.kr"
G2B_MAIN_URL = "https://www.g2b.go.kr/index.jsp"
G2B_BID_SEARCH_URL = "https://www.g2b.go.kr/ep/tbid/tbidFwd.do"
WAIT_TIMEOUT = 30  # 요소 대기 시간 (초)

def setup_browser():
    """Selenium 브라우저 설정"""
    chrome_options = Options()
    
    # Replit 환경을 위한 설정
    chrome_options.add_argument('--headless')  # GUI 없이 실행
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # 이미지 로딩 비활성화로 속도 향상
    chrome_options.add_argument('--window-size=1920,1080')
    
    # 한국어 설정
    chrome_options.add_argument('--lang=ko-KR')
    chrome_options.add_experimental_option('prefs', {
        'intl.accept_languages': 'ko-KR,ko,en-US,en'
    })
    
    # User-Agent 설정
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        # 자동으로 chromedriver 다운로드 및 설정
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("브라우저가 성공적으로 시작되었습니다.")
            return driver
        except Exception as driver_error:
            print(f"ChromeDriver 자동 설치 실패: {str(driver_error)}")
            
            # 시스템 크롬 경로 시도
            possible_chrome_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
            ]
            
            for chrome_path in possible_chrome_paths:
                if os.path.exists(chrome_path):
                    chrome_options.binary_location = chrome_path
                    try:
                        driver = webdriver.Chrome(options=chrome_options)
                        print(f"시스템 Chrome 브라우저 사용: {chrome_path}")
                        return driver
                    except:
                        continue
            
            raise Exception("Compatible Chrome browser not found")
        
    except Exception as e:
        print(f"브라우저 설정 오류: {str(e)}")
        print("\n해결 방법:")
        print("1. Chrome 브라우저를 설치하세요")
        print("2. 로컬 PC에서 실행하세요 (Replit에서는 브라우저 제한이 있을 수 있습니다)")
        print("3. 다음 명령어로 필요한 패키지를 설치하세요:")
        print("   pip install selenium webdriver-manager")
        return None

def collect_bids_with_browser() -> Optional[pd.DataFrame]:
    """브라우저 자동화를 사용한 G2B 입찰공고 수집"""
    print("브라우저 자동화로 G2B 입찰공고 수집을 시작합니다...")
    
    driver = None
    try:
        # 브라우저 설정
        driver = setup_browser()
        if driver is None:
            return None
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        # G2B 입찰공고 페이지로 이동
        print("G2B 입찰공고 페이지에 접속 중...")
        driver.get(G2B_BID_SEARCH_URL)
        time.sleep(3)  # 페이지 로딩 대기
        
        # 프레임 전환 (G2B는 프레임 구조 사용)
        try:
            # 메인 프레임으로 전환
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
            print("메인 프레임으로 전환 완료")
        except TimeoutException:
            print("프레임을 찾을 수 없습니다. 다른 방법으로 시도합니다...")
        
        # 검색 조건 설정
        try:
            # 검색 기간 설정 (최근 7일)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=SEARCH_DAYS)
            
            # 날짜 입력 필드 찾기 및 설정
            print("검색 조건을 설정 중...")
            
            # 시작일 설정
            start_date_input = wait.until(EC.presence_of_element_located((By.NAME, "srchBgnDt")))
            start_date_input.clear()
            start_date_input.send_keys(start_date.strftime('%Y%m%d'))
            
            # 종료일 설정
            end_date_input = driver.find_element(By.NAME, "srchEndDt")
            end_date_input.clear()
            end_date_input.send_keys(end_date.strftime('%Y%m%d'))
            
            print(f"검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"검색 조건 설정 실패: {str(e)}")
            print("기본 설정으로 진행합니다...")
        
        # 검색 버튼 클릭
        try:
            search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and contains(@value, '검색')]")))
            search_button.click()
            print("검색 버튼 클릭 완료")
            time.sleep(5)  # 검색 결과 로딩 대기
            
        except TimeoutException:
            print("검색 버튼을 찾을 수 없습니다. 다른 방법으로 시도합니다...")
        
        # 테이블 데이터 추출
        print("입찰공고 데이터를 추출 중...")
        
        # 결과 테이블 찾기
        try:
            # 다양한 테이블 선택자 시도
            table_selectors = [
                "table.tbl_type01",
                "table.list_table",
                "table[summary*='입찰공고']",
                "//table[contains(@class, 'list')]"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    if selector.startswith("//"):
                        table = driver.find_element(By.XPATH, selector)
                    else:
                        table = driver.find_element(By.CSS_SELECTOR, selector)
                    if table:
                        print(f"테이블을 찾았습니다: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not table:
                print("결과 테이블을 찾을 수 없습니다.")
                return None
            
            # 테이블 행 추출
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"총 {len(rows)}개의 행을 찾았습니다.")
            
            # 헤더 행 제외하고 데이터 추출
            bid_data = []
            excluded_count = 0
            
            for i, row in enumerate(rows[1:], 1):  # 첫 번째 행(헤더) 제외
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 5:  # 최소 필요한 컬럼 수 확인
                        continue
                    
                    # 각 셀에서 텍스트 추출
                    cell_texts = [cell.text.strip() for cell in cells]
                    
                    # 공고명에서 수의계약 필터링
                    bid_name = cell_texts[1] if len(cell_texts) > 1 else ""
                    contract_method = cell_texts[4] if len(cell_texts) > 4 else ""
                    
                    if '수의계약' in contract_method:
                        excluded_count += 1
                        continue
                    
                    # 데이터 구조화
                    bid_info = {
                        '공고명': bid_name,
                        '공고번호': cell_texts[0] if len(cell_texts) > 0 else '정보없음',
                        '공고기관': cell_texts[2] if len(cell_texts) > 2 else '정보없음',
                        '수요기관': cell_texts[3] if len(cell_texts) > 3 else '정보없음',
                        '계약방법': contract_method,
                        '입찰공고일': cell_texts[5] if len(cell_texts) > 5 else '정보없음',
                        '입찰마감일시': cell_texts[6] if len(cell_texts) > 6 else '정보없음',
                        '개찰일시': cell_texts[7] if len(cell_texts) > 7 else '정보없음',
                        '예정가격': cell_texts[8] if len(cell_texts) > 8 else '정보없음',
                        '추정가격': cell_texts[9] if len(cell_texts) > 9 else '정보없음',
                        '낙찰하한율': '정보없음',
                        '참가자격': '정보없음',
                        '지역제한': '정보없음',
                        '업종제한': '정보없음',
                        '공고링크': f"{G2B_BASE_URL}/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameTgong.do&bidPbancNo={cell_texts[0]}",
                        '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    bid_data.append(bid_info)
                    
                except Exception as e:
                    print(f"행 {i} 처리 중 오류: {str(e)}")
                    continue
            
            print(f"수의계약 {excluded_count}건 제외")
            print(f"최종 {len(bid_data)}건 수집 완료")
            
            if not bid_data:
                print("수집된 입찰공고가 없습니다.")
                return None
            
            # DataFrame 생성
            df = pd.DataFrame(bid_data)
            return df
            
        except Exception as e:
            print(f"데이터 추출 중 오류: {str(e)}")
            return None
            
    except Exception as e:
        print(f"브라우저 자동화 중 오류: {str(e)}")
        return None
        
    finally:
        # 브라우저 종료
        if driver:
            try:
                driver.quit()
                print("브라우저가 정상적으로 종료되었습니다.")
            except:
                pass

def print_stats(df: pd.DataFrame):
    """수집 통계 출력"""
    print("\n=== 수집 통계 ===")
    print(f"총 수집 건수: {len(df)}건")
    
    # 계약방법별 통계
    if '계약방법' in df.columns:
        contract_stats = df['계약방법'].value_counts()
        print("\n계약방법별 분포:")
        for method, count in contract_stats.items():
            print(f"  - {method}: {count}건")
    
    # 공고기관별 통계 (상위 5개)
    if '공고기관' in df.columns:
        agency_stats = df['공고기관'].value_counts().head(5)
        print("\n주요 공고기관 (상위 5개):")
        for agency, count in agency_stats.items():
            print(f"  - {agency}: {count}건")
    
    print("==================\n")

def create_demo_data():
    """데모용 샘플 데이터 생성 (API 접근 불가 시)"""
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

def main():
    """메인 실행 함수"""
    print("G2B 조달청 입찰공고 자동수집 시스템 (Browser Automation)")
    print("=" * 60)
    
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 브라우저 자동화로 입찰공고 수집
        print("브라우저 자동화를 사용하여 데이터를 수집합니다...")
        df = collect_bids_with_browser()
        
        # 브라우저 자동화 실패 시 데모 데이터 사용
        if df is None or df.empty:
            print("\n브라우저 자동화가 실패했습니다. 데모 데이터를 생성합니다.")
            print("실제 환경에서는 브라우저 자동화가 정상 작동할 때 사용하세요.")
            df = create_demo_data()
        
        if df is not None and not df.empty:
            # 파일명 생성
            current_date = datetime.now().strftime('%Y%m%d')
            filename = f'{OUTPUT_DIR}/입찰공고_{current_date}.csv'
            
            # CSV 파일로 저장
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"\n수집 완료!")
            print(f"파일 저장: {filename}")
            
            # 통계 출력
            print_stats(df)
            
            # 로컬 실행 안내
            print("=" * 60)
            print("로컬 PC 실행 방법:")
            print("1. Python 3.8+ 설치")
            print("2. pip install selenium webdriver-manager pandas requests")
            print("3. Chrome 브라우저 설치")
            print("4. python main.py")
            print("5. output 폴더에서 CSV 파일 확인")
            print("\n참고: 브라우저 자동화는 실제 브라우저를 사용하여")
            print("G2B 사이트의 403 오류를 우회할 수 있습니다.")
            
        else:
            print("데이터를 생성할 수 없습니다.")
            
    except Exception as e:
        print(f"시스템 실행 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
