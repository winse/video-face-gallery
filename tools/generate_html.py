#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate dynamic HTML index page that reads JSON"""

import os
from datetime import datetime

def generate_dynamic_index():
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信视频人脸索引</title>
    <link rel="stylesheet" href="style.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        header { background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { font-size: 28px; color: #333; margin-bottom: 12px; }
        .stats { display: flex; gap: 24px; color: #666; font-size: 14px; }
        .stat-item { display: flex; align-items: center; gap: 4px; }
        .stat-value { font-weight: bold; color: #667eea; font-size: 18px; }
        .search-bar { background: white; border-radius: 12px; padding: 16px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
        #search { width: 100%; max-width: 400px; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 16px; transition: border-color 0.2s; }
        #search:focus { outline: none; border-color: #667eea; }
        .controls { display: flex; gap: 12px; align-items: center; }
        select { padding: 12px; border-radius: 8px; border: 2px solid #e0e0e0; background: white; font-size: 14px; outline: none; transition: border-color 0.2s; }
        select:focus { border-color: #667eea; }
        .person-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px; }
        .person-card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s, box-shadow 0.2s; cursor: pointer; text-decoration: none; display: block; }
        .person-card:hover { transform: translateY(-4px); box-shadow: 0 8px 16px rgba(0,0,0,0.15); }
        .person-avatar { width: 100%; height: 200px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .person-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .person-info { padding: 16px; }
        .person-id { font-size: 14px; color: #999; margin-bottom: 4px; }
        .person-name { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 8px; }
        .person-stats { display: flex; gap: 12px; font-size: 12px; color: #666; }
        .person-stat { display: flex; align-items: center; gap: 4px; }
        .loading-text { font-size: 20px; color: white; text-align: center; padding: 40px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>微信视频人脸索引</h1>
            <div class="stats" id="stats">
                <!-- Loaded dynamically -->
            </div>
        </header>

        <div class="search-bar">
            <input type="text" id="search" placeholder="搜索人物 ID (例: 0001)...">
            <div class="controls">
                <select id="sortOrder">
                    <option value="faces">按人脸数排序 ↓</option>
                    <option value="videos">按视频数排序 ↓</option>
                    <option value="time">按最新时间排序 ↓</option>
                </select>
                <button onclick="toggleTheme()" style="background:none;border:none;font-size:24px;cursor:pointer;">🌓</button>
            </div>
        </div>

        <div id="loading" class="loading-text">正在加载人脸数据 (face_data.json)...</div>
        
        <div class="person-grid" id="personGrid">
            <!-- Loaded dynamically -->
        </div>

        <p style="text-align: center; color: white; padding: 24px; font-size: 12px;" id="lastUpdate">
        </p>
    </div>

    <!-- detail.js might be loaded later if detail page requires it, here we use data_manager to fetch -->
    <script src="data_manager.js"></script>
    <script src="index.js"></script>
    <script>
        let faceData = null;
        let personsArray = [];

        async function init() {
            try {
                // Read json data directly from html
                faceData = await DataManager.loadData('face_data.json', 'face_data');
                
                const meta = faceData.metadata || {};
                document.getElementById('lastUpdate').textContent = '最后更新时间: ' + (meta.updated_at || meta.created_at || new Date().toISOString());

                const personsMap = faceData.persons || {};
                const faceMap = faceData.faces || {};
                
                // Convert persons dictionary to array for searching and sorting
                personsArray = Object.keys(personsMap).map(pid => {
                    return {
                        id: pid,
                        ...personsMap[pid]
                    };
                });
                
                // Update stats
                const totalFaces = Object.keys(faceMap).length;
                const statsHtml = `
                    <div class="stat-item"><span class="stat-value">${totalFaces}</span><span> 人脸</span></div>
                    <div class="stat-item"><span class="stat-value">${personsArray.length}</span><span> 人物</span></div>
                `;
                document.getElementById('stats').innerHTML = statsHtml;

                document.getElementById('loading').style.display = 'none';

                // Initial render
                applyFiltersAndRender();
            } catch (error) {
                console.error('Data loading error:', error);
                document.getElementById('loading').innerHTML = `
                    <div style="color: #ffcccc;">
                        <p>❌ 数据加载失败！</p>
                        <p style="font-size: 14px; margin-top: 8px;">请确保通过本地服务器 (HTTP) 访问，而不是直接双击 HTML 文件。</p>
                        <p style="font-size: 14px;">错误详情: ${error.message}</p>
                    </div>`;
            }
        }

        function getThumbnail(pdata) {
            const faces = pdata.faces || [];
            if (!faces.length) return null;
            const f = faceData.faces[faces[0]] || {};
            const t = f.thumbnail_path || f.frame_path || '';
            const parts = t.replace(/\\\\/g, '/').split('thumbnails/');
            return parts.length > 1 ? parts.pop() : null;
        }

        function renderPersons(items) {
            const grid = document.getElementById('personGrid');
            if (items.length === 0) {
                grid.innerHTML = '<div style="color: white; grid-column: 1/-1; text-align: center; padding: 40px;">没有找到匹配的人物...</div>';
                return;
            }

            const html = items.map(p => {
                const thumb = getThumbnail(p);
                const thumbHtml = thumb ? `<img src="thumbnails/${thumb}" loading="lazy" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect width=%22100%22 height=%22100%22 fill=%22%23ccc%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2240%22>👤</text></svg>'">` : '<span style="font-size: 48px; color: #999;">👤</span>';
                
                return `
                    <a class="person-card" href="detail.html?id=${encodeURIComponent(p.id)}">
                        <div class="person-avatar">${thumbHtml}</div>
                        <div class="person-info">
                            <div class="person-id">${p.id}</div>
                            <div class="person-name">Person #${p.cluster_id}</div>
                            <div class="person-stats">
                                <div class="person-stat"><span>🖼️</span><span>${p.face_count || 0} 张</span></div>
                                <div class="person-stat"><span>📹</span><span>${p.video_count || 0} 个视频</span></div>
                            </div>
                        </div>
                    </a>
                `;
            }).join('');
            
            grid.innerHTML = html;
        }

        function applyFiltersAndRender() {
            const query = document.getElementById('search').value.toLowerCase();
            const sortBy = document.getElementById('sortOrder').value;

            // Search Filter
            let filtered = personsArray;
            if (query) {
                filtered = personsArray.filter(p => 
                    p.id.toLowerCase().includes(query) || 
                    String(p.cluster_id).includes(query)
                );
            }

            // Sorting
            if (sortBy === 'faces') {
                filtered.sort((a, b) => (b.face_count || 0) - (a.face_count || 0));
            } else if (sortBy === 'videos') {
                filtered.sort((a, b) => (b.video_count || 0) - (a.video_count || 0));
            } else if (sortBy === 'time') {
                filtered.sort((a, b) => (b.last_seen || 0) - (a.last_seen || 0));
            }

            renderPersons(filtered);
        }

        // Event Listeners
        document.getElementById('search').addEventListener('input', applyFiltersAndRender);
        document.getElementById('sortOrder').addEventListener('change', applyFiltersAndRender);

        // Start
        init();
    </script>
</body>
</html>"""
    
    out_dir = 'web'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'index.html')
    
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Generated dynamic {out_path} that reads 'face_data.json' via JS!")
        print("Note: The previous design generated dozens of static HTML files in 'person_details'.")
        print("Now it uses a clean Single Page App approach reading JSON dynamically, which scales much better!")
    except Exception as e:
        print(f"Error generating html: {e}")

if __name__ == '__main__':
    generate_dynamic_index()
