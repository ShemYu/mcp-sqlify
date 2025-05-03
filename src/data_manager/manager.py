#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Manager 主模組。

整合 WikiSQL 資料集管理與 SQLite 轉換功能，提供統一介面。
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple

from .wikisql_dataset import WikiSQLDataset
from .sqlite_converter import SQLiteConverter, TestDBManager


logger = logging.getLogger(__name__)


class DataManager:
    """
    資料管理器主類。
    
    整合 WikiSQL 資料集管理與 SQLite 轉換功能，提供統一介面。
    """
    
    def __init__(self, data_root: str = None, db_path: str = None):
        """
        初始化 DataManager 實例。
        
        Args:
            data_root: WikiSQL 資料存儲的根目錄
            db_path: SQLite 資料庫檔案的路徑
        """
        self.dataset = WikiSQLDataset(data_root)
        self.converter = SQLiteConverter(db_path)
        self.test_db_manager = TestDBManager()
    
    def load_examples(self, split: str, limit: Optional[int] = None, convert_to_sqlite: bool = False) -> List[Dict[str, Any]]:
        """
        載入範例並可選轉換為 SQLite 格式。
        
        Args:
            split: 資料分割，可為 'train', 'dev', 或 'test'
            limit: 可選的資料數量限制
            convert_to_sqlite: 是否轉換為 SQLite 格式
            
        Returns:
            範例列表，包含原始資料和可選的 SQLite 資訊
        """
        # 載入 WikiSQL 範例
        examples = self.dataset.load_split(split, limit)
        
        # 如果需要，轉換為 SQLite 格式
        if convert_to_sqlite:
            with self.converter:
                return self.converter.convert_examples(examples)
        
        # 否則，包裝到標準格式中
        return [{'raw_data': example, 'sqlite_info': None} for example in examples]
    
    def get_example_with_conversion(self, split: str, index: int) -> Dict[str, Any]:
        """
        獲取單個範例並轉換為 SQLite 格式。
        
        Args:
            split: 資料分割
            index: 範例索引
            
        Returns:
            包含原始資料和 SQLite 資訊的字典
        """
        # 獲取原始範例
        example = self.dataset.get_example(split, index)
        
        # 轉換為 SQLite 格式
        with self.converter:
            return self.converter.convert_example(example)
    
    def create_test_database(self, test_name: str, split: str = 'dev', limit: int = 10) -> str:
        """
        創建測試用資料庫。
        
        Args:
            test_name: 測試名稱
            split: 使用的資料分割
            limit: 資料數量限制
            
        Returns:
            創建的資料庫檔案路徑
        """
        # 載入範例
        examples = self.dataset.load_split(split, limit)
        
        # 創建測試資料庫
        return self.test_db_manager.create_test_db(test_name, examples)
    
    def execute_query(self, db_path: str, query: str) -> Tuple[List[str], List[List[Any]]]:
        """
        在指定資料庫上執行查詢。
        
        Args:
            db_path: 資料庫路徑
            query: SQL 查詢
            
        Returns:
            列名和結果行的元組
        """
        with SQLiteConverter(db_path) as converter:
            return converter.execute_query(query)
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """
        獲取資料集資訊。
        
        Returns:
            資料集資訊字典
        """
        # 獲取分割資訊
        splits_info = self.dataset.get_splits_info()
        
        # 資料庫資訊
        db_info = {
            'default_db_path': self.converter.db_path,
            'test_db_dir': self.test_db_manager.db_dir
        }
        
        return {
            'splits': splits_info,
            'database': db_info
        }


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 示範使用
    data_manager = DataManager()
    
    # 獲取資料集資訊
    info = data_manager.get_dataset_info()
    print("資料集資訊:")
    print(info)
    
    # 載入少量範例並轉換
    print("\n載入並轉換 3 個驗證集範例:")
    examples = data_manager.load_examples('dev', limit=3, convert_to_sqlite=True)
    
    for i, example in enumerate(examples):
        print(f"\n範例 {i+1}:")
        print(f"問題: {example['raw_data']['question']}")
        print(f"表名: {example['sqlite_info']['table_name']}")
        
    # 創建測試資料庫
    print("\n創建測試資料庫:")
    db_path = data_manager.create_test_database('sample_test', limit=5)
    print(f"測試資料庫路徑: {db_path}")
    
    # 執行查詢
    if os.path.exists(db_path):
        print("\n在測試資料庫上執行查詢:")
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        columns, rows = data_manager.execute_query(db_path, query)
        print(f"資料庫中的表: {[row[0] for row in rows]}")
