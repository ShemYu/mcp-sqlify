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

*   [ ] **Task 3.1**: Write high-level integration tests (`tests/test_integration.py`) to verify the `SQLGenerator.generate` method with sample questions and a predefined schema string.
    *   Ensure `.env` is set up with `OPENAI_API_KEY`.
    *   Ensure necessary dependencies are installed (`pip install -r requirements.txt`).

**Phase 4: Refinement (Future)**

*   [ ] **Task 4.1**: Refine the prompt template (`PROMPT_TEMPLATE` in `src/generator/core.py`) for better accuracy and handling of edge cases.
*   [ ] **Task 4.2**: Add more robust error handling.
*   [ ] **Task 4.3**: Consider adding schema validation or parsing logic if needed.
*   [ ] **Task 4.4**: Package the module for easier distribution/use.

## How to Run Tests (After Task 3.1)

1.  Create a `.env` file from `.env.example` and add your `OPENAI_API_KEY`.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run pytest: `pytest`
