import os
import traceback
from PySide6.QtCore import QThread, Signal
from src.utils.security import APIManager
from src.core.downloader import MockDownloader
from src.core.audio_parser import parse_audio_dir
from src.core.xml_generator import (
    write_boilerplate_css,
    generate_document_xhtml,
    compile_hindenburg_session
)
from src.utils.logger import ProcessLogger
from src.utils.api_metadata import fetch_and_parse_metadata

class AutomatorWorker(QThread):
    """
    QThread background worker that coordinates the complete Hindenburg session pipeline:
    1. Authenticates against the target API.
    2. Downloads and unzips raw WAV files.
    3. Extracts audio file durations and validates LUFS loudness values.
    4. Compiles .xhtml, .css, and .nhsx XML project outputs.
    5. Saves a timestamped execution log.
    """
    log_signal = Signal(str)
    status_signal = Signal(str)
    finished_signal = Signal(bool, str)  # (success, message)

    def __init__(self, api_url: str, client_id: str, client_secret: str, project_name: str, output_dir: str,
                 newsstand_id: str = None, publication_id: str = None, issue_id: str = None, feed_id: str = None):
        super().__init__()
        self.api_url = api_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.project_name = project_name
        self.output_dir = output_dir
        self.newsstand_id = newsstand_id
        self.publication_id = publication_id
        self.issue_id = issue_id
        self.feed_id = feed_id
        self.logger = ProcessLogger()

    def run(self):
        self.logger.log("Zinio Media Processor execution thread started.")
        self.status_signal.emit("Status: Running...")
        
        try:
            # 1. API Authentication
            self.status_signal.emit("Status: Authenticating...")
            self.log_signal.emit("Configuring secure keyring manager and authenticating...")
            api_manager = APIManager(api_url=self.api_url, client_id=self.client_id)
            if self.client_secret:
                api_manager.store_credentials(self.client_secret)
            token = api_manager.get_session_token()
            self.logger.set_api_info(self.api_url, "200 OK (Authenticated)")
            self.log_signal.emit(f"Authentication token acquired: {token[:15]}...")
            self.logger.set_task_status("Authentication", True)
            
            # Fetch metadata from API if publication_id is provided
            metadata_dict = {}
            if self.newsstand_id and self.publication_id and self.issue_id:
                try:
                    self.log_signal.emit("Fetching publication and issue metadata from Zinio API...")
                    metadata_dict = fetch_and_parse_metadata(
                        api_url=self.api_url,
                        token=token,
                        newsstand_id=self.newsstand_id,
                        publication_id=self.publication_id,
                        issue_id=self.issue_id
                    )
                    self.log_signal.emit(f"Metadata successfully fetched. Title: {metadata_dict.get('Title')}")
                except Exception as e:
                    self.log_signal.emit(f"[WARNING] Failed to fetch API metadata: {e}. Falling back to default values.")

            # Helper to redirect downloader & parser logging output to both process logs and the GUI
            original_log = self.logger.log
            def gui_redirect_logger(msg, level="INFO"):
                original_log(msg, level)
                self.log_signal.emit(f"[{level}] {msg}")
                
            # Create a duck-typed logger wrapper
            proxy_logger = type('ProxyLogger', (object,), {"log": staticmethod(gui_redirect_logger)})()
            
            # 2. Fetch and extract WAV payload
            self.status_signal.emit("Status: Extracting payload...")
            downloader = MockDownloader(logger=proxy_logger)
            self.logger.set_zip_name(f"{self.project_name}.zip")
            
            # The project should always be stored in a new directory named with the same content as Basefile (i.e. self.project_name)
            project_output_dir = os.path.join(self.output_dir, self.project_name)
            os.makedirs(project_output_dir, exist_ok=True)
            
            audio_files_dir = downloader.fetch_and_unpack(
                self.api_url, token, self.project_name, project_output_dir,
                newsstand_id=self.newsstand_id, issue_id=self.issue_id, feed_id=self.feed_id
            )
            self.logger.set_task_status("Extraction", True)
            
            # 3. Audio duration extraction & loudness logging
            self.status_signal.emit("Status: Analyzing audio...")
            self.log_signal.emit("Starting ffprobe/ffmpeg audio analysis...")
            
            audio_data = parse_audio_dir(audio_files_dir, logger=proxy_logger)
            self.logger.set_task_status("Audio Parsing", True)
            
            # 4. XML Project generation & static assets writes
            self.status_signal.emit("Status: Compiling Hindenburg Session...")
            self.log_signal.emit("Writing style.css stylesheet...")
            write_boilerplate_css(audio_files_dir)
            
            self.log_signal.emit("Generating Document.xhtml flow...")
            metadata = {
                "title": metadata_dict.get("Title", self.project_name),
                "creator": self.client_id,
                "language": metadata_dict.get("Language", "en"),
                "source_publisher": metadata_dict.get("SourcePublisher", ""),
                "description": metadata_dict.get("Description", ""),
                "source_date": metadata_dict.get("SourceDate", ""),
                "source_rights": metadata_dict.get("SourceRights", ""),
                "basefile": metadata_dict.get("BaseFile", self.project_name),
                "identifier": metadata_dict.get("Identifier", f"us-nls-dm-{self.project_name}")
            }
            generate_document_xhtml(audio_data, metadata, audio_files_dir)
            
            self.log_signal.emit("Generating Session.nhsx timeline project...")
            compile_hindenburg_session(audio_data, metadata, project_output_dir, self.project_name)
            self.logger.set_task_status("XML Compilation", True)
            self.logger.set_task_status("Overall Process", True)
            
            # 5. Output dynamic log file
            log_path = self.logger.write_to_file(project_output_dir)
            self.log_signal.emit(f"Session execution log written successfully to: {log_path}")
            
            self.status_signal.emit("Status: Finished successfully")
            self.finished_signal.emit(True, "Project compiled successfully.")
            
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.set_api_info(self.api_url, f"FAILED ({str(e)})")
            self.logger.log(f"Execution failed: {str(e)}\n{tb}", "ERROR")
            self.log_signal.emit(f"[ERROR] Execution failed: {str(e)}")
            self.logger.set_task_status("Overall Process", False, str(e))
            
            try:
                log_path = self.logger.write_to_file(self.output_dir)
                self.log_signal.emit(f"Session execution log written to: {log_path}")
            except Exception:
                pass
                
            self.status_signal.emit("Status: Execution failed")
            self.finished_signal.emit(False, str(e))
