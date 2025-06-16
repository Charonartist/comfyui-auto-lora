"""
LoRA設定管理用のWeb UI（シンプル版）
ComfyUIのサーバーが動いていない場合でも独立して動作
"""

import http.server
import socketserver
import json
import urllib.parse
import os
from .lora_manager import LoraManager

class LoRAWebUIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, lora_manager=None, **kwargs):
        self.lora_manager = lora_manager or LoraManager()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path == '/api/loras':
            self.serve_lora_list()
        elif self.path.startswith('/api/'):
            self.send_error(404)
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/loras':
            self.handle_lora_action()
        else:
            self.send_error(404)
    
    def serve_main_page(self):
        html_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto LoRA 設定管理</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .section h2 { color: #007bff; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        tr:hover { background-color: #f8f9fa; }
        .form-group { margin: 10px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        button.danger { background: #dc3545; }
        button.danger:hover { background: #c82333; }
        .success { color: #28a745; font-weight: bold; }
        .error { color: #dc3545; font-weight: bold; }
        .actions { text-align: center; margin: 20px 0; }
        .delete-btn { background: #dc3545; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px; }
        .delete-btn:hover { background: #c82333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Auto LoRA 設定管理</h1>
        
        <div class="section">
            <h2>📋 登録済みLoRA一覧</h2>
            <div id="lora-list">読み込み中...</div>
            <div class="actions">
                <button onclick="loadLoraList()">🔄 更新</button>
            </div>
        </div>
        
        <div class="section">
            <h2>➕ 新しいLoRA追加</h2>
            <form id="add-form">
                <div class="form-group">
                    <label for="trigger_word">トリガーワード:</label>
                    <input type="text" id="trigger_word" name="trigger_word" required 
                           placeholder="例: miku" />
                </div>
                <div class="form-group">
                    <label for="lora_file">LoRAファイル名:</label>
                    <input type="text" id="lora_file" name="lora_file" required 
                           placeholder="例: hatsune_miku.safetensors" />
                </div>
                <div class="form-group">
                    <label for="strength">強度:</label>
                    <input type="number" id="strength" name="strength" min="0" max="2" step="0.1" value="1.0" />
                </div>
                <div class="form-group">
                    <label for="description">説明 (任意):</label>
                    <textarea id="description" name="description" rows="2" 
                              placeholder="例: 初音ミクのLoRA"></textarea>
                </div>
                <div class="actions">
                    <button type="submit">➕ 追加</button>
                </div>
            </form>
        </div>
        
        <div id="message" style="margin: 20px 0; padding: 10px; display: none;"></div>
    </div>

    <script>
        async function loadLoraList() {
            try {
                const response = await fetch('/api/loras');
                const data = await response.json();
                
                if (data.loras && data.loras.length > 0) {
                    let html = '<table><thead><tr><th>トリガーワード</th><th>LoRAファイル</th><th>強度</th><th>説明</th><th>操作</th></tr></thead><tbody>';
                    
                    data.loras.forEach(lora => {
                        html += `<tr>
                            <td><strong>${lora.trigger_word}</strong></td>
                            <td>${lora.lora_file}</td>
                            <td>${lora.strength}</td>
                            <td>${lora.description || '-'}</td>
                            <td><a href="#" class="delete-btn" onclick="deleteLora('${lora.trigger_word}')">🗑️ 削除</a></td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('lora-list').innerHTML = html;
                } else {
                    document.getElementById('lora-list').innerHTML = '<p>登録済みのLoRAはありません。</p>';
                }
            } catch (error) {
                document.getElementById('lora-list').innerHTML = '<p class="error">読み込みエラー: ' + error.message + '</p>';
            }
        }
        
        async function deleteLora(triggerWord) {
            if (!confirm(`"${triggerWord}" を削除しますか？`)) return;
            
            try {
                const response = await fetch('/api/loras', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'delete', trigger_word: triggerWord })
                });
                
                const result = await response.json();
                showMessage(result.message, result.success ? 'success' : 'error');
                
                if (result.success) {
                    loadLoraList();
                }
            } catch (error) {
                showMessage('削除エラー: ' + error.message, 'error');
            }
        }
        
        function showMessage(message, type) {
            const messageEl = document.getElementById('message');
            messageEl.textContent = message;
            messageEl.className = type;
            messageEl.style.display = 'block';
            setTimeout(() => messageEl.style.display = 'none', 5000);
        }
        
        document.getElementById('add-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {
                action: 'add',
                trigger_word: formData.get('trigger_word'),
                lora_file: formData.get('lora_file'),
                strength: parseFloat(formData.get('strength')),
                description: formData.get('description')
            };
            
            try {
                const response = await fetch('/api/loras', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                showMessage(result.message, result.success ? 'success' : 'error');
                
                if (result.success) {
                    e.target.reset();
                    loadLoraList();
                }
            } catch (error) {
                showMessage('追加エラー: ' + error.message, 'error');
            }
        });
        
        // 初期読み込み
        loadLoraList();
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_lora_list(self):
        try:
            loras = self.lora_manager.list_all_mappings()
            response_data = {
                'success': True,
                'loras': loras
            }
        except Exception as e:
            response_data = {
                'success': False,
                'error': str(e),
                'loras': []
            }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def handle_lora_action(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            action = data.get('action')
            success = False
            message = ""
            
            if action == 'add':
                success = self.lora_manager.add_lora_mapping(
                    data.get('trigger_word', ''),
                    data.get('lora_file', ''),
                    data.get('strength', 1.0),
                    data.get('description', '')
                )
                message = "追加成功" if success else "追加失敗（既に存在する可能性があります）"
                
            elif action == 'delete':
                success = self.lora_manager.remove_lora_mapping(data.get('trigger_word', ''))
                message = "削除成功" if success else "削除失敗（見つかりません）"
            
            response_data = {
                'success': success,
                'message': message
            }
            
        except Exception as e:
            response_data = {
                'success': False,
                'message': f'エラー: {str(e)}'
            }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))


def start_web_ui(port=8765):
    """
    LoRA設定管理用WebUIを起動
    
    Args:
        port: ポート番号
    """
    lora_manager = LoraManager()
    
    def handler(*args, **kwargs):
        return LoRAWebUIHandler(*args, lora_manager=lora_manager, **kwargs)
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"LoRA設定管理WebUIが起動しました: http://localhost:{port}")
            print("Ctrl+C で停止")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nWebUIを停止しました")
    except Exception as e:
        print(f"WebUI起動エラー: {e}")


if __name__ == "__main__":
    start_web_ui()