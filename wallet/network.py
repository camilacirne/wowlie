import requests

API = "https://blockstream.info/testnet/api"

def get_balance(address: str):
    r = requests.get(f"{API}/address/{address}")
    r.raise_for_status()
    data = r.json()
    funded = sum(tx['value'] for tx in data['chain_stats']['funded_txo_sum'])
    spent = sum(tx['value'] for tx in data['chain_stats']['spent_txo_sum'])
    return data['chain_stats']
