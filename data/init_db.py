#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""初始化 SQLite 資料庫。"""

import os
import sqlite3

def initialize_database():
    """
    從 SQL 檔案創建並初始化 SQLite 資料庫。
    
    Returns:
        str: 資料庫檔案的路徑
    """
    # 獲取當前目錄路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(current_dir, 'init_db.sql')
    db_file = os.path.join(current_dir, 'init_db.sqlite')
    
    # 刪除已存在的資料庫檔案
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # 連接到 SQLite 資料庫
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 讀取 SQL 文件並執行
    with open(sql_file, 'r') as f:
        sql_script = f.read()
    
    # 執行 SQL 腳本
    cursor.executescript(sql_script)
    
    # 提交更改並關閉連接
    conn.commit()
    conn.close()
    
    print(f"資料庫初始化完成: {db_file}")
    return db_file

if __name__ == "__main__":
    initialize_database()
