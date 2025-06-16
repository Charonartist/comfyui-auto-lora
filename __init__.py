"""
ComfyUI Auto LoRA - 自動LoRA適用カスタムノード

このカスタムノードは、入力テキストからトリガーワードを検出し、
対応するLoRAを自動的に適用するComfyUIカスタムノードです。
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# ComfyUIに認識させるための設定
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

# バージョン情報
__version__ = "1.0.0"
__author__ = "Claude Code"
__description__ = "自動LoRA適用カスタムノード"