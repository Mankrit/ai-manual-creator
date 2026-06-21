import os
import sys
import json
import argparse
import logging
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from core.agent import run_agent
from core.prompts import get_system_instruction, get_user_prompt
from core.tools.code_tools import search_codebase, read_code_file, grep_codebase
from core.tools.web_tools import (
    browser_navigate,
    browser_fill,
    browser_click,
    browser_screenshot,
    close_browser
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

def write_documentation_file(filepath: str, content: str) -> str:
    """
    Write the generated markdown documentation to a file in the output/ directory.
    filepath: The filename (e.g. 'login.md'). It will be saved under output/.
    content: The markdown documentation content to save.
    """
    try:
        os.makedirs("output", exist_ok=True)
        # Sandbox file write to output/ directory
        basename = os.path.basename(filepath)
        full_path = os.path.join("output", basename)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully saved documentation file to output/{basename}."
    except Exception as e:
        return f"Error writing documentation file: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="AI Modular Manual Creator CLI")
    parser.add_argument("--module", type=str, required=True, help="The name of the module/feature to document (e.g. 'Login')")
    parser.add_argument("--hints", type=str, default="", help="Optional hints about the files or codebase scope")
    args = parser.parse_args()
    
    # 1. Load config.json
    if not os.path.exists("config.json"):
        logger.error("Error: config.json not found. Please copy config.example.json to config.json.")
        sys.exit(1)
        
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error reading config.json: {str(e)}")
        sys.exit(1)
        
    target_codebase = config.get("target_codebase_path")
    target_url = config.get("target_app_url")
    credentials = config.get("credentials", {})
    model = config.get("models", {}).get("writer", "openai/MiniMax-M3")
    
    if not target_codebase or not target_url:
        logger.error("Error: target_codebase_path and target_app_url must be defined in config.json.")
        sys.exit(1)
        
    logger.info(f"Target Codebase: {target_codebase}")
    logger.info(f"Target Web Application: {target_url}")
    logger.info(f"Documenting Module: {args.module}")
    logger.info(f"Using Model: {model}")
    logger.info("--------------------------------------------------")
    
    # 2. Build pre-bound tools
    def search_files(query: str) -> list[str]:
        """
        Search for filenames containing the query string (case-insensitive) in the target codebase.
        query: The substring to search for in filenames.
        """
        return search_codebase(target_codebase, query)
        
    def read_file(filepath: str, start_line: int = 1, end_line: int = None) -> str:
        """
        Read the contents of a specific file in the codebase.
        filepath: The path to the file relative to the codebase root.
        start_line: Optional start line number (1-indexed).
        end_line: Optional end line number (1-indexed).
        """
        return read_code_file(target_codebase, filepath, start_line, end_line)
        
    def find_text_pattern(pattern: str) -> list[dict]:
        """
        Search inside code files for a specific text pattern (case-insensitive).
        pattern: The text query to search for inside file contents.
        """
        return grep_codebase(target_codebase, pattern)
        
    tools = {
        "search_files": search_files,
        "read_file": read_file,
        "find_text_pattern": find_text_pattern,
        "browser_navigate": browser_navigate,
        "browser_fill": browser_fill,
        "browser_click": browser_click,
        "browser_screenshot": browser_screenshot,
        "write_documentation_file": write_documentation_file
    }
    
    # 3. Assemble Prompts
    system_instruction = get_system_instruction()
    user_prompt = get_user_prompt(args.module, target_url, credentials, args.hints)
    
    # 4. Run Agent
    logger.info("Starting documentation agent pipeline...")
    try:
        run_agent(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            tools=tools,
            model=model,
            max_turns=30
        )
        logger.info("Documentation agent pipeline finished successfully.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during execution: {str(e)}")
    finally:
        # Always close browser context at the end
        close_browser()

if __name__ == "__main__":
    main()
