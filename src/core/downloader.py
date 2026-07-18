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

    def fetch_and_unpack(self, api_url: str, token: str, project_name: str, output_dir: str, newsstand_id: str = None, issue_id: str = None, feed_id: str = None) -> str:
        """
        Queries the api_url with the auth token.
        If newsstand_id, issue_id, and feed_id are provided, retrieves the download URL from the feed endpoint,
        then downloads and extracts the real ZIP.
        Otherwise, falls back to generating local mock WAV files.
        """
        self.log(f"Fetching ZIP URL from API endpoint: {api_url}")
        
        # Determine if we should perform a real ZIP download
        is_real_download = ("127.0.0.1" in api_url or "localhost" in api_url or "/content" in api_url or (newsstand_id and issue_id))
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Create output directories
        project_files_dir = os.path.normpath(os.path.join(output_dir, f"{project_name} Files"))
        os.makedirs(project_files_dir, exist_ok=True)
        self.log(f"Created project files output directory: {project_files_dir}")

        if is_real_download:
            try:
                download_target_url = api_url
                if newsstand_id and issue_id and feed_id:
                    # Target the v3 endpoint as per documentation
                    feed_endpoint = f"{api_url}/newsstand/v3/newsstands/{newsstand_id}/issues/{issue_id}/content/feed/{feed_id}"
                    self.log(f"Querying Feed endpoint: {feed_endpoint}")
                    feed_resp = requests.get(feed_endpoint, headers=headers, timeout=15)
                    
                    if feed_resp.status_code != 200:
                        try:
                            err_json = feed_resp.json()
                            self.log(f"Feed endpoint returned error JSON (Status {feed_resp.status_code}): {err_json}", "ERROR")
                            raise RuntimeError(f"Feed endpoint error response: {err_json}")
                        except ValueError:
                            self.log(f"Feed endpoint returned error status {feed_resp.status_code}: {feed_resp.text}", "ERROR")
                            feed_resp.raise_for_status()
                        
                    feed_data = feed_resp.json()
                    
                    if "data" in feed_data and isinstance(feed_data["data"], dict) and "url" in feed_data["data"]:
                        download_target_url = feed_data["data"]["url"]
                    elif "download_url" in feed_data:
                        download_target_url = feed_data["download_url"]
                    else:
                        raise RuntimeError(f"Feed response did not return a valid download URL: {feed_data}")
                    display_url = download_target_url
                    if "com.ziniopro.console.ore.prod.storage" in display_url:
                        idx = display_url.find("com.ziniopro.console.ore.prod.storage/")
                        if idx != -1:
                            display_url = display_url[:idx + len("com.ziniopro.console.ore.prod.storage/")]
                    self.log(f"Resolved download URL from feed: {display_url}")

                display_url = download_target_url
                if "com.ziniopro.console.ore.prod.storage" in display_url:
                    idx = display_url.find("com.ziniopro.console.ore.prod.storage/")
                    if idx != -1:
                        display_url = display_url[:idx + len("com.ziniopro.console.ore.prod.storage/")]
                self.log(f"Performing ZIP download from: {display_url}")
                # Omit Authorization header for Amazon S3 pre-signed URLs to prevent 400 Bad Request
                download_headers = {} if "amazonaws.com" in download_target_url else headers
                response = requests.get(download_target_url, headers=download_headers, timeout=60)
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
                        target_path = os.path.normpath(os.path.join(project_files_dir, filename))
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())
                        self.log(f"Extracted file: {filename}")
                        
                self.log("ZIP unpack extraction completed successfully.")
                return project_files_dir
                
            except Exception as e:
                self.log(f"ZIP download/unpack failed: {str(e)}", "ERROR")
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
