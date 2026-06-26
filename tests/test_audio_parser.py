import os
import pytest
from unittest.mock import patch, MagicMock
from src.core.audio_parser import parse_audio_dir, get_audio_duration_seconds, get_integrated_loudness_lufs
from src.utils.logger import ProcessLogger

def test_get_audio_duration_seconds():
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = " 12.345 \n"
        mock_run.return_value = mock_result
        
        duration = get_audio_duration_seconds("dummy.wav")
        assert duration == 12.345
        mock_run.assert_called_once()

def test_get_integrated_loudness_lufs():
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stderr = """
        [parsed_loudnorm_0 @ 0x7fa812804500] {
            "input_i" : "-21.50",
            "input_tp" : "-1.00",
            "input_lra" : "5.0",
            "input_thresh" : "-32.1",
            "output_i" : "-22.0",
            "output_tp" : "-2.0",
            "output_lra" : "5.0",
            "output_thresh" : "-32.0",
            "normalization_type" : "dynamic",
            "target_offset" : "0.0"
        }
        """
        mock_run.return_value = mock_result
        
        loudness = get_integrated_loudness_lufs("dummy.wav")
        assert loudness == -21.5

def test_parse_audio_dir_success_with_logger():
    logger = ProcessLogger()
    with patch("src.core.audio_parser.get_audio_duration_seconds", return_value=1.5), \
         patch("src.core.audio_parser.get_integrated_loudness_lufs", return_value=-22.5), \
         patch("os.listdir", return_value=["002_author.wav", "001_title.wav"]), \
         patch("os.path.isdir", return_value=True):
         
         results = parse_audio_dir("dummy_dir", logger=logger)
         
         assert len(results) == 2
         assert results[0]["filename"] == "001_title.wav"
         assert results[0]["duration"] == 1500.0  # converted to ms
         assert results[0]["loudness"] == -22.5
         
         # Check that logging occurred
         assert any("001_title.wav" in msg for msg in logger.logs)
         assert any("Starting audio parsing" in msg for msg in logger.logs)

def test_parse_audio_dir_out_of_bounds_no_error():
    logger = ProcessLogger()
    # Out of bounds loudness (-18.0 LUFS) should NOT raise error but should log a warning
    with patch("src.core.audio_parser.get_audio_duration_seconds", return_value=10.0), \
         patch("src.core.audio_parser.get_integrated_loudness_lufs", return_value=-18.0), \
         patch("os.listdir", return_value=["out_of_bounds.wav"]), \
         patch("os.path.isdir", return_value=True):
        
        results = parse_audio_dir("dummy_dir", logger=logger)
        assert len(results) == 1
        assert results[0]["loudness"] == -18.0
        
        # Check that warning level/symbol is captured
        warning_logs = [msg for msg in logger.logs if "[WARNING]" in msg]
        assert len(warning_logs) == 1
        assert "out_of_bounds.wav" in warning_logs[0]
        assert "✗" in warning_logs[0]
