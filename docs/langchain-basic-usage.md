# LangChain 使用指南 (最新版本)

本指南涵蓋最新版本的 LangChain 核心概念、安裝方法、範例用法及常見 use case。透過豐富的程式碼範例，快速上手 LangChain 的 Chain、Agent、Memory、Document Loaders、Vectorstores 等功能。

---

## 1. 安裝與快速起步

```bash

# 安裝最新 LangChain
uv pip install --upgrade langchain
## or
uv add langchain
# 若使用 OpenAI
uv pip install openai
## or
uv add openai
```

設定環境變數（以 OpenAI 為例）

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

---

## 2. 核心概念

* **LLM**: 對接大型語言模型 (e.g., OpenAI, Azure, Anthropic)。
* **PromptTemplate**: 將輸入綁定到 prompt 模板。
* **Chain**: 把多個步驟串成 pipeline。
* **Agent**: 具備決策能力，可動態調用工具。
* **Memory**: 會話或任務上下文記憶機制。
* **Document Loader & Vectorstore**: 加載文件並建立嵌入檢索。

---

## 3. 基本用法：Prompt + LLM

```python
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI

# 1. 定義 Prompt 模板
template = "Translate the following English text to French: {text}"
prompt = PromptTemplate(input_variables=["text"], template=template)

# 2. 初始化 LLM
llm = OpenAI(temperature=0)

# 3. 建立 Chain
chain = LLMChain(llm=llm, prompt=prompt)

# 4. 執行
res = chain.run({"text": "Hello world"})
print(res)  # "Bonjour le monde"
```

---

## 4. Chains 範例

### 4.1 串接多步驟 Chain (Sequential Chain)

```python
from langchain import SequentialChain
# 步驟 1: 生成創意產品名稱
step1 = LLMChain(
    llm=OpenAI(temperature=0.7),
    prompt=PromptTemplate(
        input_variables=["industry"],
        template="Generate a creative product name for a {industry} company"
    )
)
# 步驟 2: 為產品名稱生成口號
step2 = LLMChain(
    llm=OpenAI(temperature=0.7),
    prompt=PromptTemplate(
        input_variables=["product_name"],
        template="Write a catchy slogan for {product_name}"
    )
)

seq_chain = SequentialChain(
    chains=[step1, step2],
    input_variables=["industry"],
    output_variables=["product_name", "slogan"]
)

res = seq_chain.run({"industry": "tech"})
print(res)
```

### 4.2 Router Chain (多路分發)

```python
from langchain.chains.router import MultiPromptChain, RouterChain
# 定義多條子 chain...
# ...略
# 使用 RouterChain 根據輸入自動選擇
```

---

## 5. Agents 範例

LangChain Agent 可根據工具列表動態決策。

```python
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from langchain.tools import SerpAPIWrapper

# 1. 定義工具
search = SerpAPIWrapper()
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="Useful for searching the web"
    ),
]

# 2. 初始化 Agent
agent = initialize_agent(
    tools,
    llm=OpenAI(temperature=0),
    agent="zero-shot-react-description",
    verbose=True
)

# 3. 使用 Agent
res = agent.run("What's the capital of France and what's the weather there?")
print(res)
```

---

## 6. Memory 範例

### 6.1 會話記憶 (ConversationBufferMemory)

```python
from langchain.memory import ConversationBufferMemory
from langchain import ConversationChain

memory = ConversationBufferMemory()
chain = ConversationChain(llm=OpenAI(temperature=0), memory=memory)

print(chain.predict(input="Hi, who are you?"))
print(chain.predict(input="What did I just ask?"))  # 記憶你上一句
```

### 6.2 自訂記憶 (Custom Memory)

```python
# 可以透過 inherits 自定義 Memory 類型
```

---

## 7. 文件加載與 Vectorstore

### 7.1 加載本地文件

```python
from langchain.document_loaders import TextLoader
loader = TextLoader("./docs/guide.txt")
docs = loader.load()
```

### 7.2 建立嵌入與檢索

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

emb = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(docs, embedding=emb)

# 相似度檢索
results = vectorstore.similarity_search("What is natural language processing?", k=2)
print(results)
```

---

## 8. Text-to-SQL 範例 (最新 use case)

LangChain 提供 `create_sql_agent` 方便快速啟用 SQL Agent：

```python
from langchain_experimental.sql import create_sql_agent
from langchain_experimental.sql import SQLDatabase
from langchain.llms import OpenAI

# 1. 設定資料庫連線
db = SQLDatabase.from_uri("sqlite:///data/init_db.sqlite")
# 2. 建立 SQL Agent
agent = create_sql_agent(
    llm=OpenAI(temperature=0),
    db=db,
    verbose=True
)
# 3. 執行自然語言查詢
res = agent.run("List all users from Taiwan and their total order amount.")
print(res)
```

---

## 9. 部署與注意事項

* **版本鎖定**：請確認 `langchain`、`openai` 等套件版本一致。
* **API Rate Limit**：使用 LLM 或外部工具時，注意呼叫頻率。
* **環境變數管理**：敏感資訊請放在 `.env`。
* **測試**：善用 LangChain 的 Mocking 工具測試 Agent 決策流程。

---

## 10. 進階資源

* 官方文件：[https://python.langchain.com/docs/](https://python.langchain.com/docs/)
* GitHub Repo：[https://github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain)
* 社群討論：LangChain Discord / Stack Overflow
