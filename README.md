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

## Packaging with PyInstaller

PyInstaller compiles python scripts into native standalone executables. Note that PyInstaller executables are **platform-specific** (not OS-agnostic); you must run the build command on the target OS (e.g. build on Windows to get a `.exe`, build on macOS to get an app/binary).

To generate a highly optimized, lean, and fast single-file executable, run:

```bash
pyinstaller --onefile --windowed \
  --name "HindenburgAutomator" \
  --exclude-module tkinter \
  --exclude-module unittest \
  --exclude-module email \
  --exclude-module pydoc \
  --exclude-module pdb \
  --exclude-module difflib \
  src/main.py
```

### Exclusions Explained
* `--onefile`: Packs everything into a single executable.
* `--windowed` / `-w`: Disables the console window when running the GUI.
* `--exclude-module`: Strips unused standard library modules to reduce binary footprint.

