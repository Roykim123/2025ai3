#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2B 공공데이터 API 버전
조달청 나라장터 입찰공고정보서비스 API 활용

공공데이터포털에서 API 키를 발급받아 사용하는 버전
https://www.data.go.kr/data/15129394/openapi.do
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import xml.etree.ElementTree as ET

# Configuration
SEARCH_DAYS = 7
OUTPUT_DIR = "output"
API_BASE_URL = "http://apis.data.go.kr/1230000/BidPublicInfoService01"
API_OPERATION = "getBidPblancListInfoServcPPSSrch"

def get_api_key():
    """API 키 확인 또는 사용자 입력"""
    api_key = os.getenv('G2B_API_KEY')
    if not api_key:
        print("🔑 G2B API 키가 필요합니다.")
        print("1. 공공데이터포털(https://www.data.go.kr/data/15129394/openapi.do)에서 API 신청")
        print("2. 발급받은 인증키를 환경변수 G2B_API_KEY에 설정")
        print("3. 또는 아래에 직접 입력하세요:")
        api_key = input("API 키 입력: ").strip()
        if not api_key:
            print("❌ API 키가 필요합니다.")
            return None
    return api_key

def collect_bids_via_api() -> Optional[pd.DataFrame]:
    """공공데이터 API를 통한 입찰공고 수집"""
    print("🌐 공공데이터 API를 통한 입찰공고 수집...")
    
    api_key = get_api_key()
    if not api_key:
        return None
    
    try:
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=SEARCH_DAYS)
        
        # API 요청 파라미터
        params = {
            'serviceKey': api_key,
            'numOfRows': '100',  # 한 페이지 결과 수
            'pageNo': '1',       # 페이지 번호
            'inqryDiv': '1',     # 조회구분: 1-공고게시일
            'inqryBgnDt': start_date.strftime('%Y%m%d'),
            'inqryEndDt': end_date.strftime('%Y%m%d'),
            'type': 'xml'        # 응답 형식
        }
        
        print(f"📅 검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        print("🔍 API 요청 중...")
        
        # API 호출
        url = f"{API_BASE_URL}/{API_OPERATION}"
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API 요청 실패: HTTP {response.status_code}")
            print(f"응답: {response.text[:500]}")
            return None
        
        # XML 응답 파싱
        root = ET.fromstring(response.content)
        
        # 응답 상태 확인
        result_code = root.find('.//resultCode')
        result_msg = root.find('.//resultMsg')
        
        if result_code is not None and result_code.text != '00':
            print(f"❌ API 오류: {result_msg.text if result_msg is not None else 'Unknown error'}")
            return None
        
        # 데이터 항목 추출
        items = root.findall('.//item')
        print(f"📋 {len(items)}건의 입찰공고를 수신했습니다.")
        
        if not items:
            print("❌ 수집된 입찰공고가 없습니다.")
            return None
        
        # 데이터 파싱
        bid_data = []
        excluded_count = 0
        
        for item in items:
            try:
                # XML 요소에서 텍스트 추출
                def get_text(element_name):
                    elem = item.find(element_name)
                    return elem.text.strip() if elem is not None and elem.text else '정보없음'
                
                # 수의계약 필터링
                contract_method = get_text('cntrctMthd')
                if '수의계약' in contract_method:
                    excluded_count += 1
                    continue
                
                # 데이터 구조화
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
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                bid_data.append(bid_info)
                
            except Exception as e:
                print(f"⚠️ 데이터 파싱 오류: {str(e)}")
                continue
        
        print(f"✅ 수의계약 {excluded_count}건 제외")
        print(f"✅ 최종 {len(bid_data)}건 수집 완료")
        
        if not bid_data:
            return None
        
        # DataFrame 생성
        df = pd.DataFrame(bid_data)
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {str(e)}")
        return None
    except ET.ParseError as e:
        print(f"❌ XML 파싱 오류: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return None

def create_demo_data():
    """데모 데이터 생성"""
    sample_data = [
        {
            '공고명': '[API데모] 인공지능 기반 음성인식 시스템 구축',
            '공고번호': '20250704-API-001',
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
            '공고링크': 'https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo=20250704-API-001',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            '공고명': '[API데모] 청사 보안시스템 유지보수',
            '공고번호': '20250704-API-002',
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
            '공고링크': 'https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo=20250704-API-002',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    return pd.DataFrame(sample_data)

def print_stats(df: pd.DataFrame):
    """수집 통계 출력"""
    print("\n" + "=" * 50)
    print("📊 수집 통계")
    print("=" * 50)
    print(f"총 수집 건수: {len(df)}건")
    
    if '계약방법' in df.columns:
        contract_stats = df['계약방법'].value_counts()
        print("\n계약방법별 분포:")
        for method, count in contract_stats.items():
            print(f"  - {method}: {count}건")
    
    if '공고기관' in df.columns:
        agency_stats = df['공고기관'].value_counts().head(5)
        print("\n주요 공고기관 (상위 5개):")
        for agency, count in agency_stats.items():
            print(f"  - {agency}: {count}건")
    
    print("=" * 50)

def main():
    """메인 실행 함수"""
    print("🏛️ G2B 조달청 입찰공고 자동수집 시스템 (공공데이터 API)")
    print("=" * 70)
    
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # API를 통한 입찰공고 수집
        print("🚀 공공데이터 API를 사용하여 데이터를 수집합니다...")
        df = collect_bids_via_api()
        
        # API 실패 시 데모 데이터 사용
        if df is None or df.empty:
            print("\n⚠️ API 수집이 실패했습니다. 데모 데이터를 생성합니다.")
            print("💡 실제 사용 시 공공데이터포털에서 API 키를 발급받으세요.")
            df = create_demo_data()
        
        if df is not None and not df.empty:
            # 파일명 생성
            current_date = datetime.now().strftime('%Y%m%d')
            filename = f'{OUTPUT_DIR}/입찰공고_API_{current_date}.csv'
            
            # CSV 파일로 저장
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"\n✅ 수집 완료!")
            print(f"💾 파일 저장: {filename}")
            
            # 통계 출력
            print_stats(df)
            
            # API 사용 안내
            print("\n" + "=" * 70)
            print("🔑 공공데이터 API 사용 방법:")
            print("1. 공공데이터포털 접속: https://www.data.go.kr/data/15129394/openapi.do")
            print("2. '조달청_나라장터 입찰공고정보서비스' 활용신청")
            print("3. 발급받은 인증키를 환경변수 G2B_API_KEY에 설정")
            print("4. python g2b_api_version.py 실행")
            print("\n💡 장점:")
            print("• 공식 API로 안정적인 데이터 수집")
            print("• 403 오류 없이 대량 데이터 처리 가능")
            print("• 다양한 검색 조건 지원")
            print("• XML/JSON 형식으로 구조화된 데이터 제공")
            
        else:
            print("❌ 데이터를 생성할 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 시스템 실행 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()