
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2B 데이터베이스 웹 인터페이스
Flask 기반 실시간 입찰공고 조회 시스템
"""

from flask import Flask, render_template, jsonify, request, send_file
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)

DB_NAME = "g2b_bids.db"

def get_db_connection():
    """데이터베이스 연결"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/statistics')
def api_statistics():
    """통계 API"""
    conn = get_db_connection()
    
    # 전체 통계
    cursor = conn.execute("SELECT COUNT(*) as total FROM bids")
    total_count = cursor.fetchone()['total']
    
    # 카테고리별 통계
    cursor = conn.execute("SELECT category, COUNT(*) as count FROM bids GROUP BY category")
    category_stats = [{'category': row['category'], 'count': row['count']} for row in cursor.fetchall()]
    
    # 최근 7일 수집 현황
    cursor = conn.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM bids 
        WHERE DATE(created_at) >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    """)
    daily_stats = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]
    
    # 수집 방법별 통계
    cursor = conn.execute("SELECT collection_method, COUNT(*) as count FROM bids GROUP BY collection_method")
    method_stats = [{'method': row['collection_method'], 'count': row['count']} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'total_count': total_count,
        'category_stats': category_stats,
        'daily_stats': daily_stats,
        'method_stats': method_stats,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/bids')
def api_bids():
    """입찰공고 목록 API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    
    # 기본 쿼리
    query = "SELECT * FROM bids WHERE 1=1"
    params = []
    
    # 필터링
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if search:
        query += " AND (title LIKE ? OR agency LIKE ? OR department LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    # 정렬 및 페이징
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor = conn.execute(query, params)
    bids = [dict(row) for row in cursor.fetchall()]
    
    # 전체 개수
    count_query = query.replace("SELECT * FROM", "SELECT COUNT(*) as total FROM").split("ORDER BY")[0]
    cursor = conn.execute(count_query, params[:-2])
    total_count = cursor.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'bids': bids,
        'total_count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page
    })

@app.route('/api/export')
def api_export():
    """CSV 내보내기 API"""
    conn = get_db_connection()
    
    query = '''
        SELECT 
            title as "공고명",
            bid_number as "공고번호", 
            agency as "공고기관",
            department as "수요기관",
            contract_method as "계약방법",
            announcement_date as "입찰공고일",
            deadline_date as "입찰마감일시",
            opening_date as "개찰일시",
            estimated_price as "예정가격",
            category as "입찰분류",
            collection_date as "수집일시",
            collection_method as "수집방법"
        FROM bids 
        ORDER BY created_at DESC
    '''
    
    import pandas as pd
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # CSV 파일 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"output/G2B_Export_{timestamp}.csv"
    os.makedirs("output", exist_ok=True)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    return send_file(filename, as_attachment=True, download_name=f"G2B_입찰공고_{timestamp}.csv")

@app.route('/collect')
def collect_data():
    """데이터 수집 트리거"""
    try:
        from g2b_db_solution import G2BCollector
        collector = G2BCollector()
        stats = collector.run_collection()
        collector.db.close()
        
        return jsonify({
            'success': True,
            'message': '데이터 수집 완료',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'수집 실패: {str(e)}'
        })

if __name__ == '__main__':
    # 템플릿 디렉토리 생성
    os.makedirs('templates', exist_ok=True)
    
    # 기본 HTML 템플릿이 없으면 생성
    template_path = 'templates/index.html'
    if not os.path.exists(template_path):
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write('''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>G2B 입찰공고 데이터베이스</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2196F3; }
        .controls { margin-bottom: 20px; }
        .controls input, .controls select, .controls button { margin: 5px; padding: 8px; }
        .table-container { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .pagination { text-align: center; margin-top: 20px; }
        .pagination button { margin: 0 5px; padding: 8px 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ G2B 입찰공고 데이터베이스</h1>
            <p>실시간 입찰공고 조회 및 관리 시스템</p>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-count">-</div>
                <div>전체 공고</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="today-count">-</div>
                <div>오늘 수집</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="category-count">-</div>
                <div>카테고리</div>
            </div>
        </div>
        
        <div class="controls">
            <input type="text" id="search" placeholder="공고명, 기관명 검색...">
            <select id="category">
                <option value="">전체 분류</option>
                <option value="물품">물품</option>
                <option value="용역">용역</option>
                <option value="공사">공사</option>
                <option value="외자">외자</option>
            </select>
            <button onclick="loadBids()">검색</button>
            <button onclick="collectData()">데이터 수집</button>
            <button onclick="exportData()">CSV 내보내기</button>
        </div>
        
        <div class="table-container">
            <table id="bids-table">
                <thead>
                    <tr>
                        <th>공고명</th>
                        <th>공고번호</th>
                        <th>공고기관</th>
                        <th>계약방법</th>
                        <th>입찰마감일</th>
                        <th>분류</th>
                        <th>수집일시</th>
                    </tr>
                </thead>
                <tbody id="bids-body">
                </tbody>
            </table>
        </div>
        
        <div class="pagination" id="pagination"></div>
    </div>

    <script>
        let currentPage = 1;
        
        // 통계 로드
        async function loadStats() {
            try {
                const response = await fetch('/api/statistics');
                const stats = await response.json();
                
                document.getElementById('total-count').textContent = stats.total_count;
                document.getElementById('today-count').textContent = stats.daily_stats.reduce((sum, day) => sum + day.count, 0);
                document.getElementById('category-count').textContent = stats.category_stats.length;
            } catch (error) {
                console.error('통계 로드 실패:', error);
            }
        }
        
        // 입찰공고 목록 로드
        async function loadBids(page = 1) {
            try {
                const search = document.getElementById('search').value;
                const category = document.getElementById('category').value;
                
                const params = new URLSearchParams({
                    page: page,
                    per_page: 20,
                    search: search,
                    category: category
                });
                
                const response = await fetch(`/api/bids?${params}`);
                const data = await response.json();
                
                const tbody = document.getElementById('bids-body');
                tbody.innerHTML = '';
                
                data.bids.forEach(bid => {
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td><a href="${bid.link_url}" target="_blank">${bid.title}</a></td>
                        <td>${bid.bid_number}</td>
                        <td>${bid.agency}</td>
                        <td>${bid.contract_method}</td>
                        <td>${bid.deadline_date}</td>
                        <td>${bid.category}</td>
                        <td>${bid.collection_date}</td>
                    `;
                });
                
                // 페이지네이션
                const pagination = document.getElementById('pagination');
                pagination.innerHTML = '';
                
                for (let i = 1; i <= data.total_pages; i++) {
                    const button = document.createElement('button');
                    button.textContent = i;
                    button.onclick = () => loadBids(i);
                    if (i === page) button.style.fontWeight = 'bold';
                    pagination.appendChild(button);
                }
                
                currentPage = page;
                
            } catch (error) {
                console.error('데이터 로드 실패:', error);
                alert('데이터 로드에 실패했습니다.');
            }
        }
        
        // 데이터 수집
        async function collectData() {
            try {
                const button = event.target;
                button.disabled = true;
                button.textContent = '수집 중...';
                
                const response = await fetch('/collect');
                const result = await response.json();
                
                if (result.success) {
                    alert('데이터 수집이 완료되었습니다.');
                    loadStats();
                    loadBids();
                } else {
                    alert(`수집 실패: ${result.message}`);
                }
                
            } catch (error) {
                console.error('수집 실패:', error);
                alert('데이터 수집에 실패했습니다.');
            } finally {
                const button = event.target;
                button.disabled = false;
                button.textContent = '데이터 수집';
            }
        }
        
        // CSV 내보내기
        function exportData() {
            window.open('/api/export', '_blank');
        }
        
        // 초기 로드
        loadStats();
        loadBids();
        
        // 엔터키 검색
        document.getElementById('search').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loadBids();
            }
        });
    </script>
</body>
</html>
            ''')
    
    print("🌐 G2B 웹 인터페이스 시작")
    print("📡 브라우저에서 http://0.0.0.0:5000 접속")
    app.run(host='0.0.0.0', port=5000, debug=True)
