# mcp-sqlify

## 1. 專案概述

透過一個小型 SQLite 資料庫與 Python 為例，實作從自然語句到 SQL 查詢的完整流程，包含：

1. 使用者輸入自然語句
2. 前處理 & intent 檢測
3. Schema 載入
4. SQL 生成 (Seq2Seq or LLM few-shot)
5. SQL 執行 & 回傳結果

## 2. 測試用資料庫

### 2.1 資料庫選型

* SQLite (`data/init_db.sqlite`)：輕量、免安裝，適合示範與單元測試。

### 2.2 Schema 定義 (`data/init_db.sql`)

```sql
-- users table
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  age INTEGER,
  country TEXT
);

-- orders table
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  amount REAL,
  order_date TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.3 Sample Data (`data/sample_data.sql`)

```sql
INSERT INTO users (name, age, country) VALUES
  ('Alice', 30, 'Taiwan'),
  ('Bob', 25, 'USA'),
  ('Charlie', 35, 'UK');

INSERT INTO orders (user_id, amount, order_date) VALUES
  (1, 120.5, '2025-04-01'),
  (2, 75.0, '2025-04-05'),
  (1, 200.0, '2025-04-10');
```

## 3. 專案高階模組架構

```
text2sql_project/
├── data/
│   ├── init_db.sql          # schema + sample data
│   └── init_db.sqlite       # SQLite binary
│
├── src/
│   ├── preprocess/          # 前處理：tokenization、spell-check
│   ├── schema_loader/       # 讀取並序列化 schema
│   ├── nlu/                 # 意圖判斷 & 欄位對應
│   ├── sql_generator/       # Seq2Seq 模型或 LLM prompt
│   ├── executor/            # SQL 執行 & 錯誤回饋
│   └── api/                 # Flask/FastAPI 封裝 HTTP 介面
│
├── tests/                   # 單元測試 & 集成測試
│   ├── test_preprocess.py
│   ├── test_schema_loader.py
│   ├── test_nlu.py
│   ├── test_sql_generator.py
│   └── test_executor.py
│
├── requirements.txt         # 相依套件
└── README.md                # 專案說明
```

## 4. 模組說明

* **preprocess**

  * Tokenization (使用 `spaCy` / `NLTK`)
  * 基礎文字清理 (lowercase、remove stopwords)

* **schema\_loader**

  * 讀取 SQLite PRAGMA schema
  * 輸出 JSON 格式：`{tables: [{name, columns: [{name, type}]}]}`

* **nlu**

  * Intent detection: `SELECT` vs `非查詢`
  * Entity linking: 將自然語詞映射到 table/column

* **sql\_generator**

  * Seq2Seq (T5 Base) 微調模型示範
  * Few-shot Prompt 使用範例
  * Constrained decoding 範例

* **executor**

  * 執行 SQL 並捕捉錯誤
  * 若 syntax error: 回饋給 `sql_generator`
  * 回傳 JSON 結果



## 5. 開發規劃

### 5.1 模組化開發原則

* 每個模組應遵循**單一職責原則**，專注於解決特定問題
* 模組間透過明確定義的介面進行溝通，降低耦合度
* 每個模組皆可獨立開發、測試與驗證
* 採用測試驅動開發 (TDD) 確保功能穩定性

### 5.2 最小模組開發流程

| 模組名稱 | 開發順序 | 輸入/輸出定義 | 獨立驗證方式 |
|---------|--------|------------|------------|
| **schema_loader** | 1 | 輸入：SQLite 檔案路徑<br>輸出：標準化 schema JSON | 使用測試資料庫驗證輸出是否符合預期結構 |
| **preprocess** | 2 | 輸入：自然語句字串<br>輸出：正規化 tokens | 對比多種輸入樣本的正規化結果 |
| **nlu** | 3 | 輸入：正規化 tokens + schema<br>輸出：意圖分類與實體映射 | 使用預設測試集測試識別準確率 |
| **sql_generator** | 4 | 輸入：意圖 + 實體 + schema<br>輸出：SQL 查詢 | 測試生成的 SQL 句法正確性與語義匹配度 |
| **executor** | 5 | 輸入：SQL 查詢<br>輸出：執行結果與錯誤處理 | 使用有效與無效的 SQL 查詢測試執行邏輯 |
| **integration** | 6 | 整合以上所有模組 | 端到端測試完整流程，包含異常處理 |

### 5.3 獨立驗證標準

每個模組應該建立以下測試：

* **單元測試**：覆蓋核心功能與邊界條件
* **模擬測試**：使用 mock 模擬相依模組
* **效能測試**：確保模組在預期資料量下的效能表現
* **異常處理測試**：確保模組能夠優雅地處理各種異常情況

### 5.4 虛擬環境設置

為確保開發環境的一致性與乾淨，本專案使用 UV 和 .venv 進行虛擬環境管理：

#### 使用 UV 安裝相依套件

[UV](https://github.com/astral-sh/uv) 是新一代的 Python 套件安裝與虛擬環境管理工具，速度比 pip 更快：

```bash
# 安裝 UV (如果尚未安裝)
$ curl -LsSf https://astral.sh/uv/install.sh | sh
## or 
$ pip install uv

# 創建虛擬環境
$ uv venv --python 3.12 .venv

# 啟用虛擬環境
$ source .venv/bin/activate  # Unix/MacOS
$ .venv\Scripts\activate    # Windows

# 使用 UV 安裝相依套件
$ uv pip install -r requirements.txt
```

#### 使用傳統 venv 方式

如果偏好使用 Python 內建的 venv：

```bash
# 創建虛擬環境
$ python -m venv .venv

# 啟用虛擬環境
$ source .venv/bin/activate  # Unix/MacOS
$ .venv\Scripts\activate    # Windows

# 安裝相依套件
$ pip install -r requirements.txt
```

#### 開發時注意事項

* 永遠在啟用虛擬環境後進行開發與測試
* 新增相依套件時更新 `requirements.txt`：
  ```bash
  $ uv pip freeze > requirements.txt  # 使用 UV
  $ pip freeze > requirements.txt     # 使用 pip
  ```
* 確保 `.venv/` 資料夾已加入 `.gitignore`，避免將虛擬環境檔案提交至版本控制

### 5.5 迭代開發計劃

1. 建立基礎功能並確保穩定性
2. 針對複雜自然語句優化處理能力
3. 改善 SQL 生成品質與執行效率
4. 增強處理特殊案例的能力
5. 整合完整流程並進行全面測試

---

這份 Markdown 提供了一條完整實踐脈絡與模組化開發規劃，可依此進行獨立開發與驗證，確保每個組件都能達到預期功能，最終整合成一個完整可靠的 text-to-SQL 系統。
