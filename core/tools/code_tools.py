import os
from typing import List, Dict, Any

def search_codebase(target_path: str, query: str) -> List[str]:
    """
    Search the codebase for filenames containing the query string (case-insensitive).
    Returns a list of matching file paths relative to target_path.
    """
    matches = []
    # Common compiled, ignored, or temporary folders we should not index
    ignore_dirs = {
        ".git", "node_modules", "venv", ".venv", "build", "dist", 
        "__pycache__", "bin", "obj", "temp", ".vs", "packages"
    }
    for root, dirnames, filenames in os.walk(target_path):
        # Exclude directories in-place
        dirnames[:] = [d for d in dirnames if d.lower() not in ignore_dirs]
                
        for filename in filenames:
            if query.lower() in filename.lower():
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, target_path)
                matches.append(rel_path.replace("\\", "/"))
    return matches[:50]  # Cap at 50 matches

def read_code_file(target_path: str, filepath: str, start_line: int = 1, end_line: int = None) -> str:
    """
    Read the contents of a file in the codebase.
    filepath should be relative to the target_codebase_path.
    Optional start_line and end_line parameters for large files (1-indexed).
    """
    full_path = os.path.join(target_path, filepath)
    # Security check: ensure path is within target_path
    real_target = os.path.realpath(target_path)
    real_file = os.path.realpath(full_path)
    if not real_file.startswith(real_target):
        return "Error: Access denied. File must be within the target codebase path."
        
    if not os.path.exists(full_path):
        return f"Error: File not found: {filepath}"
        
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        if end_line is None:
            end_line = len(lines)
            
        # Ensure bounds are within range
        start_line = max(1, start_line)
        end_line = min(len(lines), end_line)
        
        selected_lines = lines[start_line-1:end_line]
        content = "".join(selected_lines)
        return f"--- File: {filepath} (Lines {start_line}-{end_line} of {len(lines)}) ---\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def grep_codebase(target_path: str, pattern: str) -> List[Dict[str, Any]]:
    """
    Search inside files for a specific text pattern (case-insensitive).
    Returns list of matches containing file path, line number, and line content.
    """
    matches = []
    ignore_dirs = {
        ".git", "node_modules", "venv", ".venv", "build", "dist", 
        "__pycache__", "bin", "obj", "temp", ".vs", "packages"
    }
    # Expanded list of binary or non-text extensions to skip
    binary_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', 
        '.db', '.sqlite', '.dll', '.exe', '.pdb', '.xlsx', '.xls', '.doc', '.docx', 
        '.ppt', '.pptx', '.rar', '.7z', '.mp3', '.mp4', '.avi', '.mkv', '.class'
    }
    
    for root, dirnames, filenames in os.walk(target_path):
        dirnames[:] = [d for d in dirnames if d.lower() not in ignore_dirs]
                
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in binary_extensions:
                continue
                
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, target_path).replace("\\", "/")
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if pattern.lower() in line.lower():
                            matches.append({
                                "file": rel_path,
                                "line_number": i,
                                "content": content
                            })
                            if len(matches) >= 50:
                                return matches
            except Exception:
                pass
    return matches
