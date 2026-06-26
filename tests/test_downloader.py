import os
import tempfile
import pytest
from src.core.downloader import MockDownloader
from src.utils.logger import ProcessLogger

def test_mock_downloader():
    logger = ProcessLogger()
    downloader = MockDownloader(logger=logger)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        files_dir = downloader.fetch_and_unpack(
            api_url="https://httpbin.org/get",
            token="dummy_token",
            project_name="TestProject",
            output_dir=tmpdir
        )
        
        assert os.path.exists(files_dir)
        assert os.path.basename(files_dir) == "TestProject Files"
        
        # Verify wav files were generated
        wavs = [f for f in os.listdir(files_dir) if f.endswith(".wav")]
        assert len(wavs) == 5
        assert "001 docTitle Title.wav" in wavs
        
        # Verify log statements exist
        assert any("Simulating ZIP download" in log for log in logger.logs)
