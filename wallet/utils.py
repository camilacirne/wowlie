from pathlib import Path
import json, os

WALLET_DIR = Path.home() / ".wowlie"
WALLET_FILE = WALLET_DIR / "wallet.json"

def ensure_dirs():
    WALLET_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(WALLET_DIR, 0o700)
    except Exception:
        pass

def save_wallet(data: dict):
    ensure_dirs()
    with open(WALLET_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(WALLET_FILE, 0o600)

def load_wallet() -> dict:
    if not WALLET_FILE.exists():
        raise FileNotFoundError("Wallet não inicializada. Rode: python cli.py init")
    with open(WALLET_FILE) as f:
        return json.load(f)