
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나라장터 API 테스트 URL 생성기
브라우저에서 직접 확인할 수 있는 URL을 생성합니다.
"""

from datetime import datetime, timedelta
import urllib.parse

# API 설정
API_BASE_URL = "https://apis.data.go.kr/1230000/BidPublicInfoService"
API_KEY = "holAgj/0G+0f0COeMdfrl+0iDpm1lSzmYMlYxmMYq/7vkjMMFWZMMBZ6cReG+1VhhyIdN/pgykHNXwlkSYSZ/w=="

# API 엔드포인트
API_ENDPOINTS = {
    '물품': 'getBidPblancListInfoThngPblanc',
    '용역': 'getBidPblancListInfoServcPblanc', 
    '공사': 'getBidPblancListInfoCnstwkPblanc'
}

def generate_test_urls():
    """테스트용 API URL 생성"""
    print("🔗 나라장터 API 테스트 URL 생성")
    print("=" * 60)
    
    # 날짜 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    print(f"📅 검색 기간: {start_date_str} ~ {end_date_str}")
    print()
    
    for category, endpoint in API_ENDPOINTS.items():
        print(f"📋 {category} 공고 API 테스트 URL:")
        
        # 파라미터 구성
        params = {
            'serviceKey': API_KEY,
            'numOfRows': '5',
            'pageNo': '1',
            'bidNtceBgnDt': start_date_str,
            'bidNtceEndDt': end_date_str
        }
        
        # URL 생성
        base_url = f"{API_BASE_URL}/{endpoint}"
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        full_url = f"{base_url}?{query_string}"
        
        print(f"🌐 {full_url}")
        print()
        
        # curl 명령어도 제공
        print(f"💻 curl 테스트:")
        print(f'curl "{full_url}"')
        print()
        print("-" * 60)

def main():
    generate_test_urls()
    
    print("\n💡 사용 방법:")
    print("1. 위의 URL을 복사해서 크롬 브라우저 주소창에 붙여넣기")
    print("2. XML 응답이 나오면 API가 정상 작동하는 것")
    print("3. 오류가 나오면 API 키나 파라미터 확인 필요")
    print("\n🔧 문제 해결:")
    print("- 'SERVICE_KEY_IS_NOT_REGISTERED_ERROR': API 키 문제")
    print("- 'INVALID_REQUEST_PARAMETER_ERROR': 파라미터 문제")
    print("- 'NORMAL_SERVICE': 정상 응답")

if __name__ == "__main__":
    main()
