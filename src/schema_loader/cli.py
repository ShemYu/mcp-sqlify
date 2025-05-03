#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema Loader 命令列工具。

提供從命令列載入和輸出 SQLite schema 的功能。
"""

import os
import sys
import argparse
from pathlib import Path

from src.schema_loader.loader import load_schema


def parse_args():
    """解析命令列參數。"""
    parser = argparse.ArgumentParser(
        description='從 SQLite 資料庫載入 schema 並輸出為 JSON 格式'
    )
    
    parser.add_argument(
        'db_path',
        help='SQLite 資料庫檔案的路徑'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='輸出的 JSON 檔案路徑（若未指定，則輸出到標準輸出）'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='美化輸出的 JSON（預設：是）'
    )
    
    return parser.parse_args()


def main():
    """主函數。"""
    args = parse_args()
    
    # 檢查資料庫檔案是否存在
    if not os.path.isfile(args.db_path):
        print(f"錯誤：找不到資料庫檔案 {args.db_path}", file=sys.stderr)
        return 1
    
    try:
        # 載入 schema
        schema = load_schema(args.db_path, args.output, args.pretty)
        
        # 如果沒有指定輸出檔案，則輸出到標準輸出
        if not args.output:
            import json
            print(json.dumps(schema, ensure_ascii=False, indent=2))
            
        print(f"已成功載入 schema！", file=sys.stderr)
        
        if args.output:
            print(f"Schema 已保存到：{args.output}", file=sys.stderr)
            
    except Exception as e:
        print(f"錯誤：{str(e)}", file=sys.stderr)
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
