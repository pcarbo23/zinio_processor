import os
import pytest
from unittest.mock import patch, MagicMock
from src.core.audio_parser import parse_audio_dir, get_audio_duration_seconds, get_integrated_loudness_lufs

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

def test_parse_audio_dir_success():
    with patch("src.core.audio_parser.get_audio_duration_seconds", return_value=1.5) as mock_dur, \
         patch("src.core.audio_parser.get_integrated_loudness_lufs", return_value=-22.5) as mock_loud, \
         patch("os.listdir", return_value=["002_author.wav", "001_title.wav"]) as mock_list, \
         patch("os.path.isdir", return_value=True):
         
         results = parse_audio_dir("dummy_dir")
         
         # Verification
         assert len(results) == 2
         # Should be sorted alphabetically
         assert results[0]["filename"] == "001_title.wav"
         assert results[0]["duration"] == 1500.0  # converted to ms
         assert results[1]["filename"] == "002_author.wav"
         assert results[1]["duration"] == 1500.0
         
def test_parse_audio_dir_validation_error():
    with patch("src.core.audio_parser.get_audio_duration_seconds", return_value=10.0), \
         patch("src.core.audio_parser.get_integrated_loudness_lufs", return_value=-18.0), \
         patch("os.listdir", return_value=["test1.wav"]), \
         patch("os.path.isdir", return_value=True):
        
        with pytest.raises(ValueError) as excinfo:
            parse_audio_dir("dummy_dir")
        assert "failed loudness validation" in str(excinfo.value)
