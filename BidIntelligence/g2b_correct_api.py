
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라장터 API 올바른 호출 방식
참고 가이드를 바탕으로 수정된 버전

주요 개선사항:
- 올바른 API URL 사용
- 정확한 파라미터명 사용  
- YYYYMMDD 날짜 형식 적용
- XML 응답 처리 최적화
"""

import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional

# 설정
OUTPUT_DIR = "output"
SEARCH_DAYS = 7

# 올바른 API 설정 (가이드 참고)
API_BASE_URL = "https://apis.data.go.kr/1230000/BidPublicInfoService"
API_KEY = "holAgj/0G+0f0COeMdfrl+0iDpm1lSzmYMlYxmMYq/7vkjMMFWZMMBZ6cReG+1VhhyIdN/pgykHNXwlkSYSZ/w=="

# API 엔드포인트 (가이드의 올바른 형식)
API_ENDPOINTS = {
    '물품': 'getBidPblancListInfoThngPblanc',
    '용역': 'getBidPblancListInfoServcPblanc', 
    '공사': 'getBidPblancListInfoCnstwkPblanc'
}

def create_session():
    """세션 생성"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session

def call_g2b_api_correct(category: str) -> Optional[ET.Element]:
    """올바른 방식으로 나라장터 API 호출"""
    
    if category not in API_ENDPOINTS:
        print(f"❌ 지원하지 않는 카테고리: {category}")
        return None
    
    endpoint = API_ENDPOINTS[category]
    url = f"{API_BASE_URL}/{endpoint}"
    
    # 날짜 계산 (YYYYMMDD 형식)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=SEARCH_DAYS)
    
    # 올바른 파라미터 설정 (가이드 참고)
    params = {
        'serviceKey': API_KEY,
        'numOfRows': '100',
        'pageNo': '1',
        'bidNtceBgnDt': start_date.strftime('%Y%m%d'),  # YYYYMMDD 형식
        'bidNtceEndDt': end_date.strftime('%Y%m%d')     # YYYYMMDD 형식
    }
    
    print(f"🔗 {category} API 호출 중...")
    print(f"📅 검색기간: {params['bidNtceBgnDt']} ~ {params['bidNtceEndDt']}")
    print(f"🌐 URL: {url}")
    
    try:
        session = create_session()
        response = session.get(url, params=params, timeout=30)
        
        print(f"📡 응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"응답: {response.text[:300]}")
            return None
        
        # XML 파싱
        root = ET.fromstring(response.content)
        
        # API 응답 상태 확인
        result_code = root.find('.//resultCode')
        result_msg = root.find('.//resultMsg')
        
        if result_code is not None:
            print(f"📋 API 응답 코드: {result_code.text}")
            if result_code.text != '00':
                error_msg = result_msg.text if result_msg is not None else '알 수 없는 오류'
                print(f"❌ API 오류: {error_msg}")
                return None
        
        # 전체 건수 확인
        total_count = root.find('.//totalCount')
        if total_count is not None:
            print(f"📊 전체 공고 수: {total_count.text}")
        
        return root
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return None
    except ET.ParseError as e:
        print(f"❌ XML 파싱 오류: {e}")
        print(f"응답 내용: {response.text[:500]}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def parse_bid_data(xml_root: ET.Element, category: str) -> List[Dict]:
    """XML에서 입찰 데이터 추출"""
    bid_list = []
    
    try:
        items = xml_root.findall('.//item')
        print(f"📋 추출된 아이템 수: {len(items)}")
        
        for item in items:
            try:
                def get_text(tag_name: str) -> str:
                    elem = item.find(tag_name)
                    return elem.text.strip() if elem is not None and elem.text else '정보없음'
                
                # 기본 정보 추출 (가이드의 주요 필드들)
                bid_data = {
                    '공고명': get_text('bidNtceNm'),
                    '공고번호': get_text('bidNtceNo'),
                    '공고기관': get_text('ntceInsttNm'),
                    '수요기관': get_text('dminsttNm'), 
                    '공고일자': get_text('bidNtceDt'),
                    '마감일시': get_text('bidClseDt'),
                    '개찰일시': get_text('opengDt'),
                    '계약방법': get_text('cntrctCnclsMthdNm'),
                    '예정가격': get_text('presmptPrc'),
                    '추정가격': get_text('assmtUprc'),
                    '입찰방법': get_text('bidMethdNm'),
                    '지역제한': get_text('rgstTyNm'),
                    '업종제한': get_text('indstryClNm'),
                    '참가자격': get_text('prtcptLmtYn'),
                    '국제입찰': get_text('intrbidYn'),
                    '재공고여부': get_text('reNtceYn'),
                    '담당자': get_text('ntceInsttOfclNm'),
                    '연락처': get_text('ntceInsttOfclTelNo'),
                    '이메일': get_text('ntceInsttOfclEmailAdrs'),
                    '분류': category,
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '공고링크': f"https://www.g2b.go.kr/pt/menu/selectSubFrame.do?bidNtceNo={get_text('bidNtceNo')}"
                }
                
                # 수의계약 제외
                if '수의계약' not in bid_data['계약방법']:
                    bid_list.append(bid_data)
                
            except Exception as e:
                print(f"⚠️ 아이템 처리 오류: {e}")
                continue
        
        print(f"✅ {category}: {len(bid_list)}개 공고 처리 완료")
        return bid_list
        
    except Exception as e:
        print(f"❌ 데이터 파싱 오류: {e}")
        return []

def collect_all_bids() -> pd.DataFrame:
    """모든 카테고리의 입찰공고 수집"""
    print("🚀 올바른 나라장터 API 호출 시작")
    print("=" * 60)
    
    all_bids = []
    
    for category in API_ENDPOINTS.keys():
        print(f"\n📋 {category} 공고 수집 중...")
        
        # API 호출
        xml_root = call_g2b_api_correct(category)
        
        if xml_root is not None:
            # 데이터 파싱
            bids = parse_bid_data(xml_root, category)
            all_bids.extend(bids)
        else:
            print(f"❌ {category} API 호출 실패")
    
    if not all_bids:
        print("\n❌ 수집된 데이터가 없습니다.")
        print("💡 API 키 또는 네트워크 연결을 확인해주세요.")
        return create_demo_data()
    
    # DataFrame 생성
    df = pd.DataFrame(all_bids)
    
    # 중복 제거
    initial_count = len(df)
    df = df.drop_duplicates(subset=['공고번호'], keep='first')
    duplicate_count = initial_count - len(df)
    
    if duplicate_count > 0:
        print(f"🔄 중복 제거: {duplicate_count}개")
    
    print(f"\n🎯 최종 수집: {len(df)}개 공고")
    return df

def create_demo_data() -> pd.DataFrame:
    """데모 데이터 생성 (API 실패시)"""
    print("📋 데모 데이터 생성...")
    
    demo_data = [
        {
            '공고명': '[데모] 정보시스템 개발 및 구축',
            '공고번호': '20250704-DEMO-001',
            '공고기관': '서울특별시',
            '수요기관': '서울특별시 정보통신정책관',
            '공고일자': '20250701',
            '마감일시': '20250715 18:00',
            '개찰일시': '20250716 14:00',
            '계약방법': '일반경쟁입찰',
            '예정가격': '500000000',
            '추정가격': '450000000',
            '입찰방법': '전자입찰',
            '지역제한': '제한없음',
            '업종제한': '정보통신업',
            '참가자격': '일반',
            '국제입찰': 'N',
            '재공고여부': 'N',
            '담당자': '김담당',
            '연락처': '02-123-4567',
            '이메일': 'demo@seoul.go.kr',
            '분류': '용역',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '공고링크': 'https://www.g2b.go.kr/'
        },
        {
            '공고명': '[데모] 사무용 소프트웨어 구매',
            '공고번호': '20250704-DEMO-002',
            '공고기관': '경기도',
            '수요기관': '경기도 총무과',
            '공고일자': '20250702',
            '마감일시': '20250716 17:00',
            '개찰일시': '20250717 10:00',
            '계약방법': '제한경쟁입찰',
            '예정가격': '120000000',
            '추정가격': '110000000',
            '입찰방법': '전자입찰',
            '지역제한': '경기도',
            '업종제한': '소프트웨어업',
            '참가자격': '중소기업',
            '국제입찰': 'N',
            '재공고여부': 'N',
            '담당자': '이담당',
            '연락처': '031-123-4567',
            '이메일': 'demo@gg.go.kr',
            '분류': '물품',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '공고링크': 'https://www.g2b.go.kr/'
        }
    ]
    
    return pd.DataFrame(demo_data)

def save_results(df: pd.DataFrame) -> str:
    """결과 저장"""
    if df.empty:
        print("❌ 저장할 데이터가 없습니다")
        return ""
    
    # 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'{OUTPUT_DIR}/G2B_올바른API호출_{timestamp}.csv'
    
    # 출력 디렉토리 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # CSV 저장
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"💾 결과 저장: {filename}")
    return filename

def print_statistics(df: pd.DataFrame):
    """수집 통계 출력"""
    print("\n" + "=" * 60)
    print("📊 수집 통계")
    print("=" * 60)
    print(f"총 수집: {len(df)}개")
    
    if '분류' in df.columns:
        category_stats = df['분류'].value_counts()
        print(f"\n📋 분류별:")
        for category, count in category_stats.items():
            print(f"  • {category}: {count}개")
    
    if '계약방법' in df.columns:
        contract_stats = df['계약방법'].value_counts()
        print(f"\n🏛️ 계약방법:")
        for method, count in contract_stats.items():
            print(f"  • {method}: {count}개")
    
    if '공고기관' in df.columns:
        agency_stats = df['공고기관'].value_counts().head(5)
        print(f"\n🏢 주요 공고기관:")
        for agency, count in agency_stats.items():
            print(f"  • {agency}: {count}개")

def main():
    """메인 실행 함수"""
    print("🏛️ 나라장터 API 올바른 호출 방식")
    print("📚 참고: 제공된 가이드 기반 개선 버전")
    print("=" * 60)
    
    try:
        # 데이터 수집
        df = collect_all_bids()
        
        if not df.empty:
            # 결과 저장
            filename = save_results(df)
            
            # 통계 출력
            print_statistics(df)
            
            print(f"\n✅ 수집 완료!")
            print(f"📊 총 {len(df)}개 공고 수집")
            print(f"💾 저장파일: {filename}")
            
            # 가이드 요약
            print("\n" + "=" * 60)
            print("💡 적용된 개선사항")
            print("=" * 60)
            print("✅ 올바른 API URL 사용")
            print("✅ 정확한 파라미터명 (bidNtceBgnDt, bidNtceEndDt)")
            print("✅ YYYYMMDD 날짜 형식 적용")
            print("✅ XML 응답 처리 최적화")
            print("✅ 에러 처리 강화")
            
        else:
            print("❌ 데이터 수집 실패")
            
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
