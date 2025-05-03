#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Converter 模組。

負責將 WikiSQL 表格資料轉換為 SQLite 資料庫格式。
"""

import os
import json
import sqlite3
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteConverter:
    """
    將 WikiSQL 資料集轉換為 SQLite 資料庫。
    """
    
    # WikiSQL 類型到 SQLite 類型的映射
    TYPE_MAP = {
        'text': 'TEXT',
        'number': 'INTEGER',
        'real': 'REAL',
        'date': 'TEXT'  # SQLite 沒有專用的日期類型
    }
    
    def __init__(self, db_path: str = None):
        """
        初始化 SQLiteConverter 實例。
        
        Args:
            db_path: SQLite 資料庫檔案的路徑，若不指定則使用預設路徑
        """
        if db_path is None:
            # 假設運行於專案根目錄
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(current_dir, 'data', 'wikisql_samples.sqlite')
        else:
            self.db_path = db_path
            
        # 確保目錄存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 連接到資料庫
        self.conn = None
    
    def __enter__(self):
        """上下文管理器進入方法"""
        self.conn = sqlite3.connect(self.db_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出方法"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _connect_if_needed(self):
        """如果需要，建立資料庫連接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
    
    def _get_sql_type(self, wikisql_type: str) -> str:
        """
        將 WikiSQL 類型轉換為 SQLite 類型。
        
        Args:
            wikisql_type: WikiSQL 中的資料類型
            
        Returns:
            對應的 SQLite 資料類型
        """
        return self.TYPE_MAP.get(wikisql_type.lower(), 'TEXT')
    
    def generate_table_name(self, example: Dict[str, Any]) -> str:
        """
        為範例生成唯一的表名。
        
        Args:
            example: WikiSQL 範例
            
        Returns:
            表名
        """
        # 使用表頭和前幾個關鍵詞生成表名
        headers = example['table']['header']
        keywords = example['question'].split()[:3]
        
        # 創建基本表名
        base_name = f"ex_{abs(hash(tuple(headers) + tuple(keywords))) % 10000}"
        
        return base_name
    
    def generate_create_table_sql(self, example: Dict[str, Any], table_name: str) -> str:
        """
        生成創建表格的 SQL 語句。
        
        Args:
            example: WikiSQL 範例
            table_name: 表名
            
        Returns:
            CREATE TABLE SQL 語句
        """
        headers = example['table']['header']
        types = example['table']['types']
        
        # 生成列定義
        columns = []
        for i, (header, col_type) in enumerate(zip(headers, types)):
            sql_type = self._get_sql_type(col_type)
            
            # 設置第一列為主鍵（如果是數字類型）
            if i == 0 and col_type.lower() == 'number':
                columns.append(f'"{header}" {sql_type} PRIMARY KEY')
            else:
                columns.append(f'"{header}" {sql_type}')
        
        # 生成完整 CREATE TABLE 語句
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n  '
        create_sql += ',\n  '.join(columns)
        create_sql += '\n);'
        
        return create_sql
    
    def generate_insert_sql(self, example: Dict[str, Any], table_name: str) -> List[str]:
        """
        生成插入資料的 SQL 語句。
        
        Args:
            example: WikiSQL 範例
            table_name: 表名
            
        Returns:
            INSERT INTO SQL 語句列表
        """
        headers = example['table']['header']
        rows = example['table']['rows']
        
        insert_statements = []
        
        for row in rows:
            # 準備值，正確處理引號
            values = []
            for value in row:
                if isinstance(value, str):
                    # 字串需要轉譯單引號並包裹在單引號中
                    values.append(f"'{value.replace("'", "''")}'")
                elif value is None:
                    values.append('NULL')
                else:
                    values.append(str(value))
            
            # 生成 INSERT 語句
            headers_str = ', '.join(f'"{h}"' for h in headers)
            values_str = ', '.join(values)
            
            insert_sql = f'INSERT INTO "{table_name}" ({headers_str}) VALUES ({values_str});'
            insert_statements.append(insert_sql)
        
        return insert_statements
    
    def convert_example(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        將單個 WikiSQL 範例轉換為 SQLite 表格。
        
        Args:
            example: WikiSQL 範例
            
        Returns:
            包含轉換資訊的字典
        """
        self._connect_if_needed()
        
        # 生成表名和 SQL 語句
        table_name = self.generate_table_name(example)
        create_sql = self.generate_create_table_sql(example, table_name)
        insert_sqls = self.generate_insert_sql(example, table_name)
        
        # 執行 SQL 語句
        cursor = self.conn.cursor()
        
        # 先檢查表是否已存在，如果存在則刪除
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}";')
        
        # 創建表並插入資料
        cursor.execute(create_sql)
        for insert_sql in insert_sqls:
            cursor.execute(insert_sql)
        
        # 提交更改
        self.conn.commit()
        
        # 生成範例查詢
        question = example['question']
        headers = example['table']['header']
        
        sample_query = f'SELECT * FROM "{table_name}" LIMIT 5;'
        
        # 為 SQL 生成對應的 SQL 查詢（如果人類可讀 SQL 可用）
        target_sql = None
        if 'human_readable' in example['sql']:
            raw_sql = example['sql']['human_readable']
            # 將通用表名替換為我們的表名
            target_sql = raw_sql.replace('table', table_name)
        
        # 返回轉換結果
        return {
            'raw_data': example,
            'sqlite_info': {
                'table_name': table_name,
                'db_path': self.db_path,
                'create_sql': create_sql,
                'sample_query': sample_query,
                'target_sql': target_sql
            }
        }
    
    def convert_examples(self, examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        將多個 WikiSQL 範例轉換為 SQLite 表格。
        
        Args:
            examples: WikiSQL 範例列表
            
        Returns:
            每個範例的轉換結果列表
        """
        results = []
        
        for example in examples:
            result = self.convert_example(example)
            results.append(result)
        
        return results
    
    def execute_query(self, query: str) -> Tuple[List[str], List[List[Any]]]:
        """
        執行 SQL 查詢並返回結果。
        
        Args:
            query: SQL 查詢
            
        Returns:
            列名和結果行的元組
        """
        self._connect_if_needed()
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        # 獲取列名
        columns = [desc[0] for desc in cursor.description]
        
        # 獲取所有行
        rows = cursor.fetchall()
        
        return columns, rows


class TestDBManager:
    """
    管理測試用 SQLite 資料庫。
    """
    
    def __init__(self, db_dir: str = None):
        """
        初始化 TestDBManager 實例。
        
        Args:
            db_dir: 資料庫檔案的目錄路徑，若不指定則使用預設路徑
        """
        if db_dir is None:
            # 假設運行於專案根目錄
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_dir = os.path.join(current_dir, 'data', 'test_dbs')
        else:
            self.db_dir = db_dir
            
        # 確保目錄存在
        os.makedirs(self.db_dir, exist_ok=True)
    
    def create_test_db(self, test_name: str, examples: List[Dict[str, Any]]) -> str:
        """
        創建測試用資料庫。
        
        Args:
            test_name: 測試名稱，用於生成資料庫檔案名
            examples: WikiSQL 範例列表
            
        Returns:
            創建的資料庫檔案路徑
        """
        # 生成資料庫檔案路徑
        db_path = os.path.join(self.db_dir, f"{test_name}.sqlite")
        
        # 使用 SQLiteConverter 將範例轉換為 SQLite 表格
        with SQLiteConverter(db_path) as converter:
            converter.convert_examples(examples)
        
        return db_path
    
    def clear_test_dbs(self):
        """清除所有測試用資料庫"""
        for filename in os.listdir(self.db_dir):
            if filename.endswith('.sqlite'):
                file_path = os.path.join(self.db_dir, filename)
                os.remove(file_path)
                logger.info(f"已刪除測試資料庫: {file_path}")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 示範使用
    from wikisql_dataset import WikiSQLDataset
    
    # 載入一些範例
    dataset = WikiSQLDataset()
    examples = dataset.load_split('dev', limit=5)
    
    # 轉換為 SQLite
    with SQLiteConverter() as converter:
        results = converter.convert_examples(examples)
        
        for i, result in enumerate(results):
            print(f"\n轉換範例 {i+1}:")
            print(f"問題: {result['raw_data']['question']}")
            print(f"表名: {result['sqlite_info']['table_name']}")
            print(f"建表 SQL: \n{result['sqlite_info']['create_sql']}")
            
            # 執行查詢範例
            query = result['sqlite_info']['sample_query']
            print(f"執行查詢: {query}")
            columns, rows = converter.execute_query(query)
            
            print(f"列: {columns}")
            for row in rows[:3]:  # 只顯示前 3 行
                print(row)
            
            # 如果有目標 SQL，嘗試執行
            if result['sqlite_info']['target_sql']:
                target_sql = result['sqlite_info']['target_sql']
                print(f"目標 SQL: {target_sql}")
                try:
                    columns, rows = converter.execute_query(target_sql)
                    print(f"結果: {len(rows)} 行")
                except Exception as e:
                    print(f"執行目標 SQL 失敗: {str(e)}")
