#!/usr/bin/env python3
from pathlib import Path

def create_gitkeep():
    # 1. Find the main project directory where this script is running
    project_dir = Path(__file__).parent.resolve()
    
    # 2. Define the path to your gcode_output folder
    target_folder = project_dir / "gcode_output"
    
    # 3. Create the folder if it doesn't exist yet
    target_folder.mkdir(exist_ok=True)
    
    # 4. Define the path for the .gitkeep file
    gitkeep_file = target_folder / ".gitkeep"
    
    # 5. Create the empty file (or leave it alone if it already exists)
    gitkeep_file.touch()
    
    print(f"═" * 60)
    print(f" ✓ Target folder verified: {target_folder}")
    print(f" ✓ Created placeholder file: {gitkeep_file}")
    print(f"═" * 60)
    print("\n Ready! You can now run your git push commands in Git Bash.")

if __name__ == "__main__":
    create_gitkeep()