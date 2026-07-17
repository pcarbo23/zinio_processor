import os
import requests
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextBrowser, QFileDialog, QMessageBox,
    QComboBox, QDialog, QDialogButtonBox, QMenuBar, QMenu
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QIcon, QPixmap
from src.gui.worker import AutomatorWorker
import datetime
from src.utils.config import load_config, save_config, load_download_history, save_download_history
from src.utils.security import APIManager
from src.utils.api_metadata import generate_basefile_value

APP_VERSION = "1.0.0"

class PreferencesDialog(QDialog):
    """
    Settings dialog to store server URLs, newsstand and feed settings.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(450, 250)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        config = load_config()
        server_url = config.get("server_url", "http://127.0.0.1:8000")
        newsstand_id = config.get("newsstand_id", "3862")
        feed_id = config.get("feed_id", "1")
        client_id = config.get("client_id", "default_user")
        
        self.server_url_input = QLineEdit(server_url)
        self.newsstand_id_input = QLineEdit(newsstand_id)
        self.feed_id_input = QLineEdit(feed_id)
        self.client_id_input = QLineEdit(client_id)
        
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Load secret from keyring if available
        api_manager = APIManager(api_url=server_url, client_id=client_id)
        try:
            secret = api_manager.get_credentials()
            if secret:
                self.client_secret_input.setText(secret)
        except Exception:
            pass
            
        form_layout.addRow("Server URL:", self.server_url_input)
        form_layout.addRow("Newsstand ID:", self.newsstand_id_input)
        form_layout.addRow("Feed ID:", self.feed_id_input)
        form_layout.addRow("Client ID:", self.client_id_input)
        form_layout.addRow("Client Secret:", self.client_secret_input)
        
        layout.addLayout(form_layout)
        
        bottom_layout = QHBoxLayout()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.save_preferences)
        buttons.rejected.connect(self.reject)
        bottom_layout.addWidget(buttons)
        
        bottom_layout.addStretch()
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("color: gray;")
        bottom_layout.addWidget(version_label)
        
        layout.addLayout(bottom_layout)
        
    def save_preferences(self):
        config = {
            "server_url": self.server_url_input.text().strip(),
            "newsstand_id": self.newsstand_id_input.text().strip(),
            "feed_id": self.feed_id_input.text().strip(),
            "client_id": self.client_id_input.text().strip()
        }
        save_config(config)
        
        secret = self.client_secret_input.text().strip()
        if secret:
            api_manager = APIManager(api_url=config["server_url"], client_id=config["client_id"])
            try:
                api_manager.store_credentials(secret)
            except Exception as e:
                QMessageBox.critical(self, "Keyring Error", f"Failed to save client secret: {e}")
                
        self.accept()


class MainWindow(QMainWindow):
    """
    Main Application Window for Hindenburg Automator with Dynamic API Options.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zinio Media Processor")
        self.resize(850, 650)
        self.worker = None
        self.publications_map = {}
        self.issues_map = {}

        from src.utils.resources import get_resource_path
        # Set Window Icon
        icon_path = get_resource_path("icon_concept1.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Add Menu Bar for Preferences
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        settings_menu = self.menu_bar.addMenu("Settings")
        preferences_action = settings_menu.addAction("Preferences...")
        preferences_action.triggered.connect(self.open_preferences)
        
        about_menu = self.menu_bar.addMenu("About")
        about_action = about_menu.addAction("About Zinio Media Processor")
        about_action.triggered.connect(self.show_about_dialog)

        # Main Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
 
        # Form Container Widget
        form_widget = QWidget()
        grid_layout = QGridLayout(form_widget)
        grid_layout.setSpacing(10)
        
        self.publication_combo = QComboBox()
        self.publication_combo.setFixedWidth(450)
        self.publication_combo.currentIndexChanged.connect(self.on_publication_selected)
        
        self.issue_combo = QComboBox()
        self.issue_combo.setFixedWidth(450)
        self.issue_combo.currentIndexChanged.connect(self.on_issue_selected)
        
        self.project_name_input = QLineEdit("")
        self.project_name_input.setReadOnly(True)
        self.project_name_input.setFixedWidth(450)
        
        self.output_dir_input = QLineEdit()
        config = load_config()
        self.output_dir_input.setText(config.get("last_output_dir", os.getcwd()))
        self.output_dir_input.setFixedWidth(450)
        
        # Buttons (all equal in size, fixed width 160)
        self.sync_btn = QPushButton("Sync Publications")
        self.sync_btn.clicked.connect(self.load_publications)
        self.sync_btn.setFixedWidth(160)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_output_dir)
        self.browse_btn.setFixedWidth(160)
        
        self.fetch_btn = QPushButton("Fetch && Generate")
        self.fetch_btn.clicked.connect(self.start_process)
        self.fetch_btn.setFixedWidth(160)

        # Add to Grid Layout
        grid_layout.addWidget(QLabel("Publication:"), 0, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid_layout.addWidget(self.publication_combo, 0, 1)
        grid_layout.addWidget(self.sync_btn, 0, 2)
        
        grid_layout.addWidget(QLabel("Issue:"), 1, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid_layout.addWidget(self.issue_combo, 1, 1)
        
        grid_layout.addWidget(QLabel("Project Name:"), 2, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid_layout.addWidget(self.project_name_input, 2, 1)
        
        grid_layout.addWidget(QLabel("Output Directory:"), 3, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid_layout.addWidget(self.output_dir_input, 3, 1)
        grid_layout.addWidget(self.browse_btn, 3, 2)
        
        grid_layout.addWidget(self.fetch_btn, 4, 2)
        
        main_layout.addWidget(form_widget, 0, Qt.AlignCenter)

        # 2. Center Section - QTextBrowser Logs
        self.log_browser = QTextBrowser()
        self.log_browser.setPlaceholderText("Click 'Sync Publications' first, then configure settings or start execution...")
        main_layout.addWidget(self.log_browser)

        # 3. Lower Section - STATUS Label
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 0)
        self.status_label = QLabel("Status: Idle")
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_widget)
        
        # Auto-sync publications on startup if possible
        self.load_publications()

    def open_preferences(self):
        dialog = PreferencesDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.append_log("Preferences saved. Re-syncing publications...")
            self.load_publications()

    def show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("About Zinio Media Processor")
        dialog.setFixedSize(350, 180)
        
        layout = QVBoxLayout(dialog)
        layout.setAlignment(Qt.AlignCenter)
        
        from src.utils.resources import get_resource_path
        # Icon
        icon_path = get_resource_path("icon_concept1.png")
        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            layout.addWidget(icon_label, 0, Qt.AlignCenter)
            
        # Tool name
        name_label = QLabel("Zinio Media Processor")
        name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(name_label, 0, Qt.AlignCenter)
        
        # Version
        version_label = QLabel(f"Version {APP_VERSION}")
        layout.addWidget(version_label, 0, Qt.AlignCenter)
        
        # Close button
        button = QPushButton("Close")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button, 0, Qt.AlignCenter)
        
        dialog.exec()

    def load_publications(self):
        config = load_config()
        server_url = config.get("server_url")
        newsstand_id = config.get("newsstand_id")
        client_id = config.get("client_id")
        
        api_manager = APIManager(api_url=server_url, client_id=client_id)
        client_secret = api_manager.get_credentials()
        if not client_secret:
            self.append_log("[WARNING] Client Secret not configured. Go to Settings -> Preferences.")
            return
            
        try:
            self.sync_btn.setEnabled(False)
            token = api_manager.get_session_token()
            url = f"{api_manager.api_url}/newsstand/v2/newsstands/{newsstand_id}/publications"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            publications = response.json().get("data", [])
            self.publication_combo.blockSignals(True)
            self.publication_combo.clear()
            self.publications_map = {}
            
            for pub in publications:
                pub_id = pub.get("id")
                pub_name = pub.get("name")
                display_name = f"{pub_name} (ID: {pub_id})"
                self.publication_combo.addItem(display_name, pub_id)
                self.publications_map[pub_id] = pub
                
            self.publication_combo.setCurrentIndex(-1)
            self.publication_combo.blockSignals(False)
            
            self.issue_combo.blockSignals(True)
            self.issue_combo.clear()
            self.issue_combo.setCurrentIndex(-1)
            self.issue_combo.blockSignals(False)
            self.project_name_input.clear()
            
            self.append_log("Publications successfully synced from Zinio API.")
        except Exception as e:
            self.append_log(f"[ERROR] Failed to sync publications: {e}")
        finally:
            self.sync_btn.setEnabled(True)

    def on_publication_selected(self, index):
        if index < 0:
            self.issue_combo.blockSignals(True)
            self.issue_combo.clear()
            self.issue_combo.setCurrentIndex(-1)
            self.issue_combo.blockSignals(False)
            self.project_name_input.clear()
            return
        pub_id = self.publication_combo.itemData(index)
        if not pub_id:
            self.issue_combo.blockSignals(True)
            self.issue_combo.clear()
            self.issue_combo.setCurrentIndex(-1)
            self.issue_combo.blockSignals(False)
            self.project_name_input.clear()
            return
            
        config = load_config()
        server_url = config.get("server_url")
        newsstand_id = config.get("newsstand_id")
        client_id = config.get("client_id")
        
        api_manager = APIManager(api_url=server_url, client_id=client_id)
        try:
            token = api_manager.get_session_token()
            url = f"{api_manager.api_url}/newsstand/v2/newsstands/{newsstand_id}/publications/{pub_id}/issues"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            issues = response.json().get("data", [])
            self.issue_combo.blockSignals(True)
            self.issue_combo.clear()
            
            # Sort issues by publish date descending
            try:
                issues_sorted = sorted(issues, key=lambda x: x.get("publish_date", ""), reverse=True)
            except Exception:
                issues_sorted = issues
                
            self.issues_map = {}
            history = load_download_history()
            for i, issue in enumerate(issues_sorted):
                issue_id = issue.get("id")
                issue_name = issue.get("name")
                issue_id_str = str(issue_id)
                display_name = f"{issue_name} (ID: {issue_id})"
                
                if issue_id_str in history:
                    stored_rev = history[issue_id_str].get("content_revision", "")
                    stored_mod = history[issue_id_str].get("modified_at", "")
                    api_rev = issue.get("content_revision", "")
                    api_mod = issue.get("modified_at", "")
                    
                    if api_rev != stored_rev or (not api_rev and api_mod != stored_mod):
                        display_name += " [UPDATE AVAILABLE]"
                        self.append_log(f"[INFO] A new version is available for previously downloaded issue: {issue_name}")
                else:
                    if i == 0:
                        display_name += " [NEW ISSUE]"
                        
                self.issue_combo.addItem(display_name, issue_id)
                self.issues_map[issue_id] = issue
                
            self.issue_combo.setCurrentIndex(-1)
            self.issue_combo.blockSignals(False)
            self.project_name_input.clear()
            self.append_log(f"Issues loaded for publication ID {pub_id}.")
        except Exception as e:
            self.issue_combo.blockSignals(True)
            self.issue_combo.clear()
            self.issue_combo.setCurrentIndex(-1)
            self.issue_combo.blockSignals(False)
            self.project_name_input.clear()
            self.append_log(f"[ERROR] Failed to load issues: {e}")

    def on_issue_selected(self, index):
        if index < 0:
            self.project_name_input.clear()
            return
        pub_id = self.publication_combo.itemData(self.publication_combo.currentIndex())
        issue_id = self.issue_combo.itemData(index)
        if not pub_id or not issue_id:
            self.project_name_input.clear()
            return
        pub = self.publications_map.get(pub_id)
        issue = self.issues_map.get(issue_id)
        if pub and issue:
            basefile = generate_basefile_value(pub.get("name", ""), issue.get("cover_date", ""))
            self.project_name_input.setText(basefile)
            
            # Check if this issue has an update available
            history = load_download_history()
            issue_id_str = str(issue_id)
            if issue_id_str in history:
                stored_rev = history[issue_id_str].get("content_revision", "")
                stored_mod = history[issue_id_str].get("modified_at", "")
                api_rev = issue.get("content_revision", "")
                api_mod = issue.get("modified_at", "")
                if api_rev != stored_rev or (not api_rev and api_mod != stored_mod):
                    self.append_log(f"[WARNING] Selected issue has been updated on the server since you last downloaded it. Click 'Fetch & Generate' to get the new version.")

    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)
            config = load_config()
            config["last_output_dir"] = directory
            save_config(config)

    def start_process(self):
        if self.publication_combo.currentIndex() < 0 or self.issue_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Validation Error", "Please select a publication and an issue.")
            return
            
        pub_id = self.publication_combo.itemData(self.publication_combo.currentIndex())
        issue_id = self.issue_combo.itemData(self.issue_combo.currentIndex())
        
        config = load_config()
        server_url = config.get("server_url")
        newsstand_id = config.get("newsstand_id")
        feed_id = config.get("feed_id")
        client_id = config.get("client_id")
        
        # Save output directory preference
        output_dir = self.output_dir_input.text().strip()
        config["last_output_dir"] = output_dir
        save_config(config)
        
        api_manager = APIManager(api_url=server_url, client_id=client_id)
        client_secret = api_manager.get_credentials()
        
        if not self.project_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Project Name is required.")
            return
        if not self.output_dir_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Output Directory is required.")
            return

        self.fetch_btn.setEnabled(False)
        self.log_browser.clear()
        self.log_browser.append("Starting automated build process...")

        # Launch QThread background worker
        self.worker = AutomatorWorker(
            api_url=server_url,
            client_id=client_id,
            client_secret=client_secret,
            project_name=self.project_name_input.text().strip(),
            output_dir=self.output_dir_input.text().strip(),
            newsstand_id=newsstand_id,
            publication_id=str(pub_id),
            issue_id=str(issue_id),
            feed_id=feed_id
        )

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
            
            # Save downloaded issue to history
            pub_idx = self.publication_combo.currentIndex()
            issue_idx = self.issue_combo.currentIndex()
            if pub_idx >= 0 and issue_idx >= 0:
                pub_id = self.publication_combo.itemData(pub_idx)
                issue_id = self.issue_combo.itemData(issue_idx)
                if issue_id:
                    issue = self.issues_map.get(issue_id)
                    if issue:
                        history = load_download_history()
                        history[str(issue_id)] = {
                            "content_revision": issue.get("content_revision", ""),
                            "modified_at": issue.get("modified_at", ""),
                            "downloaded_at": datetime.datetime.now().isoformat()
                        }
                        save_download_history(history)
                        
                        # Refresh issue dropdown to remove [NEW ISSUE]/[UPDATE AVAILABLE] tags
                        self.on_publication_selected(pub_idx)
                        
                        # Reselect the downloaded issue
                        for idx in range(self.issue_combo.count()):
                            if self.issue_combo.itemData(idx) == issue_id:
                                self.issue_combo.blockSignals(True)
                                self.issue_combo.setCurrentIndex(idx)
                                self.issue_combo.blockSignals(False)
                                break
        else:
            QMessageBox.critical(self, "Process Failed", f"Automation process failed: {message}")
