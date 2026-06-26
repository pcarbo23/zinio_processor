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
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(result.stdout.strip())

def get_integrated_loudness_lufs(file_path: str) -> float:
    """
    Retrieves the integrated loudness of an audio file in LUFS using ffmpeg's loudnorm filter.
    
    Args:
        file_path: Absolute path to the audio file.
        
    Returns:
        Integrated loudness in LUFS as a float.
    """
    cmd = [
        "ffmpeg",
        "-i", file_path,
        "-filter:a", "loudnorm=print_format=json",
        "-f", "null",
        "-"
    ]
    # ffmpeg output for filters goes to stderr
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Extract the JSON block from stderr
    stderr_content = result.stderr
    # Locate the json block starting with { and ending with }
    match = re.search(r"\{.*?\}", stderr_content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract loudness information from ffmpeg output for {file_path}")
        
    loudnorm_data = json.loads(match.group(0))
    return float(loudnorm_data["input_i"])

def parse_audio_dir(audio_dir: str) -> list[dict]:
    """
    Iterates through a target directory of audio files, extracts exact duration
    in milliseconds, and validates integrated loudness is -22 LUFS (+/- 2 LU).
    
    Args:
        audio_dir: Target directory containing WAV/audio files.
        
    Returns:
        A list of dictionaries containing:
        - 'filename': name of the file
        - 'absolute_path': absolute path to the file
        - 'duration': duration of the file in milliseconds (float)
        
    Raises:
        ValueError: If any audio file fails the loudness validation (-22 +/- 2 LUFS).
    """
    if not os.path.isdir(audio_dir):
        raise FileNotFoundError(f"Audio directory not found: {audio_dir}")
        
    results = []
    # Fetch all WAV files in alphabetical order
    files = sorted([f for f in os.listdir(audio_dir) if f.lower().endswith(".wav")])
    
    for filename in files:
        file_path = os.path.join(audio_dir, filename)
        
        # 1. Get exact duration in seconds, convert to milliseconds
        duration_sec = get_audio_duration_seconds(file_path)
        duration_ms = duration_sec * 1000.0
        
        # 2. Get integrated loudness and validate
        loudness = get_integrated_loudness_lufs(file_path)
        if not (-24.0 <= loudness <= -20.0):
            raise ValueError(
                f"Audio file '{filename}' failed loudness validation. "
                f"Loudness was {loudness} LUFS, but must be -22 LUFS (+/- 2 LU)."
            )
            
        results.append({
            "filename": filename,
            "absolute_path": file_path,
            "duration": duration_ms
        })
        
    return results
