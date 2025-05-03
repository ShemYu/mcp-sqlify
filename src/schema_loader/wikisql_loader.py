#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WikiSQL Schema Loader 模組實現。

從 WikiSQL 資料集 JSON 格式直接讀取 schema 資訊，並將其轉換為標準化 JSON 格式。
"""

import json
from typing import Dict, List, Any, Optional

class WikiSQLSchemaLoader:
    """
    從 WikiSQL JSON 資料直接讀取 schema 資訊的類別。
    """
    
    def __init__(self, example: Dict[str, Any] = None):
        """
        初始化 WikiSQLSchemaLoader 實例。
        
        Args:
            example: WikiSQL 資料範例，可選，可稍後通過 load_schema_from_example 方法提供
        """
        self.example = example
        
    def load_schema_from_example(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        從 WikiSQL 資料範例讀取並轉換 schema。
        
        Args:
            example: WikiSQL 資料範例
            
        Returns:
            標準化的 schema 字典
        """
        self.example = example
        return self.load_schema()
    
    def _get_column_info(self) -> List[Dict[str, Any]]:
        """
        從 WikiSQL 資料範例中獲取列資訊。
        
        Returns:
            列資訊的字典列表
        """
        if not self.example or 'table' not in self.example:
            raise ValueError("無效的 WikiSQL 資料範例或範例缺少表格資訊")
        
        headers = self.example['table']['header']
        types = self.example['table']['types']
        
        columns = []
        for i, (header, col_type) in enumerate(zip(headers, types)):
            # 將 WikiSQL 類型轉換為 SQLite 類型
            sqlite_type = self._wikisql_type_to_sqlite(col_type)
            
            # 第一列通常作為主鍵 (如果是數字類型)
            is_primary_key = (i == 0 and col_type.lower() == 'number')
            
            column_info = {
                "name": header,
                "type": sqlite_type,
                "not_null": True,  # 在 WikiSQL 中，所有值都被視為非空
                "is_primary_key": is_primary_key
            }
            columns.append(column_info)
            
        return columns
    
    def _wikisql_type_to_sqlite(self, wikisql_type: str) -> str:
        """
        將 WikiSQL 類型轉換為 SQLite 類型。
        
        Args:
            wikisql_type: WikiSQL 中的資料類型
            
        Returns:
            對應的 SQLite 資料類型
        """
        type_map = {
            'text': 'TEXT',
            'number': 'INTEGER',
            'real': 'REAL',
            'date': 'TEXT'  # SQLite 沒有專用的日期類型
        }
        return type_map.get(wikisql_type.lower(), 'TEXT')
    
    def load_schema(self) -> Dict[str, Any]:
        """
        載入 WikiSQL 資料並返回標準化 JSON 格式的 schema。
        
        Returns:
            包含 schema 資訊的字典，可直接轉換為 JSON
            
        Raises:
            ValueError: 如果尚未提供有效的 WikiSQL 資料範例
        """
        if not self.example:
            raise ValueError("尚未提供 WikiSQL 資料範例，請使用 load_schema_from_example 方法")
        
        columns = self._get_column_info()
        
        # 從 WikiSQL 範例中獲取表名，如果沒有則創建一個通用名稱
        table_name = "table"  # WikiSQL 中的默認表名
        if 'sql' in self.example and 'table_id' in self.example['sql']:
            table_name = self.example['sql']['table_id']
        
        # 創建標準化 schema 字典
        schema = {
            "tables": [
                {
                    "name": table_name,
                    "columns": columns,
                    "foreign_keys": []  # WikiSQL 不包含外鍵信息
                }
            ]
        }
        
        return schema
    
    def load_schema_json(self, pretty: bool = False) -> str:
        """
        載入 schema 並返回 JSON 字串。
        
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
        將 schema 保存到 JSON 檔案。
        
        Args:
            output_path: 輸出檔案路徑
            pretty: 是否美化輸出的 JSON
        """
        json_schema = self.load_schema_json(pretty)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_schema)


def load_schema_from_wikisql(example: Dict[str, Any], output_path: Optional[str] = None, pretty: bool = True) -> Dict[str, Any]:
    """
    從 WikiSQL 資料範例載入 schema 的便捷函數。
    
    Args:
        example: WikiSQL 資料範例
        output_path: 可選的輸出 JSON 檔案路徑
        pretty: 是否美化輸出的 JSON
        
    Returns:
        包含 schema 資訊的字典
    """
    loader = WikiSQLSchemaLoader()
    schema = loader.load_schema_from_example(example)
    
    if output_path:
        loader.save_schema_to_file(output_path, pretty)
        
    return schema
