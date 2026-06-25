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
    close_browser,
    execute_login_flow
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

def main():
    parser = argparse.ArgumentParser(description="AI Modular Manual Creator CLI")
    parser.add_argument("--module", type=str, required=True, help="The name of the module/feature to document (e.g. 'Login')")
    parser.add_argument("--hints", type=str, default="", help="Optional hints about the files or codebase scope")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config JSON file")
    args = parser.parse_args()
    
    # 1. Load config
    if not os.path.exists(args.config):
        logger.error(f"Error: Config file {args.config} not found.")
        sys.exit(1)
        
    try:
        with open(args.config, "r") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error reading config file {args.config}: {str(e)}")
        sys.exit(1)
        
    target_codebase = config.get("target_codebase_path")
    target_url = config.get("target_app_url")
    credentials = config.get("credentials", {})
    model = config.get("models", {}).get("writer", "openai/MiniMax-M3")
    
    if not target_codebase or not target_url:
        logger.error("Error: target_codebase_path and target_app_url must be defined in the config file.")
        sys.exit(1)
        
    logger.info(f"Target Codebase: {target_codebase}")
    logger.info(f"Target Web Application: {target_url}")
    logger.info(f"Documenting Module: {args.module}")
    logger.info(f"Using Model: {model}")
    logger.info(f"Using Config: {args.config}")
    logger.info("--------------------------------------------------")
    
    # 2. Build pre-bound tools and sandbox directory
    module_folder = args.module.lower().replace(" ", "_")
    module_dir = os.path.join("output", module_folder)
    os.makedirs(module_dir, exist_ok=True)
    
    # Load project metadata if configured
    metadata_info = ""
    metadata_path = config.get("project_metadata_path")
    if metadata_path and os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                project_meta = json.load(f)
            
            project_name = project_meta.get("project_name", "Target Project")
            tech_stack = project_meta.get("tech_stack", "")
            module_meta = project_meta.get("modules", {}).get(args.module)
            
            metadata_info += f"\nProject Name: {project_name}\n"
            if tech_stack:
                metadata_info += f"Tech Stack: {tech_stack}\n"
                
            if module_meta:
                metadata_info += f"Module Metadata details for '{args.module}':\n"
                metadata_info += f" - Description: {module_meta.get('description', '')}\n"
                metadata_info += f" - Targeted files to analyze: {', '.join(module_meta.get('entry_files', []))}\n"
                if module_meta.get("related_folders"):
                    metadata_info += f" - Related folders: {', '.join(module_meta.get('related_folders', []))}\n"
                if module_meta.get("url_path"):
                    metadata_info += f" - Module URL: {module_meta.get('url_path')}\n"
            logger.info("Successfully loaded project metadata layer.")
        except Exception as e:
            logger.warning(f"Failed to read project metadata: {str(e)}")
            
    # Check if a manual already exists for incremental updates
    existing_manual_content = ""
    expected_manual_path = os.path.join(module_dir, f"{module_folder}.md")
    if os.path.exists(expected_manual_path):
        try:
            with open(expected_manual_path, "r", encoding="utf-8") as f:
                existing_manual_content = f.read()
            logger.info(f"Found existing manual at {expected_manual_path}. Enabling incremental updates.")
        except Exception as e:
            logger.warning(f"Could not read existing manual: {str(e)}")
    
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

    def save_documentation(filepath: str, content: str) -> str:
        """
        Write the generated markdown documentation to a file in the active module's output directory.
        filepath: The filename (e.g. 'login.md'). It will be saved under the active module folder.
        content: The markdown documentation content to save.
        """
        try:
            basename = os.path.basename(filepath)
            full_path = os.path.join(module_dir, basename)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully saved documentation file to output/{module_folder}/{basename}."
        except Exception as e:
            return f"Error writing documentation file: {str(e)}"

    def capture_and_save_screenshot(filename: str, highlight_selector: str = None) -> str:
        """
        Capture a screenshot of the current page and save it in the active module's output directory.
        filename: The output filename (e.g. 'login_page.png'). Saved in the active module folder.
        highlight_selector: Optional CSS selector of an element to highlight with a glowing box before screenshot.
        """
        # Pass the relative subpath to browser_screenshot so it writes to output/module_folder/filename
        basename = os.path.basename(filename)
        rel_path = f"{module_folder}/{basename}"
        return browser_screenshot(rel_path, highlight_selector)
        
    tools = {
        "search_files": search_files,
        "read_file": read_file,
        "find_text_pattern": find_text_pattern,
        "browser_navigate": browser_navigate,
        "browser_fill": browser_fill,
        "browser_click": browser_click,
        "browser_screenshot": capture_and_save_screenshot,
        "write_documentation_file": save_documentation
    }
    
    # 3. Assemble Prompts
    import time
    system_instruction = get_system_instruction()
    user_prompt = get_user_prompt(args.module, target_url, credentials, args.hints)
    
    if metadata_info:
        user_prompt += f"\n\n=== PROJECT METADATA LAYER ===\nUse this direct mapping metadata to guide your codebase investigation and navigation:\n{metadata_info}"
        
    if existing_manual_content:
        user_prompt += f"\n\n=== EXISTING MANUAL ===\nAn existing manual already exists for this module. DO NOT perform a full rewrite from scratch. Instead, update and adapt this manual to include the new changes/features while keeping as much of the existing structure and wording intact as possible:\n\n{existing_manual_content}"
        
    user_prompt += f"\n\nRun Identifier: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 4. Run Pre-defined Login Flow if specified
    login_flow = config.get("login_flow")
    if login_flow:
        is_login_module = any(x in args.module.lower() for x in ["login", "signin", "auth"])
        if is_login_module:
            logger.info("Active module is a login/auth module. Skipping automated login to allow manual documentation of the login steps.")
        else:
            logger.info("Executing configured login flow...")
            login_result = execute_login_flow(login_flow)
            logger.info(login_result)
        
    # 5. Run Agent
    logger.info("Starting documentation agent pipeline...")
    try:
        run_agent(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            tools=tools,
            model=model,
            max_turns=50
        )
        logger.info("Documentation agent pipeline finished successfully.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during execution: {str(e)}")
    finally:
        # Always close browser context at the end
        close_browser()

if __name__ == "__main__":
    main()
