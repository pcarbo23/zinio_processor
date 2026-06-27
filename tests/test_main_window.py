import pytest
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

@pytest.fixture(scope="module")
def q_app():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app

def test_main_window_init(q_app):
    window = MainWindow()
    assert window.windowTitle() == "Hindenburg Automator MVP"
    assert window.api_endpoint_input.text() == "https://httpbin.org/post"
    assert window.username_input.text() == "default_user"
    assert window.status_label.text() == "Status: Idle"
