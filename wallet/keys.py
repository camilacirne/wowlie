from btclib.mnemonic.bip39 import mnemonic_from_entropy, seed_from_mnemonic
from btclib.bip32 import rootxprv_from_seed, derive
from btclib import b32
from btclib.to_pub_key import pub_keyinfo_from_key
from wallet.utils import save_wallet, load_wallet
import os

def init_wallet():
    entropy = os.urandom(16)  
    mnemonic = mnemonic_from_entropy(entropy)
    seed = seed_from_mnemonic(mnemonic, passphrase="")

    rootxprv = rootxprv_from_seed(seed)
    
    # Derivar para o primeiro endereço BIP84 testnet
    receive_path = "m/84'/1'/0'/0/0"
    child_xprv = derive(rootxprv, receive_path)
    

    pub_key = pub_keyinfo_from_key(child_xprv)[0]    
    addr = b32.p2wpkh(pub_key, network="testnet")

    data = {
        "mnemonic": mnemonic,
        "account_path": "m/84'/1'/0'",
        "addresses": {"0": {"path": receive_path, "address": addr}},
        "next_index": 1
    }
    save_wallet(data)
    return data


def next_address():
    w = load_wallet()
    seed = seed_from_mnemonic(w["mnemonic"], passphrase="")
    
    # Criar chave raiz
    rootxprv = rootxprv_from_seed(seed)

    index = w["next_index"]
    path = f"m/84'/1'/0'/0/{index}"
    
    # Derivar chave filha
    child_xprv = derive(rootxprv, path)
    
    # Obter chave pública e endereço
    pub_key = pub_keyinfo_from_key(child_xprv)[0]
 
    addr = b32.p2wpkh(pub_key, network="testnet")
    w["addresses"][str(index)] = {"path": path, "address": addr}
    w["next_index"] = index + 1
    save_wallet(w)
    return addr