import os
import json
import shutil
import re

def compile_docs():
    output_dir = "output"
    portal_docs_dir = os.path.join("portal", "public", "docs")
    
    # Ensure portal/public/docs exists and is clean
    if os.path.exists(portal_docs_dir):
        try:
            shutil.rmtree(portal_docs_dir)
        except Exception as e:
            print(f"Warning: could not clean docs directory: {e}")
            
    os.makedirs(portal_docs_dir, exist_ok=True)
    
    catalog = []
    
    if not os.path.exists(output_dir):
        print(f"Output directory '{output_dir}' does not exist.")
        return
        
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path):
            module_key = item
            # Find markdown files in this directory
            md_files = [f for f in os.listdir(item_path) if f.endswith(".md")]
            if not md_files:
                continue
                
            # Create subdirectory in portal/public/docs/<module_key>
            dest_module_dir = os.path.join(portal_docs_dir, module_key)
            os.makedirs(dest_module_dir, exist_ok=True)
            
            # Copy all files (md and png) to the destination
            for f in os.listdir(item_path):
                src_file = os.path.join(item_path, f)
                dest_file = os.path.join(dest_module_dir, f)
                shutil.copy2(src_file, dest_file)
                
            # Extract metadata from the primary markdown file
            primary_md = md_files[0]
            primary_md_path = os.path.join(item_path, primary_md)
            
            title = module_key.replace("_", " ").title()
            try:
                with open(primary_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if match:
                        title = match.group(1).replace("MODULE:", "").strip()
            except Exception as e:
                print(f"Error reading {primary_md_path}: {e}")
            
            # Build list of screenshots referenced or found in the directory
            screenshots = [f for f in os.listdir(item_path) if f.endswith(".png")]
            
            catalog.append({
                "key": module_key,
                "title": title,
                "markdown_file": primary_md,
                "screenshots": screenshots
            })
            
    # Save the catalog
    catalog_path = os.path.join(portal_docs_dir, "catalog.json")
    try:
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        print(f"Compilation finished successfully. Saved catalog with {len(catalog)} modules to {catalog_path}")
    except Exception as e:
        print(f"Error writing catalog.json: {e}")

if __name__ == "__main__":
    compile_docs()
