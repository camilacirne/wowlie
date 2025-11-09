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
    try:
        os.chmod(WALLET_FILE, 0o600)  
    except Exception:
        pass

def load_wallet() -> dict:
    if not WALLET_FILE.exists():
        raise FileNotFoundError("Wallet não inicializada. Rode: python cli.py init")
    with open(WALLET_FILE) as f:
        return json.load(f)

def wallet_exists() -> bool:
    return WALLET_FILE.exists()


def wallet_exists() -> bool:
    try:
        load_wallet()
        return True
    except Exception:
        return False

def load_addresses():
  
    try:
        w = load_wallet()
        idxs = sorted(map(int, w.get("addresses", {}).keys()))
        addrs = [w["addresses"][str(i)]["address"] for i in idxs]
        return idxs, addrs, w
    except Exception:
        return [], [], None
