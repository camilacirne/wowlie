from btclib.mnemonic.bip39 import mnemonic_from_entropy, seed_from_mnemonic
from btclib.bip32 import rootxprv_from_seed, derive
from btclib import b32
from btclib.to_pub_key import pub_keyinfo_from_key
from wallet.utils import save_wallet, load_wallet
from wallet.crypto import encrypt_mnemonic, decrypt_mnemonic
import os


def init_wallet(password: str) -> dict:

    if not isinstance(password, str) or not password:
        raise ValueError("Senha inválida.")
    
    entropy = os.urandom(16)  
    mnemonic = mnemonic_from_entropy(entropy)
    
    encrypted_mnemonic = encrypt_mnemonic(mnemonic, password)
        
    seed = seed_from_mnemonic(mnemonic, passphrase="")
    rootxprv = rootxprv_from_seed(seed)
    
    # Derivar primeiro endereço BIP84 (native segwit) para testnet
    receive_path = "m/84'/1'/0'/0/0"
    child_xprv = derive(rootxprv, receive_path)
    
    # Obter chave pública e gerar endereço
    pub_key = pub_keyinfo_from_key(child_xprv)[0]
    addr = b32.p2wpkh(pub_key, network="testnet")
    

    data = {
        "encrypted_mnemonic": encrypted_mnemonic,  
        "account_path": "m/84'/1'/0'",
        "network": "testnet",
        "addresses": {
            "0": {
                "path": receive_path,
                "address": addr
            }
        },
        "next_index": 1
    }
    
    save_wallet(data)
    
    del seed, rootxprv, child_xprv

    return {
        "wallet": data,
        "mnemonic": mnemonic,
        "first_address": addr,
    }


def next_address(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Senha inválida.")
    
    w = load_wallet()
    
    try:
        mnemonic = decrypt_mnemonic(w["encrypted_mnemonic"], password)
    except Exception:
        print("Senha incorreta!")
        return None
    
    seed = seed_from_mnemonic(mnemonic, passphrase="")
    rootxprv = rootxprv_from_seed(seed)
    
    index = w["next_index"]
    path = f"m/84'/1'/0'/0/{index}"
    
    # Derivar nova chave
    child_xprv = derive(rootxprv, path)
    
    # Obter chave pública e gerar endereço
    pub_key = pub_keyinfo_from_key(child_xprv)[0]
    addr = b32.p2wpkh(pub_key, network="testnet")
 
    w["addresses"][str(index)] = {"path": path, "address": addr}
    w["next_index"] = index + 1
    save_wallet(w)
    
    del seed, rootxprv, child_xprv, mnemonic
    
    return addr


def get_mnemonic(password: str = None) -> str:
    """
    Retorna a mnemonic descriptografada (USO PERIGOSO: backup/recuperação).
    """

    if not isinstance(password, str) or not password:
        raise ValueError("Senha inválida.")
    
    w = load_wallet()
    
    try:
        mnemonic = decrypt_mnemonic(w["encrypted_mnemonic"], password)
        return mnemonic
    except Exception as e:
        raise ValueError("Senha incorreta!") from e


def verify_wallet_password(password: str = None) -> bool:
    """
    Verifica se a senha abre a carteira. Sem prints, sem prompt.
    """

    try:
        get_mnemonic(password)
        return True
    except Exception:
        return False
