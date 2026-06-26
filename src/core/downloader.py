import os
import requests
import zipfile
import wave
import math
import io

class MockDownloader:
    """
    Downloads project ZIP payload from API. Since we are in mockup phase,
    this queries httpbin.org and unpacks a set of dynamically generated mock
    WAV files directly to the output directory to simulate unzipping.
    """
    def __init__(self, logger=None):
        self.logger = logger

    def log(self, message: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(message, level)

    def fetch_and_unpack(self, api_url: str, token: str, project_name: str, output_dir: str) -> str:
        """
        Queries the api_url with the auth token.
        Generates mock audio files and unzips them into output_dir/<ProjectName> Files/
        """
        self.log(f"Fetching ZIP URL from API endpoint: {api_url}")
        
        # Call mock API using HTTPBin
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get("https://httpbin.org/headers", headers=headers, timeout=10)
            response.raise_for_status()
            self.log(f"API metadata request successful. Status code: {response.status_code}")
        except Exception as e:
            self.log(f"API request failed: {str(e)}", "ERROR")
            raise RuntimeError(f"Failed to query API: {str(e)}")

        # Create output directories
        project_files_dir = os.path.join(output_dir, f"{project_name} Files")
        os.makedirs(project_files_dir, exist_ok=True)
        self.log(f"Created project files output directory: {project_files_dir}")

        # Generate a list of mockup WAV filenames conforming to the spec
        mock_files = [
            ("001 docTitle Title.wav", 1.0),
            ("002 docAuthor Author Name.wav", 1.0),
            ("003 World News – Europe.wav", 2.0),
            ("004 World News – Asia.wav", 1.5),
            ("005 Standalone Article.wav", 1.0)
        ]

        self.log("Simulating ZIP download and extraction...")
        # Create WAV files programmatically
        for filename, duration in mock_files:
            file_path = os.path.join(project_files_dir, filename)
            self._write_sine_wav(file_path, duration)
            self.log(f"Extracted file: {filename} ({duration}s)")

        self.log("ZIP unpack extraction completed successfully.")
        return project_files_dir

    def _write_sine_wav(self, file_path: str, duration_sec: float):
        """
        Generates a valid mono WAV file containing a 440Hz sine wave
        """
        sample_rate = 44100
        amplitude = 10000  # volume level
        frequency = 440.0
        
        with wave.open(file_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            
            num_samples = int(sample_rate * duration_sec)
            frames = bytearray(num_samples * 2)
            
            for i in range(num_samples):
                # Calculate sine wave value
                val = int(amplitude * math.sin(2.0 * math.pi * frequency * i / sample_rate))
                # pack as signed 16-bit little endian
                frames[2*i] = val & 0xFF
                frames[2*i+1] = (val >> 8) & 0xFF
                
            w.writeframes(frames)
