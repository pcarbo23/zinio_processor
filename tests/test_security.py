import pytest
import datetime
from unittest.mock import patch, MagicMock
from src.utils.security import APIManager

def test_store_and_get_credentials():
    with patch("keyring.set_password") as mock_set, \
         patch("keyring.get_password", return_value="mypaswd") as mock_get:
        
        manager = APIManager("testuser")
        manager.store_credentials("mypaswd")
        mock_set.assert_called_with("HindenburgAutomator", "testuser", "mypaswd")
        
        creds = manager.get_credentials()
        assert creds == "mypaswd"
        mock_get.assert_called_with("HindenburgAutomator", "testuser")

def test_is_token_expired():
    manager = APIManager()
    assert manager.is_token_expired() is True  # No token yet
    
    manager.session_token = "token123"
    manager.token_timestamp = datetime.datetime.now()
    assert manager.is_token_expired() is False
    
    # Simulating 3 hours ago
    manager.token_timestamp = datetime.datetime.now() - datetime.timedelta(hours=3)
    assert manager.is_token_expired() is True

def test_get_session_token_silent_refresh():
    manager = APIManager("testuser")
    
    with patch.object(manager, "get_credentials", return_value="mypassword"), \
         patch("requests.post") as mock_post:
        
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"args": {}}
        mock_post.return_value = mock_resp
        
        # Initial call should trigger authenticate
        token1 = manager.get_session_token()
        assert token1.startswith("mock_token_session_")
        assert mock_post.call_count == 1
        
        # Second call within expiry should NOT trigger authenticate
        token2 = manager.get_session_token()
        assert token2 == token1
        assert mock_post.call_count == 1
        
        # Artificially expire the token
        manager.token_timestamp = datetime.datetime.now() - datetime.timedelta(hours=3)
        token3 = manager.get_session_token()
        assert token3.startswith("mock_token_session_")
        assert mock_post.call_count == 2
