# Project Introduction

Welcome to the 3D Fraunhofer Code Generation project! This repository serves as a dedicated workspace for creating, optimizing, and managing precision geometric motion paths (G-code) tailored for advanced 3D printing applications.

The primary goal of this project is to bridge the gap between complex mathematical patterns and physical execution, allowing for reliable, automated scanning sequences.

---

## 🎯 What This Project Does

At its core, this software calculates exact coordinate movements to guide a 3D printer bed or tool head. It takes geometric parameters and translates them into raw machine language.

* **Pattern Automation:** Automatically generates structured movement layouts based on user choices.
* **Smart Organization:** Keeps the project workspace tidy by automatically routing all completed files into a dedicated `output/` folder.
* **Safety Features:** Includes explicit utility scripts to safely reset and home printer axes (`X`, `Y`, and `Z`) to prevent mechanical errors or collisions.

---

## 💻 Environment & Requirements

To run these generation scripts, your computer needs a standard Python environment along with a few supporting tools. 

### Core Dependencies:
* **Python 3.x:** The core programming language used to calculate mathematics and generate file text.
* **CustomTkinter:** A modern graphical interface library that provides a clean, user-friendly window to input settings and select patterns without using a command terminal.
* **Pathlib & Datetime:** Built-in Python modules used to handle automatic folder management and timestamp formatting.

---

## 📂 Repository Structure At A Glance

* `gcode_generator.py` — The main application script responsible for processing patterns and generating code.
* `output/` — The designated folder where your generated `.gcode` files are stored.
* `reset_xy.py` / `reset_z.py` / `z_home.py` — Essential printer calibration utilities.
