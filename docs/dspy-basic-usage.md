# `dspy` Usage Guide (Latest Version)

This guide introduces the core features of `dspy`, a lightweight Python library for building data pipelines, transformations, and analyses. It covers installation, key concepts, and rich example usage to help you get started quickly.

---

## 1. Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate  # Windows

# Install dspy
pip install --upgrade dspy
```

Check version:

```bash
python -c "import dspy; print(dspy.__version__)"
```

---

## 2. Core Concepts

* **Pipeline**: A sequence of data processing stages.
* **Transformer**: Stateless operations that transform a DataFrame (e.g., filter, map).
* **Loader**: Read data from various sources (CSV, JSON, SQL).
* **Writer**: Output results to storage (CSV, database).
* **Task**: A named pipeline ready for execution and monitoring.

---

## 3. Basic Pipeline Example

```python
from dspy import Pipeline, CsvLoader, Filter, Map, CsvWriter

# 1. Load data from CSV
loader = CsvLoader(path="data/input.csv")

# 2. Define transformations
filter_age = Filter(lambda df: df[df.age >= 18])
capitalize_name = Map(lambda df: df.assign(name=df.name.str.title()))

# 3. Write output to CSV
writer = CsvWriter(path="data/output.csv")

# 4. Build and run pipeline
pipeline = Pipeline(
    name="adult_users_pipeline",
    stages=[loader, filter_age, capitalize_name, writer]
)
pipeline.run()
```

---

## 4. SQL Integration

```python
from dspy import SqlLoader, SqlWriter

# Load from SQLite
db_url = "sqlite:///data/db.sqlite"
loader = SqlLoader(db_url=db_url, query="SELECT * FROM users")

# Write back filtered data
overwrite_writer = SqlWriter(db_url=db_url, table_name="adult_users", if_exists="replace")

pipeline = Pipeline(
    name="sql_adult_users",
    stages=[loader, Filter(lambda df: df.age >= 18), overwrite_writer]
)
pipeline.run()
```

---

## 5. Configuration & Task Scheduling

```yaml
# config/pipelines.yaml
adult_users_pipeline:
  loader:
    type: CsvLoader
    params:
      path: data/users.csv
  stages:
    - type: Filter
      params:
        function: "lambda df: df[df.purchase_amount > 100]"
    - type: Map
      params:
        function: "lambda df: df.assign(flag='high_value')"
  writer:
    type: CsvWriter
    params:
      path: data/high_value_customers.csv
  schedule: "CRON 0 2 * * *"  # daily at 02:00
```

Load and schedule:

```python
from dspy import TaskManager

tm = TaskManager(config_path="config/pipelines.yaml")
# Execute all pipelines immediately
tm.run_all()
# Start scheduler in background
tm.start_scheduler()
```

---

## 6. Monitoring & Logging

```python
# Enable verbose logging
dspy.configure_logging(level="INFO")

# Inspect pipeline status
status = pipeline.status()
print(status)
# { 'name': 'adult_users_pipeline', 'last_run': '2025-05-01T02:00:00', 'status': 'success' }
```

---

## 7. Advanced Usage

### 7.1 Custom Transformer

```python
from dspy import Transformer

class AddFullName(Transformer):
    def transform(self, df):
        df['full_name'] = df['first_name'] + ' ' + df['last_name']
        return df

pipeline = Pipeline(
    name="user_fullname",
    stages=[CsvLoader("data/users.csv"), AddFullName(), CsvWriter("data/users_full.csv")]
)
pipeline.run()
```

### 7.2 Parallel Processing

```python
pipeline = Pipeline(
    name="parallel_pipeline",
    stages=[loader, filter_age, capitalize_name, writer],
    parallel=True,  # enable parallel stage execution
    num_workers=4
)
pipeline.run()
```

---

## 8. Error Handling

```python
from dspy import PipelineError

try:
    pipeline.run()
except PipelineError as e:
    print(f"Pipeline failed at stage {e.stage}: {e.original_exception}")
```

---

## 9. Resources & References

* Official Documentation: [https://dspy.readthedocs.io](https://dspy.readthedocs.io)
* GitHub: [https://github.com/dspy-org/dspy](https://github.com/dspy-org/dspy)
* Community Slack: [https://dspy.slack.com](https://dspy.slack.com)

---

*Guide last updated on 2025-05-04*
