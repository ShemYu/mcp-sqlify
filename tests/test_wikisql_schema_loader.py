#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 WikiSQL Schema Loader 功能。
"""

import os
import json
import pytest
from src.schema_loader.wikisql_loader import WikiSQLSchemaLoader, load_schema_from_wikisql
from src.data_manager.wikisql_dataset import WikiSQLDataset


class TestWikiSQLSchemaLoader:
    """測試 WikiSQL Schema Loader 功能的測試類"""
    
    @pytest.fixture
    def sample_wikisql_example(self):
        """提供一個樣例 WikiSQL 資料"""
        sample = {
            "question": "What is the format for South Australia?",
            "table": {
                "header": ["State/territory", "Text/background colour", "Format", "Current slogan", "Current series", "Notes"],
                "types": ["text", "text", "text", "text", "text", "text"],
                "rows": [
                    ["Australian Capital Territory", "blue/white", "Yaa-000", "Feel the power", "YZZ-00A", ""],
                    ["New South Wales", "black/yellow", "aa-00-aa", "NEW SOUTH WALES", "DEF-12W", "NSW"],
                    ["South Australia", "black/white", "S00-AAA", "SOUTH AUSTRALIA", "S000-AZ", ""]
                ]
            },
            "sql": {
                "table_id": "sample_table",
                "human_readable": "SELECT Format FROM table WHERE State/territory = South Australia"
            }
        }
        return sample
    
    def test_init_without_example(self):
        """測試無範例初始化"""
        loader = WikiSQLSchemaLoader()
        assert loader.example is None
    
    def test_init_with_example(self, sample_wikisql_example):
        """測試帶範例初始化"""
        loader = WikiSQLSchemaLoader(sample_wikisql_example)
        assert loader.example == sample_wikisql_example
    
    def test_load_schema_from_example(self, sample_wikisql_example):
        """測試從範例載入 schema"""
        loader = WikiSQLSchemaLoader()
        schema = loader.load_schema_from_example(sample_wikisql_example)
        
        # 驗證結果
        assert isinstance(schema, dict)
        assert "tables" in schema
        assert len(schema["tables"]) == 1
        
        table = schema["tables"][0]
        assert table["name"] == "sample_table"
        assert len(table["columns"]) == 6
        
        # 檢查列名
        column_names = [col["name"] for col in table["columns"]]
        expected_names = sample_wikisql_example["table"]["header"]
        assert column_names == expected_names
        
        # 檢查列類型
        column_types = [col["type"] for col in table["columns"]]
        assert all(t in ["TEXT", "INTEGER", "REAL"] for t in column_types)
    
    def test_load_schema_without_example(self):
        """測試在沒有提供範例的情況下載入 schema"""
        loader = WikiSQLSchemaLoader()
        with pytest.raises(ValueError, match="尚未提供 WikiSQL 資料範例"):
            loader.load_schema()
    
    def test_load_schema_json(self, sample_wikisql_example):
        """測試 JSON 格式輸出"""
        loader = WikiSQLSchemaLoader(sample_wikisql_example)
        json_str = loader.load_schema_json(pretty=True)
        
        # 驗證 JSON 格式
        schema = json.loads(json_str)
        assert isinstance(schema, dict)
        assert "tables" in schema
    
    def test_save_schema_to_file(self, sample_wikisql_example, tmp_path):
        """測試保存 schema 到文件"""
        output_path = os.path.join(tmp_path, "test_schema.json")
        loader = WikiSQLSchemaLoader(sample_wikisql_example)
        loader.save_schema_to_file(output_path)
        
        # 驗證文件存在並包含有效 JSON
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        assert isinstance(schema, dict)
        assert "tables" in schema
    
    def test_convenience_function(self, sample_wikisql_example, tmp_path):
        """測試便捷函數"""
        output_path = os.path.join(tmp_path, "test_schema2.json")
        schema = load_schema_from_wikisql(sample_wikisql_example, output_path)
        
        # 驗證結果
        assert isinstance(schema, dict)
        assert "tables" in schema
        assert os.path.exists(output_path)


@pytest.mark.integration
class TestIntegrationWithWikiSQLDataset:
    """與 WikiSQLDataset 集成的測試類"""
    
    @pytest.fixture(scope="class")
    def wikisql_dataset(self):
        """提供 WikiSQLDataset 實例"""
        dataset = WikiSQLDataset()
        return dataset
    
    def test_load_schema_from_real_example(self, wikisql_dataset):
        """測試從真實 WikiSQL 資料載入 schema"""
        # 載入一個樣例
        examples = wikisql_dataset.load_split("train", limit=1)
        assert len(examples) == 1
        
        # 從樣例載入 schema
        loader = WikiSQLSchemaLoader()
        schema = loader.load_schema_from_example(examples[0])
        
        # 驗證結果
        assert isinstance(schema, dict)
        assert "tables" in schema
        assert len(schema["tables"]) == 1
        
        # 打印一些詳細資訊以便檢查
        print("\nSchema from real WikiSQL example:")
        table = schema["tables"][0]
        print(f"Table name: {table['name']}")
        print(f"Columns: {', '.join(col['name'] for col in table['columns'])}")
