# Text-to-SQL Generation Project

## Goal

Develop a Python module using LangChain that takes a natural language question and a database schema (provided as text) as input, and outputs the corresponding SQL query. The module should *not* require a live database connection for the generation process itself.

## Architecture (Revised)

The project follows a modular design:

1.  **`src/`**: Contains the core source code.
    *   `config.py`: Handles configuration, primarily loading the OpenAI API key from a `.env` file.
    *   `generator/`:
        *   `core.py`: Implements the `SQLGenerator` class, responsible for:
            *   Initializing the LLM (e.g., `ChatOpenAI`).
            *   Using a prompt template that includes the schema and question.
            *   Generating the SQL query string.
    *   `__init__.py`: Makes `src` a package.
2.  **`tests/`**: Contains tests.
    *   `test_integration.py`: High-level tests verifying the `SQLGenerator`'s ability to produce reasonable SQL for given questions and schemas.
    *   `__init__.py`: Makes `tests` a package.
3.  **`.env.example`**: Example environment file template.
4.  **`.gitignore`**: Standard Python gitignore.
5.  **`requirements.txt`**: Project dependencies.
6.  **`README.md`**: This file - project overview and development plan.

## Development Plan (Revised)

**Phase 1: Project Setup & Configuration (Complete)**

*   [x] **Task 1.1**: Create project structure (directories and empty `__init__.py` files). (Completed)
*   [x] **Task 1.2**: Implement configuration loading (`src/config.py`) for `OPENAI_API_KEY`. (Completed)
*   ~~[x] **Task 1.3**: Implement database connector (`src/database/connector.py`).~~ (Removed - No longer applicable)
*   ~~[x] **Task 1.4**: Create sample database and initialization script (`data/`).~~ (Removed - No longer applicable)

**Phase 2: Core SQL Generator Implementation (Complete)**

*   [x] **Task 2.1**: Initialize LLM (`ChatOpenAI`) within the generator class. (Completed in `src/generator/core.py`)
*   [x] **Task 2.2**: Implement the core SQL generation logic using a prompt template and LLM chain. (Completed in `src/generator/core.py`)
*   [x] **Task 2.3**: Implement the `generate(question: str, schema: str)` method. (Completed in `src/generator/core.py`)

**Phase 3: Integration & Testing (User Task)**

*   [ ] **Task 3.1**: Write high-level integration tests (`tests/test_integration.py`) to verify the `SQLGenerator.generate` method with sample questions and a *predefined, static schema string*.
    *   Ensure `.env` is set up with `OPENAI_API_KEY`.
    *   Ensure necessary dependencies are installed (`pip install -r requirements.txt`, including `pytest`).

**Phase 4: Evaluation Pipeline (New)**

*   [x] **Task 4.1**: Add `datasets` library to `requirements.txt`.
*   [x] **Task 4.2**: Create an evaluation script (e.g., `scripts/evaluate.py` or within `tests/`).
*   [x] **Task 4.3**: Implement logic in the script to load the WikiSQL dataset (`validation` split) using `datasets.load_dataset("wikisql")`.
*   [x] **Task 4.4**: Implement a function to format the WikiSQL table schema (`example['table']`) into a `CREATE TABLE` string suitable for the `SQLGenerator`.
*   [x] **Task 4.5**: Implement the evaluation loop:
    *   Iterate through the loaded dataset.
    *   For each example, extract the question and the formatted schema string.
    *   Call `SQLGenerator.generate(question, schema_string)` to get the predicted SQL.
    *   Compare the `predicted_sql` with the gold SQL (`example['sql']['query']`). Initial comparison can be string-based. (Execution-based evaluation, as shown in `docs/wikisql-datasets.md`, requires creating temporary DBs and can be added later if needed).
    *   Calculate and report metrics (e.g., exact match accuracy).

**Phase 5: Refinement (Future)**

*   [ ] **Task 5.1**: Refine the prompt template (`PROMPT_TEMPLATE` in `src/generator/core.py`) based on evaluation results for better accuracy and handling of edge cases.
*   [ ] **Task 5.2**: Add more robust error handling in the generator and evaluation script.
*   [ ] **Task 5.3**: Consider adding schema validation or parsing logic if needed.
*   [ ] **Task 5.4**: Package the module for easier distribution/use.

## How to Run Tests (After Task 3.1)

1.  Create a `.env` file from `.env.example` and add your `OPENAI_API_KEY`.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run pytest: `pytest`

## How to Run Evaluation (After Phase 4)

1.  Ensure `.env` file is set up.
2.  Ensure dependencies are installed (`pip install -r requirements.txt`).
3.  Run the evaluation script: `python scripts/evaluate.py` (or the path you choose in Task 4.2).
