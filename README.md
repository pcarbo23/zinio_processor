# Zinio Media Processor MVP

Desktop application designed to process Zinio audio magazines into Hindenburg Narrator session files (`.nhsx`, `Document.xhtml`, `style.css`) for Digital Talking Books (DTBs).

## Setup Instructions

### Windows (Simplified One-Click Setup)

If you are on Windows, you can automate the entire installation process (including Python, FFmpeg, virtual environment dependencies, and compiling to a desktop shortcut):

1. Double-click the **`install.bat`** file in the root directory.
2. The script will automatically check for and install Python and FFmpeg if missing, configure all paths, install dependencies, compile the application into a standalone executable, and place a shortcut on your Desktop.

---

### Manual Setup (macOS / Linux / Advanced Windows)

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
