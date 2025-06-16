#!/usr/bin/env python3
"""
Auto LoRA WebUI 起動スクリプト
"""

from web_ui import start_web_ui
import argparse

def main():
    parser = argparse.ArgumentParser(description='Auto LoRA 設定管理WebUIを起動')
    parser.add_argument('--port', type=int, default=8765, help='ポート番号 (デフォルト: 8765)')
    
    args = parser.parse_args()
    
    print("=== Auto LoRA 設定管理WebUI ===")
    print(f"ポート: {args.port}")
    print("設定ファイル: config/lora_mapping.json")
    print("")
    
    start_web_ui(args.port)

if __name__ == "__main__":
    main()