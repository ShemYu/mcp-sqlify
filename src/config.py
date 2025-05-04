import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This will search for a .env file in the current directory or parent directories
load_dotenv()

# Get the OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Basic validation (optional but recommended)
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY is not set in the .env file.")
    # Depending on the use case, you might want to raise an error here
    # raise ValueError("OPENAI_API_KEY must be set in the .env file")

# You can add more configurations here as needed

if __name__ == "__main__":
    # Example of how to access the loaded variables
    print(f"OpenAI Key Loaded: {'Yes' if OPENAI_API_KEY else 'No'}")
