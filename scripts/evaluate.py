# Evaluation script for the Text-to-SQL model using WikiSQL

import sys
import os
import time
from datasets import load_dataset

# Add project root to Python path to allow importing from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Now we can import the generator
from src.agent.core import SQLGenerator

# TODO: Implement Task 4.5

def load_wikisql_validation(limit=None):
    """Loads the validation split of the WikiSQL dataset.

    Args:
        limit (int, optional): Maximum number of examples to load. Defaults to None (load all).

    Returns:
        Dataset: The loaded dataset.
    """
    print("Loading WikiSQL dataset (validation split)...")
    start_time = time.time()
    try:
        # Using trust_remote_code=True might be necessary depending on the dataset version/updates
        ds = load_dataset("wikisql", split="validation", trust_remote_code=True)
        if limit:
            ds = ds.select(range(limit))
            print(f"Loaded {len(ds)} examples (limited).")
        else:
            print(f"Loaded {len(ds)} examples.")
        end_time = time.time()
        print(f"Dataset loading took {end_time - start_time:.2f} seconds.")
        return ds
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise

def format_schema(table_data: dict) -> str:
    """Formats the WikiSQL table dictionary into a CREATE TABLE string.

    Args:
        table_data: A dictionary containing 'header' and 'types' keys.
            Example: {'header': ['col1', 'col2'], 'types': ['text', 'real']}

    Returns:
        A string representing the CREATE TABLE statement.
    """
    if not table_data or 'header' not in table_data or 'types' not in table_data:
        return "Error: Invalid table data format."

    header = table_data['header']
    types = table_data['types']

    if len(header) != len(types):
        return "Error: Header and types length mismatch."

    # Basic type mapping (can be expanded if needed)
    type_mapping = {
        'text': 'TEXT',
        'real': 'REAL',
        'number': 'NUMBER' # Assuming 'number' maps to a generic numeric type
    }

    column_defs = []
    for col_name, col_type in zip(header, types):
        # Sanitize column name (replace spaces, special chars if necessary - basic replacement here)
        sanitized_col_name = f'"{col_name}"' # Quote column names to handle spaces/keywords
        sql_type = type_mapping.get(col_type, 'TEXT') # Default to TEXT if type unknown
        column_defs.append(f"    {sanitized_col_name} {sql_type}")

    # Using a generic table name as it's mainly the column defs the LLM needs
    schema_string = "CREATE TABLE table (\n" + ",\n".join(column_defs) + "\n);"
    return schema_string


if __name__ == "__main__":
    print("Starting evaluation...")

    # --- Initialize Generator ---
    try:
        generator = SQLGenerator()
    except ValueError as e:
        print(f"Error initializing SQLGenerator: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during generator initialization: {e}")
        exit(1)

    # --- Task 4.3: Load Dataset ---
    # Set a small limit for initial testing, remove or increase later
    DATASET_LIMIT = 10
    try:
        validation_dataset = load_wikisql_validation(limit=DATASET_LIMIT)
        if not validation_dataset:
            exit(1)

    except Exception as e:
        print(f"Failed to load dataset: {e}")
        exit(1)

    # --- Task 4.4: Example Schema Formatting ---
    if validation_dataset:
        print("\n--- Example Schema Formatting ---")
        example_table = validation_dataset[0]['table']
        formatted_schema = format_schema(example_table)
        print(f"Original Table Data: {example_table}")
        print(f"Formatted Schema:\n{formatted_schema}")
        print("-------------------------------")


    # --- Task 4.5: Evaluation Loop ---
    print("\n--- Starting Evaluation Loop ---")
    correct_predictions = 0
    total_predictions = 0
    evaluation_start_time = time.time()

    if validation_dataset:
        total_predictions = len(validation_dataset)
        for i, example in enumerate(validation_dataset):
            question = example['question']
            table_data = example['table']
            gold_sql = example['sql']['human_readable'] # Use 'query' field which is the full SQL string

            print(f"\nProcessing example {i+1}/{total_predictions}...")
            print(f"Question: {question}")

            try:
                # Format the schema for the current example
                schema_string = format_schema(table_data)
                if schema_string.startswith("Error:"):
                    print(f"Skipping example due to schema formatting error: {schema_string}")
                    continue

                # Generate SQL using the generator
                predicted_sql = generator.generate(question, schema_string)

                # --- Enhanced Normalization for Comparison ---
                # 1. Lowercase
                # 2. Replace newlines with spaces
                # 3. Collapse multiple spaces into one
                # 4. Strip leading/trailing whitespace
                # Note: This still won't handle quoting or function syntax differences perfectly.
                normalized_pred = ' '.join(predicted_sql.lower().replace('\n', ' ').split()).strip()
                normalized_gold = ' '.join(gold_sql.lower().replace('\n', ' ').split()).strip()

                # print(f"Gold SQL: {gold_sql}")
                # print(f"Pred SQL: {predicted_sql}")
                # Optional: Print normalized versions for debugging
                print(f"Norm Gold: {normalized_gold}")
                print(f"Norm Pred: {normalized_pred}")

                if normalized_pred == normalized_gold:
                    correct_predictions += 1
                    print("Result: CORRECT")
                else:
                    print("Result: INCORRECT")

            except Exception as e:
                print(f"Error processing example {i+1}: {e}")
                # Decide if you want to stop or continue on error
                # continue

    evaluation_end_time = time.time()
    print("--- Evaluation Loop Finished ---")

    # Calculate and print accuracy
    if total_predictions > 0:
        accuracy = (correct_predictions / total_predictions) * 100
        print(f"\nEvaluation Summary:")
        print(f"Total Examples: {total_predictions}")
        print(f"Correct Predictions: {correct_predictions}")
        print(f"Exact Match Accuracy: {accuracy:.2f}%")
        print(f"Evaluation Duration: {evaluation_end_time - evaluation_start_time:.2f} seconds")
    else:
        print("\nNo examples were processed.")

    print("\nEvaluation script finished.")
