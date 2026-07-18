import os
import subprocess
import json
import re

def get_audio_duration_seconds(file_path: str) -> float:
    """
    Retrieves the duration of an audio file in seconds using ffprobe.
    
    Args:
        file_path: Absolute path to the audio file.
        
    Returns:
        Duration as a float in seconds.
    """
    file_path = os.path.normpath(file_path)
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except FileNotFoundError:
        raise RuntimeError("ffprobe executable not found. Please ensure that ffmpeg and ffprobe are installed and added to your system's PATH environment variable.")

def get_integrated_loudness_lufs(file_path: str) -> float:
    """
    Retrieves the integrated loudness of an audio file in LUFS using ffmpeg's loudnorm filter.
    
    Args:
        file_path: Absolute path to the audio file.
        
    Returns:
        Integrated loudness in LUFS as a float.
    """
    file_path = os.path.normpath(file_path)
    cmd = [
        "ffmpeg",
        "-i", file_path,
        "-filter:a", "loudnorm=print_format=json",
        "-f", "null",
        "-"
    ]
    # ffmpeg output for filters goes to stderr
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        raise RuntimeError("ffmpeg executable not found. Please ensure that ffmpeg and ffprobe are installed and added to your system's PATH environment variable.")
    
    # Extract the JSON block from stderr
    stderr_content = result.stderr
    # Locate the json block starting with { and ending with }
    match = re.search(r"\{.*?\}", stderr_content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract loudness information from ffmpeg output for {file_path}")
        
    loudnorm_data = json.loads(match.group(0))
    return float(loudnorm_data["input_i"])

def parse_audio_dir(audio_dir: str, logger=None) -> list[dict]:
    """
    Iterates through a target directory of audio files, extracts exact duration
    in milliseconds, and logs the integrated loudness.
    
    Args:
        audio_dir: Target directory containing WAV/audio files.
        logger: Optional ProcessLogger instance to record details.
        
    Returns:
        A list of dictionaries containing:
        - 'filename': name of the file
        - 'absolute_path': absolute path to the file
        - 'duration': duration of the file in milliseconds (float)
    """
    if not os.path.isdir(audio_dir):
        msg = f"Audio directory not found: {audio_dir}"
        if logger:
            logger.log(msg, level="ERROR")
        raise FileNotFoundError(msg)
        
    results = []
    # Fetch all WAV files in alphabetical order
    files = sorted([f for f in os.listdir(audio_dir) if f.lower().endswith(".wav")])
    
    if logger:
        logger.log(f"Starting audio parsing in directory: {audio_dir}")
        logger.log(f"Found {len(files)} WAV files to parse.")
    
    for filename in files:
        file_path = os.path.normpath(os.path.join(audio_dir, filename))
        
        # 1. Get exact duration in seconds, convert to milliseconds
        try:
            duration_sec = get_audio_duration_seconds(file_path)
            duration_ms = duration_sec * 1000.0
        except Exception as e:
            msg = f"Failed to get duration for '{filename}': {str(e)}"
            if logger:
                logger.log(msg, level="ERROR")
            raise
        
        # 2. Get integrated loudness and log it
        try:
            loudness = get_integrated_loudness_lufs(file_path)
            is_valid = (-24.0 <= loudness <= -20.0)
            status_symbol = "✓" if is_valid else "✗"
            log_msg = f"File: {filename} | Loudness: {loudness} LUFS | Target range (-22 +/- 2 LUFS): {status_symbol}"
            
            if logger:
                if is_valid:
                    logger.log(log_msg, level="INFO")
                else:
                    logger.log(log_msg, level="WARNING")
        except Exception as e:
            # Fallback if loudness parse fails, we still keep duration
            loudness = None
            log_msg = f"File: {filename} | Loudness check failed: {str(e)}"
            if logger:
                logger.log(log_msg, level="WARNING")
            
        results.append({
            "filename": filename,
            "absolute_path": file_path,
            "duration": duration_ms,
            "loudness": loudness
        })
        
    if logger:
        logger.log("Audio directory parsing completed.")
        
    return results
