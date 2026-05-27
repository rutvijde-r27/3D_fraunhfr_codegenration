# 3D Fraunhofer G-Code Generator (Version 2)

A Python-based utility designed to generate custom G-code motion paths for Anycubic 3D printers, specifically optimized for Fraunhofer co-generation patterns.

## 🚀 Features
* Automatically calculates grid parameters (`plate_x`, `plate_y`, `gap`, etc.).
* Supports multiple scanning patterns with dynamic angle adjustments.
* Generates an automatic preview of the first 15 motion lines in the terminal.
* Automatically creates an `output/` directory and saves structured `.gcode` files with clean timestamps.

## 🛠️ How it Works
Explain in a few sentences how the script runs. For example:
1. The script initializes configuration parameters for the print bed.
2. It processes the chosen geometric pattern and applies offsets or rotations.
3. It compiles the motion commands (`G0` and `G1`) into a single text block.
4. It exports the file directly to the `/output` folder.

## 📦 How to Run
1. Ensure you have Python installed.
2. Open your terminal in this directory and run:
   ```bash
   python gcode_generator.py