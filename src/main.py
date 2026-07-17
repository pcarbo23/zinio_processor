import os
import sys

# Add project root to sys.path to allow execution from any folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.gui.main_window import MainWindow

def main():
    """
    Entry point for the Zinio Media Processor application.
    """
    # Fix taskbar icon on Windows (prevent grouping with python.exe default icon)
    if sys.platform == "win32":
        import ctypes
        try:
            myappid = "zinio.mediaprocessor.generator.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Fix macOS menu bar name when running raw script (prevent showing "Python")
    if sys.platform == "darwin":
        try:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if app_info is not None:
                    app_info['CFBundleName'] = "Zinio Media Processor"
        except Exception:
            pass

    from src.utils.resources import get_resource_path

    app = QApplication(sys.argv)
    app.setApplicationName("Zinio Media Processor")
    app.setApplicationDisplayName("Zinio Media Processor")
    
    # Set application-wide icon
    icon_path = get_resource_path("icon_concept1.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
