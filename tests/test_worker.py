import pytest
import tempfile
from unittest.mock import patch, MagicMock
from src.gui.worker import AutomatorWorker

def test_worker_execution_flow():
    # Mock all backend systems to isolate the thread loop
    with patch("src.gui.worker.APIManager") as mock_api_mgr, \
         patch("src.gui.worker.MockDownloader") as mock_downloader, \
         patch("src.gui.worker.parse_audio_dir", return_value=[]) as mock_parser, \
         patch("src.gui.worker.write_boilerplate_css") as mock_css, \
         patch("src.gui.worker.generate_document_xhtml") as mock_xhtml, \
         patch("src.gui.worker.compile_hindenburg_session") as mock_nhsx:
         
         # Mock manager instance
         mgr_instance = MagicMock()
         mgr_instance.get_session_token.return_value = "token123"
         mock_api_mgr.return_value = mgr_instance
         
         # Mock downloader instance
         dl_instance = MagicMock()
         dl_instance.fetch_and_unpack.return_value = "/tmp/mag_files"
         mock_downloader.return_value = dl_instance
         
         # Initialize worker
         with tempfile.TemporaryDirectory() as tmpdir:
             worker = AutomatorWorker(
                 api_url="https://httpbin.org/post",
                 username="user",
                 password="pwd",
                 project_name="mag_name",
                 output_dir=tmpdir
             )
             
             # Connect mock slots
             mock_finished = MagicMock()
             worker.finished_signal.connect(mock_finished)
             
             # Call synchronously for testing (avoiding Qt event loop threading complications)
             worker.run()
             
             # Check backend invocations
             mock_api_mgr.assert_called_with(username="user")
             mgr_instance.store_credentials.assert_called_with("pwd")
             dl_instance.fetch_and_unpack.assert_called_with("https://httpbin.org/post", "token123", "mag_name", tmpdir)
             mock_parser.assert_called_once()
             mock_css.assert_called_with(tmpdir)
             mock_xhtml.assert_called_once()
             mock_nhsx.assert_called_once()
             
             # Verify signal emits
             mock_finished.assert_called_with(True, "Project compiled successfully.")

def test_worker_failure_flow():
    with patch("src.gui.worker.APIManager") as mock_api_mgr:
        # Simulate authentication failure
        mgr_instance = MagicMock()
        mgr_instance.get_session_token.side_effect = RuntimeError("Auth server is offline")
        mock_api_mgr.return_value = mgr_instance
        
        with tempfile.TemporaryDirectory() as tmpdir:
            worker = AutomatorWorker(
                api_url="https://httpbin.org/post",
                username="user",
                password="pwd",
                project_name="mag_name",
                output_dir=tmpdir
            )
            
            mock_finished = MagicMock()
            worker.finished_signal.connect(mock_finished)
            
            worker.run()
            
            # Should have failed
            mock_finished.assert_called_with(False, "Auth server is offline")
            assert worker.logger.api_status == "FAILED (Auth server is offline)"
