# DSPy Usage Guide (Latest Version)

This guide walks you through the core functionality of DSPy (Declarative Self-improving Python), from installation to advanced usage, using the latest API patterns.

---

## 1. Installation & Configuration

```bash
# Install DSPy
pip install --upgrade dspy
```

Authenticate your LLM provider before use (examples below). DSPy supports OpenAI, Anthropic, Databricks, Ollama, and any OpenAI-compatible endpoint. ([dspy.ai](https://dspy.ai/))

```python
import dspy
# OpenAI GPT-4o-mini
lm = dspy.LM('openai/gpt-4o-mini', api_key='YOUR_OPENAI_API_KEY')
# or Anthropic Claude
# lm = dspy.LM('anthropic/claude-3-opus-20240229', api_key='YOUR_ANTHROPIC_API_KEY')
# or Databricks Meta Llama
# lm = dspy.LM('databricks/databricks-meta-llama-3-1-70b-instruct')

# Configure global LLM
dspy.configure(lm=lm)
```

---

## 2. Calling the LLM Directly

Even without modules, you can use the configured `lm`:

````python
# Simple completion
print(lm("Summarize the plot of Hamlet in one sentence."))
# Chat-style
en = lm(messages=[{"role": "user", "content": "Hello!"}])
print(en)
``` ([dspy.ai](https://dspy.ai/))

---

## 3. Modules: Declarative AI Components

DSPy modules let you express tasks as type-checked signatures.

### 3.1 Predict (Simple Inference)

```python
from dspy import Signature, InputField, OutputField, Predict
from typing import Literal

class Sentiment(Signature):
    text: str = InputField()
    sentiment: Literal['positive','negative','neutral'] = OutputField()

predictor = Predict(Sentiment)
res = predictor(text="This movie was fantastic!")
print(res.sentiment)  # e.g., 'positive'
``` ([dspy.ai](https://dspy.ai/))

### 3.2 ChainOfThought (Step-by-step reasoning)

```python
from dspy import ChainOfThought

cot = ChainOfThought("question -> answer: float")
ans = cot(question="What is the probability of rolling two sixes with two dice?")
print(ans.reasoning)
``` ([dspy.ai](https://dspy.ai/))

### 3.3 ReAct (Reason+Action agents)

```python
from dspy import ReAct, PythonInterpreter, ColBERTv2

# Define tool functions
def calc(expr: str):
    return PythonInterpreter({})(expr)

def wiki(query: str):
    docs = ColBERTv2(url='http://localhost:2017/wiki')(query, k=3)
    return [d['text'] for d in docs]

agent = ReAct(
    "question -> answer: str",
    tools=[calc, wiki]
)
out = agent(question="What year did DSPy launch? Do the research if needed.")
print(out.answer)
``` ([dspy.ai](https://dspy.ai/))

---

## 4. Evaluation Utilities

DSPy offers built-in evaluators for exact match, semantic F1, and composite tasks.

```python
from dspy import Evaluate, answer_exact_match, SemanticF1

eval_chain = Evaluate(
    signature=Sentiment,
    evaluator=answer_exact_match
)
# or semantic match
eval_f1 = Evaluate(signature=Sentiment, evaluator=SemanticF1)
``` ([dspy.ai](https://dspy.ai/))

---

## 5. Persistence: Saving & Loading Modules

```python
# Save a fine-tuned module
predictor.save('sentiment-module')
# Load later
from dspy import load
predictor2 = load('sentiment-module')
``` ([dspy.ai](https://dspy.ai/))

---

## 6. Deployment & Observability

- **MCP Integration**: Use `dspy.MCP` to embed modules into production pipelines. ([dspy.ai](https://dspy.ai/))
- **Logging**: Enable detailed logs:
  ```python
dspy.enable_logging()
````

* **Debugging**: Wrap calls with `dspy.StreamListener()` to trace intermediate steps.

---

## 7. Further Resources

* **API Reference**: [https://dspy.ai/docs/api](https://dspy.ai/docs/api)
* **GitHub Repo**: [https://github.com/stanfordnlp/dspy](https://github.com/stanfordnlp/dspy)
* **Tutorials**: [https://dspy.ai/tutorials](https://dspy.ai/tutorials)

*Guide last updated May 4, 2025*
