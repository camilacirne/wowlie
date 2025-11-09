from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import os
import base64


# Número de iterações PBKDF2 (100.000 é um bom balanço entre segurança e performance)
PBKDF2_ITERATIONS = 100_000


def encrypt_mnemonic(mnemonic: str, password: str) -> dict:
    """
    Criptografa a mnemonic usando AES-256-GCM com senha do usuário.
    
    Args:
        mnemonic: A seed phrase de 12 ou 24 palavras
        password: Senha do usuário para proteger a carteira
    
    Returns:
        Dict com salt, nonce e ciphertext (todos em base64)
    """
    # Gerar salt aleatório
    salt = os.urandom(32)  # 256 bits
    
    # Derivar chave da senha usando PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits para AES-256
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))
    
    # Gerar nonce aleatório para AES-GCM
    nonce = os.urandom(12)  # 96 bits (recomendado para GCM)
    
    # Criptografar usando AES-GCM (autenticação + criptografia)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, mnemonic.encode('utf-8'), None)
    
    # Retornar tudo em base64 para armazenamento JSON
    return {
        "salt": base64.b64encode(salt).decode('utf-8'),
        "nonce": base64.b64encode(nonce).decode('utf-8'),
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
        "iterations": PBKDF2_ITERATIONS
    }


def decrypt_mnemonic(encrypted_data: dict, password: str) -> str:
    """
    Descriptografa a mnemonic usando a senha do usuário.
    
    Args:
        encrypted_data: Dict com salt, nonce, ciphertext e iterations
        password: Senha do usuário
    
    Returns:
        A mnemonic descriptografada
    
    Raises:
        cryptography.exceptions.InvalidTag: Se a senha estiver incorreta
    """
    # Decodificar dados de base64
    salt = base64.b64decode(encrypted_data["salt"])
    nonce = base64.b64decode(encrypted_data["nonce"])
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    iterations = encrypted_data.get("iterations", PBKDF2_ITERATIONS)
    
    # Derivar chave da senha usando os mesmos parâmetros
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))
    
    # Descriptografar usando AES-GCM
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    
    return plaintext.decode('utf-8')


def verify_password(encrypted_data: dict, password: str) -> bool:
    """
    Verifica se a senha está correta sem descriptografar completamente.
    
    Args:
        encrypted_data: Dict com dados criptografados
        password: Senha para verificar
    
    Returns:
        True se a senha estiver correta, False caso contrário
    """
    try:
        decrypt_mnemonic(encrypted_data, password)
        return True
    except Exception:
        return False