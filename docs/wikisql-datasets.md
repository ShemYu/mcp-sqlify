# WikiSQL Dataset Usage Guide

This guide provides an overview of the WikiSQL dataset, its structure, and examples of how to load and use it for Text-to-SQL tasks.

---

## 1. What is WikiSQL?

WikiSQL is a large-scale dataset for training and evaluating natural language to SQL translation models. It consists of:

* **24,241** tables extracted from Wikipedia
* **80,654** example pairs of natural language questions and corresponding SQL queries
* **3** splits: `train` (61,297 examples), `dev` (9,145 examples), `test` (10,212 examples)

Key characteristics:

* **Single-table**: Each query references exactly one table
* **SQL complexity**: SELECT with optional aggregation and WHERE clauses (no JOINs)
* **Human-authored**: Natural language questions and queries are written and verified by human annotators

---

## 2. Data Structure

Each example in WikiSQL has the following fields:

| Field Name  | Type   | Description                                                         |
| ----------- | ------ | ------------------------------------------------------------------- |
| `table_id`  | string | Identifier linking to the table schema                              |
| `question`  | string | User’s natural language question                                    |
| `sql`       | object | SQL query components (see below)                                    |
| `sql.query` | string | The full SQL query string                                           |
| `sql.sel`   | int    | Index of the selected column in the table                           |
| `sql.agg`   | int    | Aggregation operator index (0 = NONE, 1 = MAX, 2 = MIN, etc.)       |
| `sql.conds` | list   | List of conditions: each is `[column_index, operator_index, value]` |

Each **table schema** (in `tables.json`) has:

| Field Name | Type   | Description                               |
| ---------- | ------ | ----------------------------------------- |
| `id`       | string | Table identifier                          |
| `header`   | list   | Column names                              |
| `types`    | list   | Column types (e.g., `text`, `real`)       |
| `rows`     | list   | List of rows (each a list of cell values) |

---

## 3. Loading WikiSQL with `datasets`

### 3.1 Installation

```bash
pip install datasets
```

### 3.2 Loading from Hugging Face Hub

```python
from datasets import load_dataset

ds = load_dataset("wikisql")
print(ds)
# DatasetDict({
#   train: Dataset({num_rows: 61297}),
#   validation: Dataset({num_rows: 9145}),
#   test: Dataset({num_rows: 10212})
# })
```

### 3.3 Inspecting Examples

```python
example = ds['train'][0]
print("Question:", example['question'])
print("SQL Query:", example['sql']['human_readable'])
print("Table ID:", example['table_id'])
```

### 3.4 Loading Table Schemas

```python
tables = load_dataset("wikisql", split="train", features="table")
# Alternatively, schemas are in tables.json in the original repo
```

---

## 4. Converting to SQLite for Execution

```python
import sqlite3
from datasets import load_dataset

ds = load_dataset("wikisql")
sample = ds['train'][0]

# Create SQLite DB
db = sqlite3.connect('wikisql.db')
# Create table
enums = sample['table']['header']
cols = sample['table']['header']
dtypes = sample['table']['types']

create_stmt = f"CREATE TABLE {sample['table_id']} (" + ", ".join([
    f'{col} {"TEXT" if typ=="text" else "REAL"}' for col, typ in zip(cols,dtypes)
]) + ");"
db.execute(create_stmt)

# Insert rows
for row in sample['table']['rows']:
    placeholders = ','.join('?' for _ in row)
    db.execute(f"INSERT INTO {sample['table_id']} VALUES ({placeholders})", row)

# Execute the gold SQL
table_id = sample['table_id']
gold_sql = sample['sql']['query'].replace(table_id, sample['table_id'])
print(db.execute(gold_sql).fetchall())
```

---

## 5. Example: Evaluating a Text-to-SQL Model

```python
from datasets import load_dataset
import sqlite3

ds = load_dataset("wikisql", split="validation")

correct = 0
for ex in ds:
    # prepare DB for this example (as above)
    db = sqlite3.connect(f"{ex['table_id']}.db")
    # create and populate table ...

    # inference
    pred_sql = my_text2sql_model(ex['question'], ex['table'])
    try:
        pred_rows = db.execute(pred_sql).fetchall()
        gold_rows = db.execute(ex['sql']['query']).fetchall()
        if pred_rows == gold_rows:
            correct += 1
    except:
        pass

accuracy = correct / len(ds)
print(f"Execution Accuracy: {accuracy:.2%}")
```

---

## 6. Resources

* Original Paper: Zhong et al., "Seq2SQL: Generating Structured Queries from Natural Language using Reinforcement Learning"
* Dataset Repo: [https://github.com/salesforce/WikiSQL](https://github.com/salesforce/WikiSQL)
* Hugging Face Hub: [https://huggingface.co/datasets/wikisql](https://huggingface.co/datasets/wikisql)

---

*Guide last updated: May 4, 2025*
