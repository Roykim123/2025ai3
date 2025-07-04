# G2B 입찰공고 자동수집 시스템

## Overview

This is a Korean Government Procurement (G2B) bid collection system that automatically scrapes bid announcements from the official G2B website. The system has been converted from a web application to a single-file command-line script for local execution.

## System Architecture

### Single-File CLI Architecture
- **Main Script**: Single main.py file containing all functionality
- **No Web Interface**: Removed Flask web application components
- **Local Execution**: Designed for command-line execution on local PC
- **CSV Output**: Direct CSV file generation to output directory

### Backend Components
- **Data Processing**: Pandas for data manipulation and CSV export
- **HTTP Client**: Requests library with enhanced session management for G2B API calls
- **Error Handling**: Comprehensive error handling with detailed diagnostics

### Data Collection Strategy
- **Direct API Calls**: POST requests to G2B procurement API
- **Enhanced Session Management**: Multi-step session establishment to mimic browser behavior
- **Rate Limiting**: Built-in request delays to respect server limits
- **Anti-Bot Protection**: Advanced headers and session handling for government site access

## Key Components

### 1. Session Management
- **Purpose**: Establish authenticated session with G2B website
- **Features**: 
  - Multi-step page visits to acquire cookies
  - Browser-like headers with Chrome user agent
  - Proper referer and security headers

### 2. Data Collection Engine
- **Purpose**: Core bid collection functionality
- **Features**:
  - Configurable search parameters (7-day default)
  - JSON payload construction for POST API
  - Data parsing and filtering
  - Automatic exclusion of private contracts (수의계약)

### 3. CSV Export System
- **Purpose**: Data export and file management
- **Features**:
  - UTF-8 BOM encoding for Korean characters
  - Date-based file naming (입찰공고_YYYYMMDD.csv)
  - Automatic output directory creation
  - Statistical summary generation

### 4. Demo Data Generation
- **Purpose**: Fallback when API access is restricted
- **Features**:
  - Sample bid data for testing
  - Proper data structure demonstration
  - Educational examples

## Data Flow

1. **Session Establishment**: Visit main pages to acquire cookies and session state
2. **API Request**: Send POST request with JSON payload to G2B API
3. **Data Processing**: Parse JSON response and filter out private contracts
4. **CSV Generation**: Save processed data as CSV with Korean encoding
5. **Statistics Display**: Show collection summary and file location

## Current Limitations

### G2B API Access
- **403 Forbidden**: Government site blocks automated requests
- **Anti-Bot Protection**: Advanced protection measures prevent script access
- **Solution Required**: May need proxy, VPN, or alternative approach for real data access

### Workarounds
- **Demo Data**: Sample data generation when API fails
- **Error Diagnostics**: Detailed error reporting for troubleshooting
- **Local Ready**: Script prepared for local PC execution when API access works

## Dependencies

### Core Dependencies
- **Requests**: HTTP client for G2B API communication
- **Pandas**: Data manipulation and CSV export

### Installation
```bash
pip install requests pandas
```

## Usage

### Local Execution
```bash
python main.py
```

### Output
- File: `output/입찰공고_YYYYMMDD.csv`
- Statistics: Terminal output with collection summary
- Encoding: UTF-8 with BOM for Korean character support

## Recent Changes
- July 04, 2025: Converted from web application to single CLI script
- July 04, 2025: Removed Flask, templates, static files, and web interface
- July 04, 2025: Enhanced session management for government site access
- July 04, 2025: Added demo data generation for API access issues
- July 04, 2025: Implemented detailed error diagnostics and user guidance
- July 04, 2025: Added Selenium browser automation to bypass 403 Forbidden errors
- July 04, 2025: Created g2b_local_version.py optimized for local PC execution
- July 04, 2025: Implemented both headless and visual browser automation options
- July 04, 2025: Updated for 차세대 나라장터 2025 system changes
- July 04, 2025: Added public data API integration as primary method
- July 04, 2025: Created complete multi-method solution with fallbacks
- July 04, 2025: Updated selectors and URLs for new G2B system structure

## 차세대 나라장터 2025 대응
- **시스템 변경**: 2025년 1월 6일 차세대 나라장터 시범 개통
- **URL 변경**: 기존 프레임 기반에서 새로운 구조로 전환
- **API 우선**: 공공데이터포털 공식 API를 1순위 수집 방법으로 채택
- **다중 방법**: API, 브라우저 자동화, 데모 데이터 순서로 fallback 구현

## Multi-Method Solution
1. **Public Data API** (최우선)
   - 공공데이터포털 공식 API 활용
   - 안정적이고 대용량 데이터 처리 가능
   - API 키 발급 필요: https://www.data.go.kr/data/15129394/openapi.do

2. **Browser Automation** (차선책)
   - 차세대 나라장터 구조에 맞는 스마트 셀렉터 탐지
   - 여러 URL 시도 및 테이블 자동 인식
   - 로컬 PC에서 Chrome 브라우저 필요

3. **Demo Data** (마지막 수단)
   - 다른 방법 실패시 구조 확인용 샘플 데이터

## Browser Automation Features
- **Purpose**: Bypass G2B's anti-bot protection that causes 403 errors
- **Technology**: Selenium WebDriver with automatic ChromeDriver management
- **2025 Compatibility**: Updated selectors for new system structure
- **Smart Detection**: Advanced table detection and content analysis
- **Capabilities**: 
  - Real browser session mimicking human behavior
  - Multiple URL fallback strategy
  - Intelligent selector adaptation
  - Table structure analysis and data mapping
  - Multi-platform support (Windows, macOS, Linux)

## User Preferences

Preferred communication style: Simple, everyday language.
Preferred architecture: Single-file CLI script for local execution.
Preferred solution: Browser automation for reliable G2B data access.