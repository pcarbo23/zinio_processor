# Hindenburg Automator MVP

Desktop application designed to automate the creation of Hindenburg Narrator session files (`.nhsx`, `Document.xhtml`, `style.css`) for Digital Talking Books (DTBs).

## Setup Instructions

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run tests:
   ```bash
   pytest
   ```
4. Run the application:
   ```bash
   python src/main.py
   ```
