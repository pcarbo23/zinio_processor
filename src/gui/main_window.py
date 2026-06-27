import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QFileDialog, QMessageBox
)
from PySide6.QtCore import Slot
from src.gui.worker import AutomatorWorker

class MainWindow(QMainWindow):
    """
    Main Application Window for Hindenburg Automator.
    
    Layout Hierarchy:
    - Top Section: Parameters form input fields (API URL, Username, Password, Project Name, Output Directory selection)
      and a 'Fetch & Generate' action trigger button.
    - Center Section: Large QTextBrowser log viewer displaying background thread outputs and extraction progress.
    - Lower Section: Status indicator label displaying real-time application state.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hindenburg Automator MVP")
        self.resize(800, 600)
        self.worker = None

        # Main Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Top Section - Input Form & Action Button
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.api_endpoint_input = QLineEdit("https://httpbin.org/post")
        self.username_input = QLineEdit("default_user")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.project_name_input = QLineEdit("Mock Magazine")
        
        # Dynamic directory browse block
        dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText(os.getcwd())
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(self.output_dir_input)
        dir_layout.addWidget(self.browse_btn)

        form_layout.addRow("API Endpoint:", self.api_endpoint_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password / Token:", self.password_input)
        form_layout.addRow("Project Name:", self.project_name_input)
        form_layout.addRow("Output Directory:", dir_layout)

        self.fetch_btn = QPushButton("Fetch & Generate")
        self.fetch_btn.clicked.connect(self.start_process)
        form_layout.addRow(self.fetch_btn)
        
        main_layout.addWidget(form_widget)

        # 2. Center Section - QTextBrowser Logs
        self.log_browser = QTextBrowser()
        self.log_browser.setPlaceholderText("Execution logs will appear here...")
        main_layout.addWidget(self.log_browser)

        # 3. Lower Section - STATUS Label
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 0)
        self.status_label = QLabel("Status: Idle")
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_widget)

    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)

    def start_process(self):
        # Validation checks
        if not self.password_input.text():
            QMessageBox.warning(self, "Validation Error", "Password / Token is required for API token authentication.")
            return
        if not self.project_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Project Name is required.")
            return
        if not self.output_dir_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Output Directory is required.")
            return

        # Clear UI state and disable inputs
        self.fetch_btn.setEnabled(False)
        self.log_browser.clear()
        self.log_browser.append("Starting automated build process...")

        # Launch QThread background worker
        self.worker = AutomatorWorker(
            api_url=self.api_endpoint_input.text(),
            username=self.username_input.text(),
            password=self.password_input.text(),
            project_name=self.project_name_input.text().strip(),
            output_dir=self.output_dir_input.text().strip()
        )

        # Setup GUI signal links
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.process_finished)

        self.worker.start()

    @Slot(str)
    def append_log(self, text):
        self.log_browser.append(text)

    @Slot(str)
    def update_status(self, status):
        self.status_label.setText(status)

    @Slot(bool, str)
    def process_finished(self, success, message):
        self.fetch_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Process Completed", "Hindenburg Session compiled successfully!")
        else:
            QMessageBox.critical(self, "Process Failed", f"Automation process failed: {message}")
