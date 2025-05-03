#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Manager 命令列工具。

提供從命令列管理 WikiSQL 資料集與 SQLite 轉換的功能。
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from .manager import DataManager


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool):
    """設置日誌級別"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def download_command(args):
    """下載 WikiSQL 資料集"""
    dm = DataManager(args.data_root)
    
    for split in args.splits:
        try:
            # 下載檔案
            if args.force:
                print(f"強制重新下載資料集 {split}...")
            else:
                print(f"下載資料集 {split}（如果不存在）...")
                
            file_path = dm.dataset.download_dataset(split, args.force)
            print(f"資料集 {split} 已下載至 {file_path}")
            
        except Exception as e:
            print(f"下載 {split} 失敗: {str(e)}", file=sys.stderr)
            if not args.continue_on_error:
                return 1
    
    return 0


def info_command(args):
    """顯示資料集資訊"""
    dm = DataManager(args.data_root)
    info = dm.get_dataset_info()
    
    print("WikiSQL 資料集資訊:")
    print("-" * 50)
    
    for split, split_info in info['splits'].items():
        if split_info.get('file_path'):
            status = "已下載"
            examples = f"{split_info['examples']:,} 個範例"
            size = f"{split_info['file_size'] / (1024*1024):.2f} MB"
        else:
            status = "未下載"
            examples = "N/A"
            size = "N/A"
            
        print(f"{split}: {status}, {examples}, {size}")
        
    print("\n資料庫資訊:")
    print(f"預設資料庫: {info['database']['default_db_path']}")
    print(f"測試資料庫目錄: {info['database']['test_db_dir']}")
    
    return 0


def sample_command(args):
    """顯示範例資料"""
    dm = DataManager(args.data_root)
    
    try:
        if args.index is not None:
            # 獲取特定範例
            example = dm.dataset.get_example(args.split, args.index)
            examples = [example]
        else:
            # 獲取多個範例
            examples = dm.dataset.load_split(args.split, args.limit)
        
        for i, example in enumerate(examples):
            if i > 0:
                print("\n" + "-" * 70 + "\n")
                
            print(f"範例 {args.index if args.index is not None else i}:")
            print(f"問題: {example['question']}")
            
            # 表格資訊
            print(f"\n表格欄位: {example['table']['header']}")
            print(f"欄位類型: {example['table']['types']}")
            
            # 顯示部分表格資料
            rows = example['table']['rows']
            print(f"\n表格資料 (共 {len(rows)} 行):")
            
            table_data = rows[:min(5, len(rows))]
            print(tabulate(table_data, headers=example['table']['header']))
            
            # SQL 資訊
            sql = example['sql']
            if 'human_readable' in sql:
                print(f"\nSQL: {sql['human_readable']}")
            else:
                print(f"\nSQL: {json.dumps(sql, ensure_ascii=False, indent=2)}")
            
            if args.convert:
                print("\n轉換為 SQLite:")
                with dm.converter:
                    result = dm.converter.convert_example(example)
                    print(f"表名: {result['sqlite_info']['table_name']}")
                    print(f"建表 SQL: \n{result['sqlite_info']['create_sql']}")
                    
                    if result['sqlite_info']['target_sql']:
                        print(f"目標 SQL: {result['sqlite_info']['target_sql']}")
            
            if i >= args.limit - 1:
                break
        
    except Exception as e:
        print(f"顯示範例失敗: {str(e)}", file=sys.stderr)
        return 1
    
    return 0


def convert_command(args):
    """轉換 WikiSQL 為 SQLite 資料庫"""
    dm = DataManager(args.data_root, args.db_path)
    
    try:
        # 載入範例
        print(f"載入 {args.split} 資料集，限制 {args.limit} 個範例...")
        examples = dm.dataset.load_split(args.split, args.limit)
        
        # 轉換為 SQLite
        print(f"轉換為 SQLite 資料庫 {args.db_path}...")
        with dm.converter:
            results = dm.converter.convert_examples(examples)
        
        # 顯示轉換結果
        print(f"已成功轉換 {len(results)} 個範例至 SQLite 資料庫。")
        
        # 列出所有表格
        with dm.converter:
            columns, rows = dm.converter.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            tables = [row[0] for row in rows]
            
        print(f"\n資料庫中的表 ({len(tables)}):")
        for i, table in enumerate(tables):
            if i > 0 and i % 5 == 0:
                print()
            print(f"{table}", end=", " if i < len(tables) - 1 else "\n")
        
    except Exception as e:
        print(f"轉換失敗: {str(e)}", file=sys.stderr)
        return 1
    
    return 0


def test_db_command(args):
    """管理測試資料庫"""
    dm = DataManager(args.data_root)
    
    try:
        if args.clear:
            # 清除所有測試資料庫
            print("清除所有測試資料庫...")
            dm.test_db_manager.clear_test_dbs()
            print("測試資料庫已清除。")
        else:
            # 創建測試資料庫
            print(f"從 {args.split} 分割創建測試資料庫 {args.name}...")
            db_path = dm.create_test_database(args.name, args.split, args.limit)
            
            print(f"測試資料庫已創建: {db_path}")
            
            # 列出所有表格
            columns, rows = dm.execute_query(
                db_path,
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            tables = [row[0] for row in rows]
            
            print(f"\n資料庫中的表 ({len(tables)}):")
            for table in tables:
                print(f"- {table}")
            
            # 為每個表顯示行數
            print("\n各表行數:")
            for table in tables:
                columns, rows = dm.execute_query(
                    db_path,
                    f"SELECT COUNT(*) FROM \"{table}\";"
                )
                count = rows[0][0] if rows else 0
                print(f"- {table}: {count} 行")
        
    except Exception as e:
        print(f"測試資料庫操作失敗: {str(e)}", file=sys.stderr)
        return 1
    
    return 0


def query_command(args):
    """在 SQLite 資料庫上執行查詢"""
    dm = DataManager(args.data_root, args.db_path)
    
    try:
        # 執行查詢
        print(f"在 {args.db_path} 上執行查詢: {args.query}")
        columns, rows = dm.execute_query(args.db_path, args.query)
        
        # 顯示結果
        if not rows:
            print("查詢未返回結果。")
        else:
            print(f"查詢返回 {len(rows)} 行:")
            print(tabulate(rows[:min(20, len(rows))], headers=columns))
            
            if len(rows) > 20:
                print(f"... 僅顯示前 20 行，共 {len(rows)} 行")
        
    except Exception as e:
        print(f"查詢失敗: {str(e)}", file=sys.stderr)
        return 1
    
    return 0


def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='WikiSQL 資料管理與 SQLite 轉換工具'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='啟用詳細日誌輸出'
    )
    
    parser.add_argument(
        '--data-root',
        help='WikiSQL 資料存儲的根目錄'
    )
    
    # 建立子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # download 命令
    download_parser = subparsers.add_parser(
        'download',
        help='下載 WikiSQL 資料集'
    )
    download_parser.add_argument(
        'splits',
        nargs='+',
        choices=['train', 'dev', 'test', 'all'],
        help='要下載的資料分割'
    )
    download_parser.add_argument(
        '--force',
        action='store_true',
        help='強制重新下載，即使檔案已存在'
    )
    download_parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='出錯時繼續下載其他分割'
    )
    
    # info 命令
    info_parser = subparsers.add_parser(
        'info',
        help='顯示資料集資訊'
    )
    
    # sample 命令
    sample_parser = subparsers.add_parser(
        'sample',
        help='顯示範例資料'
    )
    sample_parser.add_argument(
        '--split',
        default='train',
        choices=['train', 'dev', 'test'],
        help='資料分割'
    )
    sample_parser.add_argument(
        '--index',
        type=int,
        help='特定範例的索引'
    )
    sample_parser.add_argument(
        '--limit',
        type=int,
        default=1,
        help='顯示的範例數量'
    )
    sample_parser.add_argument(
        '--convert',
        action='store_true',
        help='同時顯示轉換為 SQLite 的結果'
    )
    
    # convert 命令
    convert_parser = subparsers.add_parser(
        'convert',
        help='轉換 WikiSQL 為 SQLite 資料庫'
    )
    convert_parser.add_argument(
        '--split',
        default='dev',
        choices=['train', 'dev', 'test'],
        help='要轉換的資料分割'
    )
    convert_parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='轉換的範例數量'
    )
    convert_parser.add_argument(
        '--db-path',
        help='SQLite 資料庫檔案的路徑'
    )
    
    # test-db 命令
    test_db_parser = subparsers.add_parser(
        'test-db',
        help='管理測試資料庫'
    )
    test_db_parser.add_argument(
        '--name',
        default='test',
        help='測試資料庫名稱'
    )
    test_db_parser.add_argument(
        '--split',
        default='dev',
        choices=['train', 'dev', 'test'],
        help='使用的資料分割'
    )
    test_db_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='使用的範例數量'
    )
    test_db_parser.add_argument(
        '--clear',
        action='store_true',
        help='清除所有測試資料庫'
    )
    
    # query 命令
    query_parser = subparsers.add_parser(
        'query',
        help='在 SQLite 資料庫上執行查詢'
    )
    query_parser.add_argument(
        'query',
        help='SQL 查詢'
    )
    query_parser.add_argument(
        '--db-path',
        required=True,
        help='SQLite 資料庫檔案的路徑'
    )
    
    return parser.parse_args()


def main():
    """主函數"""
    args = parse_args()
    setup_logging(args.verbose)
    
    # 擴展 'all' 參數
    if hasattr(args, 'splits') and 'all' in args.splits:
        args.splits = ['train', 'dev', 'test']
    
    # 根據命令調用相應的處理函數
    if args.command == 'download':
        return download_command(args)
    elif args.command == 'info':
        return info_command(args)
    elif args.command == 'sample':
        return sample_command(args)
    elif args.command == 'convert':
        return convert_command(args)
    elif args.command == 'test-db':
        return test_db_command(args)
    elif args.command == 'query':
        return query_command(args)
    else:
        print("請指定子命令。使用 -h 或 --help 查看幫助。", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
