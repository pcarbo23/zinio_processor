import os
import json

USER_DIR = os.path.normpath(os.path.join(os.path.expanduser("~"), ".zinio_processor"))
os.makedirs(USER_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(USER_DIR, "config.json")

DEFAULT_CONFIG = {
    "server_url": "",
    "newsstand_id": "",
    "feed_id": "",
    "client_id": ""
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all keys are present
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

HISTORY_FILE = os.path.join(os.path.dirname(CONFIG_FILE), "download_history.json")

def load_download_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_download_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    except Exception:
        pass
