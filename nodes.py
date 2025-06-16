"""
ComfyUI Auto LoRA カスタムノード実装
"""

import torch
import os
import folder_paths
from .lora_manager import LoraManager

class AutoLoRANode:
    """
    テキストからトリガーワードを検出し、自動的にLoRAを適用するノード
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "text": ("STRING", {
                    "multiline": True, 
                    "default": "beautiful girl"
                }),
            },
            "optional": {
                "enable_auto_lora": ("BOOLEAN", {"default": True}),
                "manual_strength": ("FLOAT", {
                    "default": -1.0, 
                    "min": -1.0, 
                    "max": 2.0, 
                    "step": 0.01,
                    "display": "slider"
                }),
            }
        }
    
    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "text", "lora_info")
    FUNCTION = "apply_auto_lora"
    CATEGORY = "Auto LoRA"
    DESCRIPTION = "テキストからトリガーワードを検出し、対応するLoRAを自動適用"
    
    def __init__(self):
        self.lora_manager = LoraManager()
    
    def apply_auto_lora(self, model, clip, text, enable_auto_lora=True, manual_strength=-1.0):
        """
        自動LoRA適用の主要処理
        
        Args:
            model: 入力モデル
            clip: 入力CLIP
            text: 入力テキスト
            enable_auto_lora: 自動LoRA適用の有効/無効
            manual_strength: 手動強度設定（-1.0の場合は設定ファイルの値を使用）
            
        Returns:
            (model, clip, text, lora_info): 処理結果
        """
        output_model = model
        output_clip = clip
        output_text = text
        lora_info = "LoRA未適用"
        
        if not enable_auto_lora:
            return (output_model, output_clip, output_text, "自動LoRA無効")
        
        try:
            # トリガーワードを検出
            matching_lora = self.lora_manager.get_first_matching_lora(text)
            
            if matching_lora:
                lora_file = matching_lora['lora_file']
                strength = manual_strength if manual_strength >= 0 else matching_lora['strength']
                
                # LoRAファイルのパスを構築
                lora_path = self._find_lora_file(lora_file)
                
                if lora_path and os.path.exists(lora_path):
                    # LoRAを適用
                    output_model, output_clip = self._apply_lora(
                        model, clip, lora_path, strength, strength
                    )
                    
                    lora_info = f"適用: {matching_lora['trigger_word']} -> {lora_file} (強度: {strength})"
                    print(f"[AutoLoRA] {lora_info}")
                else:
                    lora_info = f"エラー: LoRAファイルが見つかりません - {lora_file}"
                    print(f"[AutoLoRA] {lora_info}")
            else:
                lora_info = "トリガーワード未検出"
                
        except Exception as e:
            lora_info = f"エラー: {str(e)}"
            print(f"[AutoLoRA] エラー: {e}")
        
        return (output_model, output_clip, output_text, lora_info)
    
    def _find_lora_file(self, lora_filename):
        """
        LoRAファイルを検索
        
        Args:
            lora_filename: LoRAファイル名
            
        Returns:
            LoRAファイルの完全パス、またはNone
        """
        # ComfyUIのLoRAディレクトリから検索
        lora_paths = folder_paths.get_folder_paths("loras")
        
        for lora_dir in lora_paths:
            lora_path = os.path.join(lora_dir, lora_filename)
            if os.path.exists(lora_path):
                return lora_path
        
        return None
    
    def _apply_lora(self, model, clip, lora_path, model_strength, clip_strength):
        """
        LoRAを適用
        
        Args:
            model: モデル
            clip: CLIP
            lora_path: LoRAファイルパス
            model_strength: モデル強度
            clip_strength: CLIP強度
            
        Returns:
            (model, clip): LoRA適用後のモデルとCLIP
        """
        try:
            # ComfyUIのLoRA読み込み機能を使用
            import comfy.utils
            import comfy.model_management
            
            # LoRAを読み込み
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            
            # モデルにLoRAを適用
            model_lora = comfy.model_management.load_lora_for_models(
                model, clip, lora, model_strength, clip_strength
            )
            
            return model_lora
            
        except Exception as e:
            print(f"[AutoLoRA] LoRA適用エラー: {e}")
            return model, clip


class LoRAManagerNode:
    """
    LoRA設定を管理するノード
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["list", "add", "remove", "reload"], {"default": "list"}),
            },
            "optional": {
                "trigger_word": ("STRING", {"default": ""}),
                "lora_file": ("STRING", {"default": ""}),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "description": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "manage_lora"
    CATEGORY = "Auto LoRA"
    DESCRIPTION = "LoRA設定の管理"
    
    def __init__(self):
        self.lora_manager = LoraManager()
    
    def manage_lora(self, action, trigger_word="", lora_file="", strength=1.0, description=""):
        """
        LoRA設定管理の主要処理
        
        Args:
            action: 実行するアクション
            trigger_word: トリガーワード
            lora_file: LoRAファイル名
            strength: 強度
            description: 説明
            
        Returns:
            (result,): 処理結果
        """
        try:
            if action == "list":
                mappings = self.lora_manager.list_all_mappings()
                if mappings:
                    result_lines = ["=== 登録済みLoRA一覧 ==="]
                    for i, mapping in enumerate(mappings, 1):
                        line = f"{i}. '{mapping['trigger_word']}' -> {mapping['lora_file']} (強度: {mapping.get('strength', 1.0)})"
                        if mapping.get('description'):
                            line += f" - {mapping['description']}"
                        result_lines.append(line)
                    result = "\\n".join(result_lines)
                else:
                    result = "登録済みLoRAはありません"
            
            elif action == "add":
                if not trigger_word or not lora_file:
                    result = "エラー: トリガーワードとLoRAファイル名を指定してください"
                else:
                    success = self.lora_manager.add_lora_mapping(
                        trigger_word, lora_file, strength, description
                    )
                    if success:
                        result = f"追加成功: '{trigger_word}' -> {lora_file}"
                    else:
                        result = f"追加失敗: '{trigger_word}' は既に登録されています"
            
            elif action == "remove":
                if not trigger_word:
                    result = "エラー: 削除するトリガーワードを指定してください"
                else:
                    success = self.lora_manager.remove_lora_mapping(trigger_word)
                    if success:
                        result = f"削除成功: '{trigger_word}'"
                    else:
                        result = f"削除失敗: '{trigger_word}' が見つかりません"
            
            elif action == "reload":
                self.lora_manager.load_config()
                result = "設定ファイルを再読み込みしました"
            
            else:
                result = f"不明なアクション: {action}"
                
        except Exception as e:
            result = f"エラー: {str(e)}"
        
        return (result,)


# ComfyUIに登録するノード
NODE_CLASS_MAPPINGS = {
    "AutoLoRANode": AutoLoRANode,
    "LoRAManagerNode": LoRAManagerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AutoLoRANode": "🤖 Auto LoRA",
    "LoRAManagerNode": "⚙️ LoRA Manager",
}