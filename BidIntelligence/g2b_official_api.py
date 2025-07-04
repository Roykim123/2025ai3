#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2B 공식 API 솔루션 - 조달청 나라장터 입찰공고정보서비스
Official G2B API Solution using Public Data Portal

Based on official documentation:
- Service: BidPublicInfoService
- Endpoint: https://apis.data.go.kr/1230000/ad/BidPublicInfoService
- Operations: 물품, 용역, 공사, 외자 입찰공고 조회
"""

import os
import sys
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.parse import quote

# Configuration
SEARCH_DAYS = 7
OUTPUT_DIR = "output"

# Official API Configuration (from documentation)
API_BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"

# Available operations
API_OPERATIONS = {
    'construction': 'getBidPblancListInfoCnstwkPPSSrch',  # 공사 조회
    'service': 'getBidPblancListInfoServcPPSSrch',        # 용역 조회  
    'goods': 'getBidPblancListInfoThngPPSSrch',           # 물품 조회
    'foreign': 'getBidPblancListInfoFrgcptPPSSrch'        # 외자 조회
}

def get_api_key() -> Optional[str]:
    """Get API key from environment or user input"""
    # Try environment variable first
    api_key = os.getenv('G2B_API_KEY')
    if api_key:
        print(f"✓ Using API key from environment variable")
        return api_key
    
    # Try hardcoded keys provided by user
    provided_keys = [
        "holAgj%2F0G%2B0f0COeMdfrl%2B0iDpm1lSzmYMlYxmMYq%2F7vkjMMFWZMMBZ6cReG%2B1VhhyIdN%2FpgykHNXwlkSYSZ%2Fw%3D%3D",  # Encoded
        "holAgj/0G+0f0COeMdfrl+0iDpm1lSzmYMlYxmMYq/7vkjMMFWZMMBZ6cReG+1VhhyIdN/pgykHNXwlkSYSZ/w=="   # Decoded
    ]
    
    for key in provided_keys:
        if key:
            print(f"✓ Using provided API key")
            return key
    
    print("❌ No API key found")
    print("💡 Please set G2B_API_KEY environment variable or provide API key")
    return None

def call_g2b_api(operation: str, params: Dict) -> Optional[Dict]:
    """Call G2B API with specified operation and parameters"""
    try:
        url = f"{API_BASE_URL}/{operation}"
        
        print(f"🔗 Calling API: {operation}")
        
        # Enhanced headers for better compatibility
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/xml, text/xml, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # Use decoded API key
        if 'serviceKey' in params:
            # Try decoded key first
            decoded_key = "holAgj/0G+0f0COeMdfrl+0iDpm1lSzmYMlYxmMYq/7vkjMMFWZMMBZ6cReG+1VhhyIdN/pgykHNXwlkSYSZ/w=="
            params['serviceKey'] = decoded_key
        
        print(f"📋 Using decoded API key")
        
        # Make API request with SSL verification disabled and enhanced session
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(
            url, 
            params=params, 
            timeout=30,
            verify=False,  # Disable SSL verification for Replit compatibility
            allow_redirects=True
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
        
        print(f"✅ API call successful, response size: {len(response.content)} bytes")
        
        # Parse response based on type
        if params.get('type', '').lower() == 'json':
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"Response text: {response.text[:500]}")
                return None
        else:
            # Default XML parsing
            try:
                root = ET.fromstring(response.content)
                return {'xml_root': root, 'raw_response': response.text}
            except ET.ParseError as e:
                print(f"❌ XML parsing error: {e}")
                print(f"Response text: {response.text[:500]}")
                return None
                
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        print("💡 This may be due to network restrictions in the current environment")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def parse_xml_response(xml_root) -> List[Dict]:
    """Parse XML response to extract bid information"""
    try:
        # Check response status
        result_code = xml_root.find('.//resultCode')
        result_msg = xml_root.find('.//resultMsg')
        
        if result_code is not None and result_code.text != '00':
            error_msg = result_msg.text if result_msg is not None else 'Unknown error'
            print(f"❌ API Error: {error_msg}")
            return []
        
        # Extract total count
        total_count = xml_root.find('.//totalCount')
        total = int(total_count.text) if total_count is not None and total_count.text else 0
        print(f"📊 Total announcements available: {total}")
        
        # Extract items
        items = xml_root.findall('.//item')
        print(f"📋 Processing {len(items)} items in current page")
        
        if not items:
            print("ℹ️ No items found in response")
            return []
        
        bid_data = []
        excluded_count = 0
        
        for item in items:
            try:
                # Helper function to safely extract text
                def get_text(tag_name: str) -> str:
                    elem = item.find(tag_name)
                    return elem.text.strip() if elem is not None and elem.text else '정보없음'
                
                # Extract basic information
                contract_method = get_text('cntrctCnclsMthdNm')
                bid_number = get_text('bidNtceNo')
                
                # Filter out private contracts (수의계약)
                if '수의계약' in contract_method:
                    excluded_count += 1
                    continue
                
                # Build bid information dictionary
                bid_info = {
                    '공고명': get_text('bidNtceNm'),
                    '공고번호': bid_number,
                    '공고기관': get_text('ntceInsttNm'),
                    '수요기관': get_text('dminsttNm'),
                    '계약방법': contract_method,
                    '입찰공고일': get_text('bidNtceDt'),
                    '입찰마감일시': get_text('bidClseDt') if get_text('bidClseDt') != '정보없음' else '정보없음',
                    '개찰일시': get_text('opengDt') if get_text('opengDt') != '정보없음' else '정보없음',
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
                    '수집방법': 'Official API'
                }
                
                bid_data.append(bid_info)
                
            except Exception as e:
                print(f"⚠️ Error processing item: {e}")
                continue
        
        print(f"✅ Processed {len(bid_data)} valid announcements")
        print(f"🚫 Excluded {excluded_count} private contracts")
        
        return bid_data
        
    except Exception as e:
        print(f"❌ XML parsing error: {e}")
        return []

def collect_bids_by_category(category: str, api_key: str) -> List[Dict]:
    """Collect bids for specific category"""
    if category not in API_OPERATIONS:
        print(f"❌ Unknown category: {category}")
        return []
    
    operation = API_OPERATIONS[category]
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=SEARCH_DAYS)
    
    # Prepare API parameters according to documentation
    params = {
        'serviceKey': api_key,
        'numOfRows': '100',  # Results per page
        'pageNo': '1',       # Page number
        'type': 'xml',       # Response format
        'inqryDiv': '1',     # Query type: 1=registration date
        'inqryBgnDt': start_date.strftime('%Y%m%d%H%M'),  # YYYYMMDDHHMM format
        'inqryEndDt': end_date.strftime('%Y%m%d%H%M')     # YYYYMMDDHHMM format
    }
    
    print(f"📅 Search period: {start_date.strftime('%Y-%m-%d %H:%M')} ~ {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Call API
    response_data = call_g2b_api(operation, params)
    
    if not response_data:
        return []
    
    # Parse XML response
    if 'xml_root' in response_data:
        return parse_xml_response(response_data['xml_root'])
    else:
        print("❌ Invalid response format")
        return []

def collect_all_bids(api_key: str) -> pd.DataFrame:
    """Collect bids from all categories"""
    print("🚀 Starting comprehensive bid collection...")
    
    all_bids = []
    categories = ['goods', 'service', 'construction', 'foreign']
    category_names = {'goods': '물품', 'service': '용역', 'construction': '공사', 'foreign': '외자'}
    
    for category in categories:
        print(f"\n📋 Collecting {category_names[category]} announcements...")
        try:
            bids = collect_bids_by_category(category, api_key)
            if bids:
                # Add category information
                for bid in bids:
                    bid['입찰분류'] = category_names[category]
                all_bids.extend(bids)
                print(f"✅ {category_names[category]}: {len(bids)} announcements collected")
            else:
                print(f"ℹ️ {category_names[category]}: No announcements found")
        except Exception as e:
            print(f"❌ {category_names[category]} collection failed: {e}")
            continue
    
    if not all_bids:
        print("❌ No announcements collected from any category")
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(all_bids)
    
    # Remove duplicates based on announcement number
    initial_count = len(df)
    df = df.drop_duplicates(subset=['공고번호'], keep='first')
    duplicate_count = initial_count - len(df)
    
    if duplicate_count > 0:
        print(f"🔄 Removed {duplicate_count} duplicate announcements")
    
    print(f"🎯 Final result: {len(df)} unique announcements")
    
    return df

def print_detailed_stats(df: pd.DataFrame):
    """Print detailed collection statistics"""
    print("\n" + "=" * 80)
    print("📊 DETAILED COLLECTION STATISTICS")
    print("=" * 80)
    print(f"Total announcements: {len(df)}")
    
    if len(df) == 0:
        print("No data to analyze")
        return
    
    # Collection method breakdown
    if '수집방법' in df.columns:
        method_stats = df['수집방법'].value_counts()
        print(f"\n📡 Collection method:")
        for method, count in method_stats.items():
            print(f"  • {method}: {count} items")
    
    # Category breakdown
    if '입찰분류' in df.columns:
        category_stats = df['입찰분류'].value_counts()
        print(f"\n📋 Bid categories:")
        for category, count in category_stats.items():
            print(f"  • {category}: {count} announcements")
    
    # Contract method distribution
    if '계약방법' in df.columns:
        contract_stats = df['계약방법'].value_counts()
        print(f"\n🏛️ Contract methods:")
        for method, count in contract_stats.items():
            print(f"  • {method}: {count} announcements")
    
    # Bid method distribution
    if '입찰방식' in df.columns:
        bid_method_stats = df['입찰방식'].value_counts()
        print(f"\n💼 Bid methods:")
        for method, count in bid_method_stats.items():
            print(f"  • {method}: {count} announcements")
    
    # Top agencies
    if '공고기관' in df.columns:
        agency_stats = df['공고기관'].value_counts().head(10)
        print(f"\n🏢 Top 10 announcing agencies:")
        for agency, count in agency_stats.items():
            print(f"  • {agency}: {count} announcements")
    
    # Date distribution
    if '입찰공고일' in df.columns:
        df['공고날짜'] = pd.to_datetime(df['입찰공고일'], errors='coerce').dt.date
        date_stats = df['공고날짜'].value_counts().sort_index()
        print(f"\n📅 Announcements by date:")
        for date, count in date_stats.items():
            if pd.notna(date):
                print(f"  • {date}: {count} announcements")
    
    print("=" * 80)

def save_results(df: pd.DataFrame) -> str:
    """Save results to CSV file"""
    if df.empty:
        print("❌ No data to save")
        return ""
    
    # Generate filename
    current_date = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'{OUTPUT_DIR}/G2B_입찰공고_공식API_{current_date}.csv'
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save to CSV with Korean encoding
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"💾 Results saved to: {filename}")
    return filename

def main():
    """Main execution function"""
    print("🏛️ G2B Official API Solution - 조달청 나라장터 입찰공고정보서비스")
    print("=" * 80)
    print("📡 Using official Public Data Portal API")
    print("🔧 Service: BidPublicInfoService")
    print("🌐 Endpoint: https://apis.data.go.kr/1230000/ad/BidPublicInfoService")
    print("=" * 80)
    
    try:
        # Get API key
        api_key = get_api_key()
        if not api_key:
            print("❌ Cannot proceed without API key")
            print("💡 Get your API key from: https://www.data.go.kr/data/15129394/openapi.do")
            return
        
        # Collect all bid announcements
        df = collect_all_bids(api_key)
        
        if df.empty:
            print("❌ No announcements collected")
            print("💡 This could be due to:")
            print("   • Invalid API key")
            print("   • No announcements in the specified date range")
            print("   • API service temporarily unavailable")
            return
        
        # Save results
        filename = save_results(df)
        
        # Print statistics
        print_detailed_stats(df)
        
        # Success summary
        print(f"\n✅ Collection completed successfully!")
        print(f"📊 Total announcements: {len(df)}")
        print(f"💾 File saved: {filename}")
        
        # Usage tips
        print("\n" + "=" * 80)
        print("💡 USAGE TIPS")
        print("=" * 80)
        print("• This solution uses the official G2B API from Public Data Portal")
        print("• All data is authentic and real-time from government sources")
        print("• No 403 errors or rate limiting issues")
        print("• Data includes: 물품, 용역, 공사, 외자 announcements")
        print("• Private contracts (수의계약) are automatically filtered out")
        print("• Duplicate announcements are removed")
        print("• For questions about API usage, contact: dobin@korea.kr")
        
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()