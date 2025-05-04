在主流 Text-to-SQL 基准（以 WikiSQL 和 Spider 为例）中，最常用的评估指标包括：

1. **Execution Accuracy (ExecAcc)**

   * **定义**：模型生成的 SQL 在执行后，返回的结果集（Row Set）与标注 SQL 的结果集完全一致的样本比例。
   * **公式**：

     $$
       \text{ExecAcc} = \frac{|\{\,i:\; \text{exec}(\widehat{\text{SQL}}_i) = \text{exec}(\text{SQL}^*_i)\}|}{N}
     $$
   * **意义**：最贴近实际应用——只要用户得到的数据正确，就算成功。

2. **Exact Logical Form Match (EM / LF-Match)**

   * **定义**：将生成的 SQL 字符串（去掉格式差异，如空格、大小写）与标注 SQL 完全相同的样本比例。
   * **公式**：

     $$
       \text{EM} = \frac{|\{\,i:\; \text{normalize}(\widehat{\text{SQL}}_i) = \text{normalize}(\text{SQL}^*_i)\}|}{N}
     $$
   * **意义**：衡量模型在“生成正确结构”上的能力，便于对齐语法和逻辑。

3. **Component-Level F1**

   * **定义**：将 SQL 拆分为若干子组件（如 SELECT 列、WHERE 条件、GROUP BY、ORDER BY、聚合函数），分别计算 Precision、Recall，再合并为 F1。
   * **应用**：

     * **SELECT F1**：正确选出的列 / 标注列
     * **WHERE F1**：正确条件对数 / 标注条件总数
     * …
   * **意义**：细粒度诊断模型在哪个子结构上最容易出错。

4. **Schema Linking Accuracy**

   * **定义**：模型在映射自然语言中提到的实体（column/table 名）到实际 schema 中的正确率。
   * **公式**：

     $$
       \text{LinkAcc} = \frac{|\{\,(e,\,\hat{e}):\;\hat{e} \text{正确映射到} e^*\}|}{|\text{总实体数}|}
     $$
   * **意义**：衡量模型对 schema 元素（表名、列名）的定位能力。

---

### WikiSQL vs. Spider

| 基准集         | ExecAcc | LF-Match | Component-F1 | SchemaLink |
| ----------- | :-----: | :------: | :----------: | :--------: |
| **WikiSQL** |    ✓    |     ✓    |    × (可扩展)   |   × (可扩展)  |
| **Spider**  |    ✓    |     ✓    |       ✓      |      ✓     |

* **WikiSQL**：论文中主要报告 Execution Accuracy 与 Exact Match。
* **Spider**：更复杂，通常都会补充 Component-Level F1 和 Schema Linking Accuracy（也称 “Column Prediction Accuracy”）来全面评估跨表与多表查询能力。

---

**推荐实践**：

1. **核心指标**：以 **Execution Accuracy** 为主，确保查询结果正确。
2. **结构对齐**：辅以 **Exact Match**，监控模型生成的一致性。
3. **调试诊断**：引入 **Component-Level F1** 与 **Schema Linking**，快速定位生成逻辑或映射错误。

**WikiSQL原始資料庫位置**

使用 WikiSQL 進行查詢評估時，原始資料庫位於 GitHub 上的 `tables.json` 文件中。這些資料庫定義了表格的結構（schema）及其內容，位於 Salesforce 的 WikiSQL 倉庫（[https://github.com/salesforce/WikiSQL）。此外，資料集的內容也包含在](https://github.com/salesforce/WikiSQL）。此外，資料集的內容也包含在) Hugging Face 上的 dataset 中，但原始的 JSON 檔案仍然來自於 GitHub 的 `data` 資料夾。你可以從那裡下載，包括 `tables.json` 和其他配套檔案。


你可以在官方 Salesforce/WikiSQL GitHub 仓库里的 `data.tar.bz2` 包中直接拿到已经生成好的 SQLite 数据库文件，用来做执行评估。

具体路径（以 clone 下来的 repo 为例）：

```
$ git clone https://github.com/salesforce/WikiSQL
$ cd WikiSQL
$ tar xvjf data.tar.bz2
# 解压后会看到：
data/
├── train.db        # 用于 train split 的 SQLite DB
├── dev.db          # 用于 dev split 的 SQLite DB
└── test.db         # 用于 test split 的 SQLite DB
```

* 这些 `.db` 文件就是你运行 `evaluate.py` 时所使用的原始数据库，里面已经包含了对应分割（train/dev/test）下的所有表结构和数据 ([GitHub][1])。

如果你想要从头生成，也可以先把 `data/tables.json` 和 `data/{train,dev,test}.jsonl` 里的 schema+rows 读取出来，然后用 SQLite API 自行建表并插入，但官方直接提供的 `.db` 最快捷。

[1]: https://github.com/salesforce/WikiSQL?utm_source=chatgpt.com "salesforce/WikiSQL: A large annotated semantic parsing ... - GitHub"
