from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional

# Import config
from ..config import OPENAI_API_KEY

# Define a basic prompt template for Text-to-SQL
# This will be improved later (Task 4)
PROMPT_TEMPLATE = """
Based on the table schema below, write a SQL query that would answer the user's question.
Do not query for columns that are not in the schema.
Pay attention to the type of columns.
Output the SQL query ONLY, without any explanation or markdown formatting.

Schema:
{schema}

Question:
{question}

SQL Query:
"""

class SQLGenerator:
    """Handles the generation of SQL queries from natural language using an LLM."""

    def __init__(self, llm: Optional[ChatOpenAI] = None, prompt_template: Optional[str] = None):
        """
        Initializes the SQLGenerator.

        Args:
            llm: Optional pre-initialized ChatOpenAI instance.
            prompt_template: Optional custom prompt template string.
        """
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured. Please set it in your .env file.")

        self.llm = llm or ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=OPENAI_API_KEY)
        self.prompt = ChatPromptTemplate.from_template(prompt_template or PROMPT_TEMPLATE)
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

        print("SQL Generator initialized successfully.")

    def generate(self, question: str, schema: str) -> str:
        """Generates an SQL query based on the user's question and table schema.

        Args:
            question: The natural language question.
            schema: A string describing the database schema (e.g., CREATE TABLE statements).

        Returns:
            The generated SQL query string.
        """
        print(f"\nGenerating SQL for question: '{question}'")
        print(f"Using Schema:\n{schema}")
        try:
            # Use invoke for synchronous execution
            sql_query = self.chain.invoke({"question": question, "schema": schema})
            print(f"Generated SQL: {sql_query}")
            return sql_query
        except Exception as e:
            print(f"Error during SQL generation: {e}")
            # Return a meaningful error or re-raise
            return f"Error generating SQL: {e}"

# Example usage
if __name__ == "__main__":
    print("Testing SQLGenerator...")
    try:
        # Example Schema (replace with your actual schema definition)
        example_schema = """
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            amount REAL,
            transaction_date TEXT, -- Format YYYY-MM-DD
            category TEXT
        );
        """

        generator = SQLGenerator()
        print("\nSQLGenerator instance created.")

        # --- Test the generate method ---
        test_query = "How many transactions are there?"
        # test_query = "What is the total amount for Alice Smith?"
        # test_query = "List all transactions for groceries sorted by date."

        generated_sql = generator.generate(test_query, example_schema)
        print("\n--- Result --- ")
        print(generated_sql)
        print("---------------")

        test_query_2 = "Show me the names and amounts for transactions in the 'Electronics' category."
        generated_sql_2 = generator.generate(test_query_2, example_schema)
        print("\n--- Result 2 --- ")
        print(generated_sql_2)
        print("---------------")

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
    except Exception as e:
        print(f"An error occurred during testing: {e}")
