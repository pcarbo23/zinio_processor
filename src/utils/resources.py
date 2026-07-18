import os
import sys

def get_resource_path(relative_path: str) -> str:
    """
    Resolves the absolute path to a resource file.
    Works for standard local development execution as well as PyInstaller single-file mode.
    """
    try:
        # PyInstaller extracts resources to a temp folder named sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Resolve path relative to the project root directory
        # Since this file is located in src/utils/resources.py, we go 3 levels up
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return os.path.normpath(os.path.join(base_path, relative_path))
