import os
import tempfile
from src.utils.logger import ProcessLogger

def test_process_logger():
    logger = ProcessLogger()
    logger.log("Hello log")
    logger.set_api_info("http://httpbin.org/get", "200 OK")
    logger.set_zip_name("test.zip")
    logger.set_task_status("Extraction", True)
    logger.set_task_status("XML Building", False, "Missing tags")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = logger.write_to_file(tmpdir)
        assert os.path.exists(log_path)
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Execution Date/Time" in content
        assert "Operating System" in content
        assert "http://httpbin.org/get" in content
        assert "test.zip" in content
        assert "Extraction: SUCCESS" in content
        assert "XML Building: FAILED (Missing tags)" in content
        assert "Hello log" in content
