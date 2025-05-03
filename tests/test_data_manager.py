#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
對 data_manager 模組的測試。
"""

import os
import json
import pytest
import sqlite3
import tempfile
from pathlib import Path

# 導入被測試的模組
from src.data_manager.wikisql_dataset import WikiSQLDataset
from src.data_manager.sqlite_converter import SQLiteConverter, TestDBManager
from src.data_manager.manager import DataManager


@pytest.fixture
def mock_wikisql_data():
    """創建模擬的 WikiSQL 資料"""
    return {
        "question": "有多少項目的交易金額超過 100 元?",
        "table": {
            "header": ["id", "name", "amount", "date"],
            "types": ["number", "text", "real", "text"],
            "rows": [
                ["1", "Alice", "120.5", "2025-04-01"],
                ["2", "Bob", "75.0", "2025-04-02"],
                ["3", "Charlie", "200.0", "2025-04-03"]
            ]
        },
        "sql": {
            "sel": 0,
            "agg": 1,
            "conds": [[2, 0, "100"]],
            "human_readable": "SELECT COUNT(id) FROM table WHERE amount > 100"
        }
    }


@pytest.fixture
def temp_db_path():
    """創建臨時 SQLite 資料庫路徑"""
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # 清理：測試結束後刪除臨時資料庫
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_dataset_dir():
    """創建模擬的資料集目錄"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 創建模擬的 JSONL 文件
        for split in ['train', 'dev', 'test']:
            file_path = os.path.join(temp_dir, f"{split}.jsonl")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # 寫入 5 個模擬的範例
                for i in range(5):
                    example = {
                        "question": f"測試問題 {i+1} for {split}",
                        "table": {
                            "header": ["id", "name", "value"],
                            "types": ["number", "text", "real"],
                            "rows": [
                                [str(j+1), f"Name{j+1}", str((j+1)*10.5)] for j in range(3)
                            ]
                        },
                        "sql": {
                            "sel": 0,
                            "agg": 0,
                            "conds": [[1, 0, "Name1"]],
                            "human_readable": f"SELECT id FROM table WHERE name = 'Name1'"
                        }
                    }
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        yield temp_dir


class TestWikiSQLDataset:
    """WikiSQLDataset 類的測試"""
    
    def test_initialization(self, mock_dataset_dir):
        """測試初始化"""
        dataset = WikiSQLDataset(mock_dataset_dir)
        assert dataset.data_root == mock_dataset_dir
        assert isinstance(dataset.data_cache, dict)
    
    def test_load_split(self, mock_dataset_dir):
        """測試載入資料分割"""
        dataset = WikiSQLDataset(mock_dataset_dir)
        
        # 不指定 limit
        data = dataset.load_split('train')
        assert len(data) == 5
        
        # 指定 limit
        data = dataset.load_split('dev', limit=2)
        assert len(data) == 2
        
        # 檢查快取是否有效
        assert 'dev_2' in dataset.data_cache
        
        # 從快取載入
        data2 = dataset.load_split('dev', limit=2)
        assert data is data2  # 應該是相同的對象
    
    def test_get_example(self, mock_dataset_dir):
        """測試獲取單個範例"""
        dataset = WikiSQLDataset(mock_dataset_dir)
        
        example = dataset.get_example('train', 2)
        assert example['question'] == '測試問題 3 for train'
        
        # 測試索引錯誤
        with pytest.raises(IndexError):
            dataset.get_example('train', 10)  # 超出範圍
    
    def test_get_table_schema(self, mock_wikisql_data):
        """測試獲取表格結構"""
        dataset = WikiSQLDataset()
        schema = dataset.get_table_schema(mock_wikisql_data)
        
        assert schema['header'] == mock_wikisql_data['table']['header']
        assert schema['types'] == mock_wikisql_data['table']['types']
        assert 'name' in schema


class TestSQLiteConverter:
    """SQLiteConverter 類的測試"""
    
    def test_initialization(self, temp_db_path):
        """測試初始化"""
        converter = SQLiteConverter(temp_db_path)
        assert converter.db_path == temp_db_path
        assert converter.conn is None
    
    def test_context_manager(self, temp_db_path):
        """測試上下文管理器功能"""
        with SQLiteConverter(temp_db_path) as converter:
            assert converter.conn is not None
            
        # 確認連接已關閉
        try:
            converter.conn.execute("SELECT 1")
            # 如果不拋出異常，則測試失敗
            assert False, "連接應該已關閉"
        except sqlite3.ProgrammingError:
            # 預期會拋出這個異常
            pass
    
    def test_generate_table_name(self, mock_wikisql_data):
        """測試生成表名"""
        converter = SQLiteConverter()
        table_name = converter.generate_table_name(mock_wikisql_data)
        
        assert isinstance(table_name, str)
        assert table_name.startswith('ex_')
    
    def test_generate_create_table_sql(self, mock_wikisql_data):
        """測試生成 CREATE TABLE SQL"""
        converter = SQLiteConverter()
        table_name = 'test_table'
        sql = converter.generate_create_table_sql(mock_wikisql_data, table_name)
        
        assert 'CREATE TABLE' in sql
        assert table_name in sql
        # 檢查所有列是否都包含在 SQL 中
        for header in mock_wikisql_data['table']['header']:
            assert header in sql
    
    def test_convert_example(self, mock_wikisql_data, temp_db_path):
        """測試轉換單個範例"""
        converter = SQLiteConverter(temp_db_path)
        
        with converter:
            result = converter.convert_example(mock_wikisql_data)
            
            assert 'raw_data' in result
            assert 'sqlite_info' in result
            assert result['raw_data'] is mock_wikisql_data
            
            # 檢查 SQLite 資訊
            assert 'table_name' in result['sqlite_info']
            assert 'create_sql' in result['sqlite_info']
            assert 'sample_query' in result['sqlite_info']
            
            # 執行查詢
            columns, rows = converter.execute_query(result['sqlite_info']['sample_query'])
            assert len(columns) > 0
            assert len(rows) <= 5  # LIMIT 5


class TestDataManager:
    """DataManager 類的測試"""
    
    def test_initialization(self, mock_dataset_dir, temp_db_path):
        """測試初始化"""
        manager = DataManager(mock_dataset_dir, temp_db_path)
        
        assert isinstance(manager.dataset, WikiSQLDataset)
        assert isinstance(manager.converter, SQLiteConverter)
        assert isinstance(manager.test_db_manager, TestDBManager)
    
    def test_load_examples(self, mock_dataset_dir, temp_db_path):
        """測試載入範例"""
        manager = DataManager(mock_dataset_dir, temp_db_path)
        
        # 不轉換為 SQLite
        examples = manager.load_examples('train', limit=2, convert_to_sqlite=False)
        assert len(examples) == 2
        assert all(example['raw_data'] is not None for example in examples)
        assert all(example['sqlite_info'] is None for example in examples)
        
        # 轉換為 SQLite
        examples = manager.load_examples('dev', limit=1, convert_to_sqlite=True)
        assert len(examples) == 1
        assert examples[0]['raw_data'] is not None
        assert examples[0]['sqlite_info'] is not None
    
    def test_get_example_with_conversion(self, mock_dataset_dir, temp_db_path):
        """測試獲取單個範例並轉換"""
        manager = DataManager(mock_dataset_dir, temp_db_path)
        
        example = manager.get_example_with_conversion('train', 0)
        
        assert example['raw_data'] is not None
        assert example['sqlite_info'] is not None
        assert 'table_name' in example['sqlite_info']
    
    def test_create_test_database(self, mock_dataset_dir):
        """測試創建測試資料庫"""
        # 創建臨時測試目錄
        with tempfile.TemporaryDirectory() as temp_test_dir:
            # 設置測試資料庫管理器使用這個臨時目錄
            manager = DataManager(mock_dataset_dir)
            manager.test_db_manager.db_dir = temp_test_dir
            
            # 創建測試資料庫
            db_path = manager.create_test_database('test_db', 'train', 3)
            
            # 檢查資料庫是否存在
            assert os.path.exists(db_path)
            
            # 檢查資料庫是否包含表格
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert len(tables) > 0
            
            # 清理
            conn.close()


if __name__ == "__main__":
    pytest.main(["-v"])
