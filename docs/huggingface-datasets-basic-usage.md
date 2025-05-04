# Hugging Face `datasets` Library 使用指南

本指南介紹如何使用 Hugging Face 的 `datasets` 套件進行資料版本控制、下載與基本操作。

---

## 1. 安裝

```bash
pip install --upgrade datasets
```

如果要推送自訂資料集到 Hub：

```bash
pip install --upgrade huggingface_hub
```

````

---

## 2. 載入資料集

### 2.1 從 Hub 載入

```python
from datasets import load_dataset

ds = load_dataset("squad")  # 預設載入最新穩定版本
print(ds)
# DatasetDict({ 'train': ..., 'validation': ... })
````

### 2.2 指定版本／commit

* **透過 `revision`** 參數載入特定 commit、分支或 tag：

```python
# 載入特定 Git commit
ds_old = load_dataset("squad", revision="5b23d1f")

# 載入某個分支或 tag
ds_beta = load_dataset("glue", "mrpc", revision="glue-v2.0")
```

---

## 3. 本地緩存管理

* `datasets` 自動將下載的檔案緩存在 `~/.cache/huggingface/datasets/`
* 如要清除緩存：

```bash
datasets-cli cache info  # 查看緩存路徑與大小
datasets-cli cache remove <dataset>  # 移除特定資料集緩存
```

---

## 4. 資料集瀏覽與轉換

```python
# 查看欄位和範例
ds_train = ds["train"]
print(ds_train.column_names)
print(ds_train[0])

# 轉為 Pandas
import pandas as pd
df = pd.DataFrame(ds_train[:100])

# 篩選條件
filtered = ds_train.filter(lambda x: len(x['question']) > 50)

# map 轉換
def add_len(example):
    example['q_len'] = len(example['question'])
    return example

mapped = ds_train.map(add_len)
```

---

## 5. 自訂資料集與版本推送

### 5.1 建立 `DatasetDict`

```python
from datasets import Dataset, DatasetDict
import pandas as pd

df = pd.read_csv("data/my_data.csv")
my_ds = Dataset.from_pandas(df)
dataset_dict = DatasetDict({"train": my_ds})
```

### 5.2 推送到 Hub

```python
from huggingface_hub import HfApi, Repository

# 登入
from huggingface_hub import login
login(token="YOUR_TOKEN")

# 推送程式
repository_id = "username/my-dataset"
repo = Repository(local_dir="./my-dataset", clone_from=repository_id)

# 儲存資料與推送
dataset_dict.push_to_hub(repository_id, token="YOUR_TOKEN")
```

* 推送後可在 Hub 網頁上看到版本歷史、Diff 和 commit logs。

---

## 6. 進階功能

* **Streaming**：處理超大資料集時可用

```python
stream_ds = load_dataset("big_dataset", streaming=True)
for example in stream_ds["train"]:
    process(example)
```

* **Shard**：分片加快下載

```python
ds_shard = load_dataset("common_voice", "en", split="train", num_shards=4, shard_index=0)
```

* **Data Versioning**：在推送之前，可用 Git 操作版本控制檔案

---

## 7. 小結

1. 安裝並使用 `load_dataset` 載入 Hub 上的資料集，可指定 `revision` 控制版本。
2. 本地自動緩存，可透過 CLI 工具管理。
3. 支援 `filter`、`map`、`to_pandas` 等常見轉換。
4. 建立自訂 `DatasetDict`，並使用 `push_to_hub` 推送與版本控管。
5. 進階可用 `streaming`、`sharding` 等功能處理大規模資料。

更多細節請參考官方文件：[https://huggingface.co/docs/datasets/index](https://huggingface.co/docs/datasets/index)
