#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
對 schema_loader 模組的測試。
"""

import os
import json
import pytest
import sqlite3
import tempfile
from pathlib import Path

# 導入被測試的模組
from src.schema_loader.loader import SchemaLoader, load_schema


@pytest.fixture
def test_db_path():
    """創建臨時測試資料庫的 fixture。"""
    # 創建臨時文件
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
        db_path = tmp.name
    
    # 連接到臨時數據庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 創建測試表
    cursor.executescript('''
    -- 創建 users 表
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        country TEXT
    );
    
    -- 創建 orders 表
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        order_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # 清理：測試結束後刪除臨時資料庫
    os.unlink(db_path)


class TestSchemaLoader:
    """SchemaLoader 類別的測試案例。"""
    
    def test_initialization(self, test_db_path):
        """測試 SchemaLoader 的初始化。"""
        loader = SchemaLoader(test_db_path)
        assert loader.db_path == test_db_path
        assert loader.conn is None
    
    def test_context_manager(self, test_db_path):
        """測試上下文管理器功能。"""
        with SchemaLoader(test_db_path) as loader:
            assert loader.conn is not None
        # 上下文退出後，連接應該已關閉
        # sqlite3.Connection 沒有 closed 屬性，所以我們需要嘗試執行一個操作來驗證連接是否已關閉
        try:
            loader.conn.execute("SELECT 1")
            # 如果能執行，說明連接還沒關閉，應該失敗
            assert False, "連接應該已關閉，但仍然可以執行操作"
        except sqlite3.ProgrammingError:
            # 捕獲到 ProgrammingError 表示連接已關閉，這是預期行為
            pass
    
    def test_get_tables(self, test_db_path):
        """測試獲取表清單的功能。"""
        with SchemaLoader(test_db_path) as loader:
            tables = loader._get_tables()
            assert isinstance(tables, list)
            assert set(tables) == {'users', 'orders'}
    
    def test_get_columns(self, test_db_path):
        """測試獲取列資訊的功能。"""
        with SchemaLoader(test_db_path) as loader:
            # 測試 users 表的列
            columns = loader._get_columns('users')
            assert len(columns) == 4
            
            # 檢查第一列是否為 id，且是主鍵
            assert columns[0]['name'] == 'id'
            assert columns[0]['is_primary_key'] is True
            
            # 檢查 name 欄位是否是 NOT NULL
            name_col = next(col for col in columns if col['name'] == 'name')
            assert name_col['not_null'] is True
    
    def test_get_foreign_keys(self, test_db_path):
        """測試獲取外鍵的功能。"""
        with SchemaLoader(test_db_path) as loader:
            # orders 表應有一個外鍵
            fks = loader._get_foreign_keys('orders')
            assert len(fks) == 1
            
            # 檢查外鍵細節
            assert fks[0]['column'] == 'user_id'
            assert fks[0]['referenced_table'] == 'users'
            assert fks[0]['referenced_column'] == 'id'
            
            # users 表不應有外鍵
            assert not loader._get_foreign_keys('users')
    
    def test_load_schema(self, test_db_path):
        """測試載入完整 schema 的功能。"""
        with SchemaLoader(test_db_path) as loader:
            schema = loader.load_schema()
            
            # 基本結構檢查
            assert 'tables' in schema
            assert len(schema['tables']) == 2
            
            # 檢查表名
            table_names = [t['name'] for t in schema['tables']]
            assert set(table_names) == {'users', 'orders'}
            
            # 找到 orders 表並檢查其外鍵
            orders_table = next(t for t in schema['tables'] if t['name'] == 'orders')
            assert len(orders_table['foreign_keys']) == 1
            assert orders_table['foreign_keys'][0]['column'] == 'user_id'
    
    def test_load_schema_json(self, test_db_path):
        """測試載入 schema 為 JSON 字串的功能。"""
        with SchemaLoader(test_db_path) as loader:
            # 獲取非美化 JSON
            json_str = loader.load_schema_json(pretty=False)
            assert isinstance(json_str, str)
            
            # 應該能夠被解析回 Python 對象
            parsed = json.loads(json_str)
            assert 'tables' in parsed
            
            # 獲取美化 JSON
            pretty_json = loader.load_schema_json(pretty=True)
            assert '\n' in pretty_json  # 美化的 JSON 應包含換行符
    
    def test_save_schema_to_file(self, test_db_path, tmp_path):
        """測試將 schema 保存到檔案的功能。"""
        output_file = tmp_path / "schema.json"
        
        with SchemaLoader(test_db_path) as loader:
            loader.save_schema_to_file(str(output_file))
        
        # 檢查檔案是否存在
        assert output_file.exists()
        
        # 檢查檔案內容
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            parsed = json.loads(content)
            assert 'tables' in parsed
            assert len(parsed['tables']) == 2


def test_load_schema_function(test_db_path, tmp_path):
    """測試便捷函數 load_schema。"""
    # 不指定輸出檔案
    schema = load_schema(test_db_path)
    assert 'tables' in schema
    assert len(schema['tables']) == 2
    
    # 指定輸出檔案
    output_file = tmp_path / "output_schema.json"
    schema = load_schema(test_db_path, str(output_file))
    
    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        parsed = json.loads(content)
        assert 'tables' in parsed
