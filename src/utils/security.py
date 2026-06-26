import keyring
import requests
import datetime
import time

class APIManager:
    """
    Manages secure API credential storage using the keyring library,
    authenticates to a mock endpoint (httpbin.org), caches the session token,
    and refreshes the token silently if it is expired (older than 2 hours).
    """
    SERVICE_NAME = "HindenburgAutomator"
    TOKEN_EXPIRY_SECONDS = 7200  # 2 hours

    def __init__(self, username: str = "default_user"):
        self.username = username
        self.session_token = None
        self.token_timestamp = None

    def store_credentials(self, password: str):
        """
        Securely stores the API password/token using the OS-native keyring.
        """
        keyring.set_password(self.SERVICE_NAME, self.username, password)
        # Invalidate current cached token
        self.session_token = None
        self.token_timestamp = None

    def get_credentials(self) -> str:
        """
        Retrieves the securely stored API password/token.
        """
        return keyring.get_password(self.SERVICE_NAME, self.username)

    def delete_credentials(self):
        """
        Deletes stored credentials from keyring.
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, self.username)
        except keyring.errors.PasswordDeleteError:
            pass
        self.session_token = None
        self.token_timestamp = None

    def is_token_expired(self) -> bool:
        """
        Checks if the cached session token is missing or has expired.
        """
        if not self.session_token or not self.token_timestamp:
            return True
        elapsed = (datetime.datetime.now() - self.token_timestamp).total_seconds()
        return elapsed >= self.TOKEN_EXPIRY_SECONDS

    def authenticate(self) -> str:
        """
        Authenticates against the API endpoint using stored credentials
        and returns a new session token.
        """
        password = self.get_credentials()
        if not password:
            raise ValueError("No credentials found. Please set credentials first.")

        # HTTPBin mockup API request
        url = "https://httpbin.org/post"
        payload = {
            "username": self.username,
            "password": password
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            # Simulated response details from httpbin
            data = response.json()
            # We generate a mockup session token based on mock payload validation
            self.session_token = f"mock_token_session_{int(time.time())}"
            self.token_timestamp = datetime.datetime.now()
            return self.session_token
            
        except requests.RequestException as e:
            raise RuntimeError(f"Authentication failed: {str(e)}")

    def get_session_token(self) -> str:
        """
        Retrieves the active session token, executing silent re-authentication
        if the token has expired.
        """
        if self.is_token_expired():
            # Silent refresh
            return self.authenticate()
        return self.session_token
