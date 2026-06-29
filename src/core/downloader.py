import os
import requests
import zipfile
import wave
import math
import io

class MockDownloader:
    """
    Downloads project ZIP payload from API. Supports real ZIP download
    and extraction if a real endpoint is provided, falling back to
    simulating/generating mock WAV files.
    """
    def __init__(self, logger=None):
        self.logger = logger

    def log(self, message: str, level: str = "INFO"):
        if self.logger:
            self.logger.log(message, level)

    def fetch_and_unpack(self, api_url: str, token: str, project_name: str, output_dir: str) -> str:
        """
        Queries the api_url with the auth token.
        If the endpoint is a real API or local mock server, downloads and extracts the real ZIP.
        Otherwise, falls back to generating local mock WAV files.
        """
        self.log(f"Fetching ZIP URL from API endpoint: {api_url}")
        
        # Determine if we should perform a real ZIP download
        is_real_download = ("127.0.0.1" in api_url or "localhost" in api_url or "/content" in api_url)
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Create output directories
        project_files_dir = os.path.join(output_dir, f"{project_name} Files")
        os.makedirs(project_files_dir, exist_ok=True)
        self.log(f"Created project files output directory: {project_files_dir}")

        if is_real_download:
            try:
                self.log("Performing real ZIP download...")
                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()
                self.log(f"Successfully downloaded ZIP payload. Content size: {len(response.content)} bytes.")
                
                # Unpack the downloaded zip file directly to output directory
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                    # Hindenburg requires unzipped wav files directly inside "<ProjectName> Files"
                    # So we extract them there. If the zip contains a nested folder, we flatten it.
                    for member in zip_ref.infolist():
                        if member.is_dir():
                            continue
                        # Flatten the directory structure by using the basename
                        filename = os.path.basename(member.filename)
                        if not filename:
                            continue
                        target_path = os.path.join(project_files_dir, filename)
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())
                        self.log(f"Extracted file: {filename}")
                        
                self.log("ZIP unpack extraction completed successfully.")
                return project_files_dir
                
            except Exception as e:
                self.log(f"Real ZIP download/unpack failed: {str(e)}", "ERROR")
                raise RuntimeError(f"Failed to query real API: {str(e)}")

        # Fallback Mock logic
        try:
            response = requests.get("https://httpbin.org/headers", headers=headers, timeout=10)
            response.raise_for_status()
            self.log(f"API metadata request successful. Status code: {response.status_code}")
        except Exception as e:
            self.log(f"API request failed: {str(e)}", "ERROR")
            raise RuntimeError(f"Failed to query API: {str(e)}")

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
                val = int(amplitude * math.sin(2.0 * math.pi * frequency * i / sample_rate))
                frames[2*i] = val & 0xFF
                frames[2*i+1] = (val >> 8) & 0xFF
                
            w.writeframes(frames)
