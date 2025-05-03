#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema Loader 模組實現。

從 SQLite 資料庫讀取 schema 資訊，並將其轉換為標準化 JSON 格式。
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional


class SchemaLoader:
    """
    從 SQLite 資料庫讀取 schema 資訊的類別。
    """
    
    def __init__(self, db_path: str):
        """
        初始化 SchemaLoader 實例。
        
        Args:
            db_path: SQLite 資料庫文件的路徑
        """
        self.db_path = db_path
        self.conn = None
        
    def __enter__(self):
        """上下文管理器進入方法"""
        self.conn = sqlite3.connect(self.db_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出方法"""
        if self.conn:
            self.conn.close()
    
    def _get_tables(self) -> List[str]:
        """
        獲取資料庫中所有表的名稱。
        
        Returns:
            表名稱的清單
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    
    def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        獲取指定表的所有列資訊。
        
        Args:
            table_name: 表名稱
            
        Returns:
            包含列資訊的字典清單
        """
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        
        for col in cursor.fetchall():
            # col 格式: (cid, name, type, notnull, default_value, pk)
            column_info = {
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "is_primary_key": bool(col[5])
            }
            columns.append(column_info)
            
        return columns
    
    def _get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """
        獲取指定表的外鍵資訊。
        
        Args:
            table_name: 表名稱
            
        Returns:
            包含外鍵資訊的字典清單
        """
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = []
        
        for fk in cursor.fetchall():
            # fk 格式: (id, seq, table, from, to, on_update, on_delete, match)
            foreign_key_info = {
                "column": fk[3],
                "referenced_table": fk[2],
                "referenced_column": fk[4]
            }
            foreign_keys.append(foreign_key_info)
            
        return foreign_keys
    
    def load_schema(self) -> Dict[str, Any]:
        """
        載入資料庫 schema 並返回標準化 JSON 格式。
        
        Returns:
            包含 schema 資訊的字典，可直接轉換為 JSON
        """
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
        
        tables = self._get_tables()
        schema = {"tables": []}
        
        for table_name in tables:
            columns = self._get_columns(table_name)
            foreign_keys = self._get_foreign_keys(table_name)
            
            table_info = {
                "name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys
            }
            
            schema["tables"].append(table_info)
        
        return schema
    
    def load_schema_json(self, pretty: bool = False) -> str:
        """
        載入資料庫 schema 並返回 JSON 字串。
        
        Args:
            pretty: 是否美化輸出的 JSON
            
        Returns:
            JSON 字串
        """
        schema = self.load_schema()
        indent = 2 if pretty else None
        return json.dumps(schema, ensure_ascii=False, indent=indent)
    
    def save_schema_to_file(self, output_path: str, pretty: bool = True) -> None:
        """
        將資料庫 schema 保存到 JSON 檔案。
        
        Args:
            output_path: 輸出檔案路徑
            pretty: 是否美化輸出的 JSON
        """
        json_schema = self.load_schema_json(pretty)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_schema)


def load_schema(db_path: str, output_path: Optional[str] = None, pretty: bool = True) -> Dict[str, Any]:
    """
    從 SQLite 資料庫載入 schema 的便捷函數。
    
    Args:
        db_path: SQLite 資料庫檔案的路徑
        output_path: 可選的輸出 JSON 檔案路徑
        pretty: 是否美化輸出的 JSON
        
    Returns:
        包含 schema 資訊的字典
    """
    with SchemaLoader(db_path) as loader:
        schema = loader.load_schema()
        
        if output_path:
            loader.save_schema_to_file(output_path, pretty)
            
    return schema
