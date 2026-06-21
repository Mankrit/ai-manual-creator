import json
import os
from dotenv import load_dotenv
from core.agent import run_agent
from core.tools.code_tools import search_codebase, read_code_file, grep_codebase

load_dotenv()

def main():
    # 1. Load config
    if not os.path.exists("config.json"):
        print("Error: config.json not found.")
        print("Please copy config.example.json to config.json and populate your local settings (paths, models, credentials).")
        return
        
    with open("config.json", "r") as f:
        config = json.load(f)
        
    target_path = config.get("target_codebase_path")
    model = config.get("models", {}).get("routing", "gemini/gemini-1.5-flash")
    
    print(f"Target codebase path: {target_path}")
    print(f"Model selected: {model}")
    print("----------------------------------------")
    
    # 2. Define tools with pre-bound target path
    # We write simple wrapper functions with docstrings and type hints so the schema parser can parse them.
    
    def search_files(query: str) -> list[str]:
        """
        Search for filenames containing the query string (case-insensitive) in the target codebase.
        query: The substring to search for in filenames.
        """
        return search_codebase(target_path, query)
        
    def read_file(filepath: str, start_line: int = 1, end_line: int = None) -> str:
        """
        Read the contents of a specific file in the codebase.
        filepath: The path to the file relative to the codebase root.
        start_line: Optional start line number (1-indexed).
        end_line: Optional end line number (1-indexed).
        """
        return read_code_file(target_path, filepath, start_line, end_line)
        
    def find_text_pattern(pattern: str) -> list[dict]:
        """
        Search inside code files for a specific text pattern (case-insensitive).
        pattern: The text query to search for inside file contents.
        """
        return grep_codebase(target_path, pattern)

    tools = {
        "search_files": search_files,
        "read_file": read_file,
        "find_text_pattern": find_text_pattern
    }
    
    # 3. Define prompt and system instruction
    system_instruction = (
        "You are an expert developer assistant. You have access to tools that let you "
        "search and read the source code of a target project. Your goal is to help the user "
        "find and understand how parts of their application work. Always use the search tools "
        "first to identify files, and read the relevant files before summarizing."
    )
    
    user_prompt = (
        "Search for a python file containing 'main' or 'writer' in its filename, "
        "read the first 50 lines of it, and briefly summarize what it does."
    )
    
    # 4. Run the agent
    print("Starting agent loop...")
    history = run_agent(
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        tools=tools,
        model=model,
        max_turns=10
    )
    
    print("\n----------------------------------------")
    print("Agent run finished.")
    print(f"Total conversation messages: {len(history)}")
    
if __name__ == "__main__":
    main()
