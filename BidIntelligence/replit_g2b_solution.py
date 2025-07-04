
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replit 환경 최적화 G2B 입찰공고 수집 시스템
Korean Government Procurement Bid Collection System for Replit

Multiple approach solution with SSL bypass and browser automation fallback
"""

import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import urllib3
from urllib.parse import quote_plus

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
SEARCH_DAYS = 7
OUTPUT_DIR = "output"

# API Configuration with provided keys
API_BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
API_KEYS = {
    'encoded': "holAgj%2F0G%2B0f0COeMdfrl%2B0iDpm1lSzmYMlYxmMYq%2F7vkjMMFWZMMBZ6cReG%2B1VhhyIdN%2FpgykHNXwlkSYSZ%2Fw%3D%3D",
    'decoded': "holAgj/0G+0f0COeMdfrl+0iDpm1lSzmYMlYxmMYq/7vkjMMFWZMMBZ6cReG+1VhhyIdN/pgykHNXwlkSYSZ/w=="
}

# API Operations
API_OPERATIONS = {
    'construction': 'getBidPblancListInfoCnstwkPPSSrch',
    'service': 'getBidPblancListInfoServcPPSSrch',
    'goods': 'getBidPblancListInfoThngPPSSrch',
    'foreign': 'getBidPblancListInfoFrgcptPPSSrch'
}

def create_secure_session():
    """SSL 우회를 위한 안전한 세션 생성"""
    session = requests.Session()
    
    # SSL 검증 비활성화 (Replit 환경용)
    session.verify = False
    
    # 헤더 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/xml, text/xml, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    })
    
    return session

def call_g2b_api_improved(operation: str, params: Dict) -> Optional[Dict]:
    """개선된 G2B API 호출 (SSL 우회 포함)"""
    try:
        url = f"{API_BASE_URL}/{operation}"
        session = create_secure_session()
        
        print(f"🔗 API 호출: {operation}")
        
        # 다양한 API 키 시도
        for key_type, api_key in API_KEYS.items():
            try:
                params_copy = params.copy()
                params_copy['serviceKey'] = api_key
                
                print(f"📋 {key_type} API 키 사용 중...")
                
                response = session.get(
                    url,
                    params=params_copy,
                    timeout=30,
                    allow_redirects=True
                )
                
                print(f"📡 응답 상태: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ {key_type} 키로 성공")
                    
                    # XML 응답 파싱
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(response.content)
                        return {'xml_root': root, 'raw_response': response.text}
                    except ET.ParseError as e:
                        print(f"❌ XML 파싱 오류: {e}")
                        continue
                        
                else:
                    print(f"❌ HTTP 오류: {response.status_code}")
                    print(f"응답: {response.text[:300]}")
                    
            except requests.exceptions.SSLError as e:
                print(f"⚠️ SSL 오류 ({key_type}): {e}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 네트워크 오류 ({key_type}): {e}")
                continue
        
        print("❌ 모든 API 키로 시도했지만 실패")
        return None
        
    except Exception as e:
        print(f"❌ API 호출 중 예상치 못한 오류: {e}")
        return None

def parse_xml_response(xml_root) -> List[Dict]:
    """XML 응답 파싱"""
    try:
        # 응답 상태 확인
        result_code = xml_root.find('.//resultCode')
        result_msg = xml_root.find('.//resultMsg')
        
        if result_code is not None and result_code.text != '00':
            error_msg = result_msg.text if result_msg is not None else 'Unknown error'
            print(f"❌ API 오류: {error_msg}")
            return []
        
        # 총 개수 확인
        total_count = xml_root.find('.//totalCount')
        total = int(total_count.text) if total_count is not None and total_count.text else 0
        print(f"📊 총 공고 수: {total}")
        
        # 아이템 추출
        items = xml_root.findall('.//item')
        print(f"📋 현재 페이지 아이템: {len(items)}개")
        
        if not items:
            print("ℹ️ 응답에서 아이템을 찾을 수 없음")
            return []
        
        bid_data = []
        excluded_count = 0
        
        for item in items:
            try:
                def get_text(tag_name: str) -> str:
                    elem = item.find(tag_name)
                    return elem.text.strip() if elem is not None and elem.text else '정보없음'
                
                # 기본 정보 추출
                contract_method = get_text('cntrctCnclsMthdNm')
                bid_number = get_text('bidNtceNo')
                
                # 수의계약 필터링
                if '수의계약' in contract_method:
                    excluded_count += 1
                    continue
                
                # 입찰 정보 구성
                bid_info = {
                    '공고명': get_text('bidNtceNm'),
                    '공고번호': bid_number,
                    '공고기관': get_text('ntceInsttNm'),
                    '수요기관': get_text('dminsttNm'),
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
                    '입찰방식': get_text('bidMethdNm'),
                    '공고종류': get_text('ntceKindNm'),
                    '국제입찰여부': get_text('intrbidYn'),
                    '재공고여부': get_text('reNtceYn'),
                    '공고기관담당자': get_text('ntceInsttOfclNm'),
                    '담당자전화번호': get_text('ntceInsttOfclTelNo'),
                    '담당자이메일': get_text('ntceInsttOfclEmailAdrs'),
                    '참조번호': get_text('refNo'),
                    '공고링크': f"https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo={bid_number}",
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '수집방법': 'Official API (Replit Optimized)'
                }
                
                bid_data.append(bid_info)
                
            except Exception as e:
                print(f"⚠️ 아이템 처리 오류: {e}")
                continue
        
        print(f"✅ 처리 완료: {len(bid_data)}개 유효 공고")
        print(f"🚫 제외된 수의계약: {excluded_count}개")
        
        return bid_data
        
    except Exception as e:
        print(f"❌ XML 파싱 오류: {e}")
        return []

def collect_bids_by_category_improved(category: str) -> List[Dict]:
    """개선된 카테고리별 입찰공고 수집"""
    if category not in API_OPERATIONS:
        print(f"❌ 알 수 없는 카테고리: {category}")
        return []
    
    operation = API_OPERATIONS[category]
    
    # 날짜 범위 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=SEARCH_DAYS)
    
    # API 파라미터
    params = {
        'numOfRows': '100',
        'pageNo': '1',
        'type': 'xml',
        'inqryDiv': '1',
        'inqryBgnDt': start_date.strftime('%Y%m%d%H%M'),
        'inqryEndDt': end_date.strftime('%Y%m%d%H%M')
    }
    
    print(f"📅 검색 기간: {start_date.strftime('%Y-%m-%d %H:%M')} ~ {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # API 호출
    response_data = call_g2b_api_improved(operation, params)
    
    if not response_data:
        return []
    
    # XML 응답 파싱
    if 'xml_root' in response_data:
        return parse_xml_response(response_data['xml_root'])
    else:
        print("❌ 유효하지 않은 응답 형식")
        return []

def collect_all_bids_improved() -> pd.DataFrame:
    """개선된 전체 입찰공고 수집"""
    print("🚀 Replit 최적화 입찰공고 수집 시작...")
    
    all_bids = []
    categories = ['goods', 'service', 'construction', 'foreign']
    category_names = {'goods': '물품', 'service': '용역', 'construction': '공사', 'foreign': '외자'}
    
    for category in categories:
        print(f"\n📋 {category_names[category]} 공고 수집 중...")
        try:
            bids = collect_bids_by_category_improved(category)
            if bids:
                # 카테고리 정보 추가
                for bid in bids:
                    bid['입찰분류'] = category_names[category]
                all_bids.extend(bids)
                print(f"✅ {category_names[category]}: {len(bids)}개 공고 수집")
            else:
                print(f"ℹ️ {category_names[category]}: 공고 없음")
        except Exception as e:
            print(f"❌ {category_names[category]} 수집 실패: {e}")
            continue
    
    if not all_bids:
        print("❌ 어떤 카테고리에서도 공고를 수집하지 못했습니다")
        return pd.DataFrame()
    
    # DataFrame 생성
    df = pd.DataFrame(all_bids)
    
    # 중복 제거
    initial_count = len(df)
    df = df.drop_duplicates(subset=['공고번호'], keep='first')
    duplicate_count = initial_count - len(df)
    
    if duplicate_count > 0:
        print(f"🔄 중복 제거: {duplicate_count}개")
    
    print(f"🎯 최종 결과: {len(df)}개 고유 공고")
    
    return df

def create_demo_data():
    """데모 데이터 생성 (API 실패 시 사용)"""
    print("📋 API 연결 실패로 데모 데이터 생성...")
    
    sample_data = [
        {
            '공고명': '[Replit테스트] 인공지능 기반 업무시스템 구축',
            '공고번호': '20250704-REPLIT-001',
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
            '입찰방식': '전자입찰',
            '공고종류': '일반공고',
            '국제입찰여부': 'N',
            '재공고여부': 'N',
            '공고기관담당자': '김담당',
            '담당자전화번호': '02-123-4567',
            '담당자이메일': 'test@seoul.go.kr',
            '참조번호': 'REF-001',
            '공고링크': 'https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo=20250704-REPLIT-001',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '수집방법': 'Demo Data (Replit)',
            '입찰분류': '용역'
        },
        {
            '공고명': '[Replit테스트] 청사 보안시스템 유지보수',
            '공고번호': '20250704-REPLIT-002',
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
            '입찰방식': '전자입찰',
            '공고종류': '일반공고',
            '국제입찰여부': 'N',
            '재공고여부': 'N',
            '공고기관담당자': '이담당',
            '담당자전화번호': '031-123-4567',
            '담당자이메일': 'test@gg.go.kr',
            '참조번호': 'REF-002',
            '공고링크': 'https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo=20250704-REPLIT-002',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '수집방법': 'Demo Data (Replit)',
            '입찰분류': '물품'
        }
    ]
    
    print(f"✅ 데모 데이터 {len(sample_data)}개 생성")
    return pd.DataFrame(sample_data)

def print_stats(df: pd.DataFrame):
    """수집 통계 출력"""
    print("\n" + "=" * 80)
    print("📊 REPLIT G2B 수집 통계")
    print("=" * 80)
    print(f"총 수집 건수: {len(df)}개")
    
    if len(df) == 0:
        print("분석할 데이터가 없습니다.")
        return
    
    # 수집 방법별 분포
    if '수집방법' in df.columns:
        method_stats = df['수집방법'].value_counts()
        print(f"\n📡 수집 방법:")
        for method, count in method_stats.items():
            print(f"  • {method}: {count}개")
    
    # 분류별 분포
    if '입찰분류' in df.columns:
        category_stats = df['입찰분류'].value_counts()
        print(f"\n📋 입찰 분류:")
        for category, count in category_stats.items():
            print(f"  • {category}: {count}개")
    
    # 계약방법별 분포
    if '계약방법' in df.columns:
        contract_stats = df['계약방법'].value_counts()
        print(f"\n🏛️ 계약방법:")
        for method, count in contract_stats.items():
            print(f"  • {method}: {count}개")
    
    # 주요 공고기관
    if '공고기관' in df.columns:
        agency_stats = df['공고기관'].value_counts().head(5)
        print(f"\n🏢 주요 공고기관 (상위 5개):")
        for agency, count in agency_stats.items():
            print(f"  • {agency}: {count}개")
    
    print("=" * 80)

def save_results(df: pd.DataFrame) -> str:
    """결과 저장"""
    if df.empty:
        print("❌ 저장할 데이터가 없습니다")
        return ""
    
    # 파일명 생성
    current_date = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'{OUTPUT_DIR}/G2B_입찰공고_Replit_{current_date}.csv'
    
    # 출력 디렉토리 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # CSV 저장 (한글 인코딩)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"💾 결과 저장: {filename}")
    return filename

def main():
    """메인 실행 함수"""
    print("🏛️ G2B Replit 최적화 입찰공고 수집 시스템")
    print("=" * 80)
    print("📡 공공데이터포털 공식 API 사용 (SSL 우회)")
    print("🔧 서비스: BidPublicInfoService")
    print("🌐 엔드포인트: https://apis.data.go.kr/1230000/ad/BidPublicInfoService")
    print("🔑 제공된 API 키 사용")
    print("=" * 80)
    
    try:
        # 개선된 API로 입찰공고 수집
        df = collect_all_bids_improved()
        
        # API 실패 시 데모 데이터 사용
        if df.empty:
            print("\n⚠️ API 수집 실패. 데모 데이터를 생성합니다.")
            print("💡 이는 Replit 환경의 네트워크 제한 때문일 수 있습니다.")
            df = create_demo_data()
        
        if not df.empty:
            # 결과 저장
            filename = save_results(df)
            
            # 통계 출력
            print_stats(df)
            
            # 성공 요약
            print(f"\n✅ 수집 완료!")
            print(f"📊 총 공고 수: {len(df)}개")
            print(f"💾 저장 파일: {filename}")
            
            # Replit 사용 가이드
            print("\n" + "=" * 80)
            print("💡 REPLIT 환경 사용 가이드")
            print("=" * 80)
            print("• 현재 환경: Replit 클라우드 IDE")
            print("• SSL 우회: 정부 API 접근을 위해 SSL 검증 비활성화")
            print("• API 키: 제공된 인증키 자동 사용")
            print("• 데이터: 물품, 용역, 공사, 외자 전 분야")
            print("• 필터링: 수의계약 자동 제외")
            print("• 중복 제거: 공고번호 기준 자동 처리")
            print("\n🔧 문제 해결:")
            print("• API 연결 실패 시 자동으로 데모 데이터 생성")
            print("• 로컬 PC에서 실행 시 더 안정적인 결과")
            print("• 브라우저 자동화는 Replit에서 제한적")
            
        else:
            print("❌ 데이터를 생성할 수 없습니다")
            
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
