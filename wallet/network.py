import requests

API = "https://blockstream.info/testnet/api"

def get_address_info(address: str) -> dict:
    r = requests.get(f"{API}/address/{address}", timeout=20)
    r.raise_for_status()
    return r.json()

def get_utxos(address: str) -> list:
    r = requests.get(f"{API}/address/{address}/utxo", timeout=20)
    r.raise_for_status()
    return r.json()

def get_balance(address: str) -> dict:
    info = get_address_info(address)
    chain = info.get("chain_stats", {})
    mem = info.get("mempool_stats", {})
    confirmed = int(chain.get("funded_txo_sum", 0)) - int(chain.get("spent_txo_sum", 0))
    unconfirmed = int(mem.get("funded_txo_sum", 0)) - int(mem.get("spent_txo_sum", 0))
    return {
        "confirmed": confirmed,
        "unconfirmed": unconfirmed,
        "total": confirmed + unconfirmed,
    }

def broadcast_tx(raw_tx_hex: str) -> str:
    r = requests.post(f"{API}/tx", data=raw_tx_hex, timeout=30,
                      headers={"Content-Type": "text/plain"})
    r.raise_for_status()
    return r.text.strip()  
