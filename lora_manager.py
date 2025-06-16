import json
import os
import re
from typing import Dict, List, Optional, Tuple

class LoraManager:
    """Loraの管理とトリガーワード検出を行うクラス"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # カスタムノードのディレクトリを基準にconfigファイルのパスを設定
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "config", "lora_mapping.json")
        
        self.config_path = config_path
        self.lora_mappings = []
        self.settings = {}
        self.load_config()
    
    def load_config(self):
        """設定ファイルを読み込む"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.lora_mappings = config.get('lora_mappings', [])
                    self.settings = config.get('settings', {})
            else:
                print(f"設定ファイルが見つかりません: {self.config_path}")
                self.create_default_config()
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """デフォルト設定を作成"""
        default_config = {
            "lora_mappings": [
                {
                    "trigger_word": "example_trigger",
                    "lora_file": "example_lora.safetensors",
                    "strength": 1.0,
                    "description": "例 - この設定を編集してください"
                }
            ],
            "settings": {
                "case_sensitive": False,
                "max_lora_count": 3,
                "default_strength": 1.0
            }
        }
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self.lora_mappings = default_config['lora_mappings']
        self.settings = default_config['settings']
    
    def save_config(self):
        """設定ファイルを保存"""
        try:
            config = {
                "lora_mappings": self.lora_mappings,
                "settings": self.settings
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"設定ファイルの保存エラー: {e}")
            return False
    
    def find_trigger_words(self, text: str) -> List[Dict]:
        """
        テキスト内のトリガーワードを検出する
        
        Args:
            text: 検索対象のテキスト
            
        Returns:
            マッチしたトリガーワード情報のリスト
        """
        if not text:
            return []
        
        case_sensitive = self.settings.get('case_sensitive', False)
        search_text = text if case_sensitive else text.lower()
        
        found_triggers = []
        
        for mapping in self.lora_mappings:
            trigger_word = mapping['trigger_word']
            if not case_sensitive:
                trigger_word = trigger_word.lower()
            
            # 完全一致での検出（単語境界を考慮）
            pattern = r'\b' + re.escape(trigger_word) + r'\b'
            
            if re.search(pattern, search_text):
                found_triggers.append({
                    'trigger_word': mapping['trigger_word'],
                    'lora_file': mapping['lora_file'],
                    'strength': mapping.get('strength', self.settings.get('default_strength', 1.0)),
                    'description': mapping.get('description', ''),
                    'original_mapping': mapping
                })
                
                # 最初に見つかったもののみ返す（仕様通り）
                break
        
        return found_triggers
    
    def get_first_matching_lora(self, text: str) -> Optional[Dict]:
        """
        最初にマッチしたLoraの情報を取得
        
        Args:
            text: 検索対象のテキスト
            
        Returns:
            マッチしたLora情報、またはNone
        """
        triggers = self.find_trigger_words(text)
        return triggers[0] if triggers else None
    
    def add_lora_mapping(self, trigger_word: str, lora_file: str, 
                        strength: float = 1.0, description: str = "") -> bool:
        """
        新しいLora マッピングを追加
        
        Args:
            trigger_word: トリガーワード
            lora_file: Loraファイル名
            strength: 強度
            description: 説明
            
        Returns:
            成功したかどうか
        """
        # 既存のトリガーワードをチェック
        for mapping in self.lora_mappings:
            if mapping['trigger_word'].lower() == trigger_word.lower():
                print(f"トリガーワード '{trigger_word}' は既に登録されています")
                return False
        
        new_mapping = {
            "trigger_word": trigger_word,
            "lora_file": lora_file,
            "strength": strength,
            "description": description
        }
        
        self.lora_mappings.append(new_mapping)
        return self.save_config()
    
    def remove_lora_mapping(self, trigger_word: str) -> bool:
        """
        Loraマッピングを削除
        
        Args:
            trigger_word: 削除するトリガーワード
            
        Returns:
            成功したかどうか
        """
        for i, mapping in enumerate(self.lora_mappings):
            if mapping['trigger_word'].lower() == trigger_word.lower():
                del self.lora_mappings[i]
                return self.save_config()
        
        print(f"トリガーワード '{trigger_word}' が見つかりません")
        return False
    
    def update_lora_mapping(self, trigger_word: str, **updates) -> bool:
        """
        Loraマッピングを更新
        
        Args:
            trigger_word: 更新するトリガーワード
            **updates: 更新する項目
            
        Returns:
            成功したかどうか
        """
        for mapping in self.lora_mappings:
            if mapping['trigger_word'].lower() == trigger_word.lower():
                for key, value in updates.items():
                    if key in ['lora_file', 'strength', 'description']:
                        mapping[key] = value
                return self.save_config()
        
        print(f"トリガーワード '{trigger_word}' が見つかりません")
        return False
    
    def list_all_mappings(self) -> List[Dict]:
        """
        全てのLoraマッピングを取得
        
        Returns:
            Loraマッピングのリスト
        """
        return self.lora_mappings.copy()
    
    def get_settings(self) -> Dict:
        """
        設定を取得
        
        Returns:
            設定辞書
        """
        return self.settings.copy()
    
    def update_settings(self, **settings) -> bool:
        """
        設定を更新
        
        Args:
            **settings: 更新する設定項目
            
        Returns:
            成功したかどうか
        """
        self.settings.update(settings)
        return self.save_config()