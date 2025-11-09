from typing import List, Dict, Tuple, Optional, Iterator
import struct
import json
import requests
import hashlib
import os
from wallet.network import get_utxos
from wallet.keys import get_mnemonic
from wallet.utils import load_wallet
from btclib.mnemonic.bip39 import seed_from_mnemonic
from btclib.bip32 import rootxprv_from_seed, derive
from btclib.to_pub_key import pub_keyinfo_from_key
from btclib.hashes import hash160
from btclib.ecc import dsa
from btclib import b32

API = "https://blockstream.info/testnet/api"


def secure_zeroize(buf: Optional[bytearray]) -> None:
    """
    Best-effort: sobrescreve o conteúdo de um bytearray com zeros.
    Não há garantia absoluta em CPython (cópias podem existir), mas é melhor que nada.
    """
    if buf is None:
        return
    try:
        mv = memoryview(buf)
        mv[:] = b"\x00" * len(buf)
        mv.release()
    except Exception:
        # fallback
        try:
            for i in range(len(buf)):
                buf[i] = 0
        except Exception:
            pass

class SensitiveBytes:
    """
    Context manager para segredos em memória mutável (bytearray).
    Garante zeroização no __exit__ (best-effort).
    Use assim:
        with SensitiveBytes(data_bytes) as secret:
            # use secret (bytearray)
    """
    def __init__(self, data: bytes | bytearray):
        # copia para bytearray local mutável (evitar referência ao original)
        self._buf = bytearray(data)

    def __enter__(self) -> bytearray:
        return self._buf

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        secure_zeroize(self._buf)
        # substituir por buffer vazio para minimizar referências
        self._buf = bytearray()

# ---------------------------
# Helpers de serialização
# ---------------------------

def varint_encode(n: int) -> bytes:
    if n < 0xfd:
        return bytes([n])
    elif n <= 0xffff:
        return b'\xfd' + struct.pack('<H', n)
    elif n <= 0xffffffff:
        return b'\xfe' + struct.pack('<I', n)
    else:
        return b'\xff' + struct.pack('<Q', n)

def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def serialize_script_pubkey(address: str) -> bytes:
    """
    Constrói scriptPubKey para endereço bech32 P2WPKH (v0).
    Suporta hrp 'tb' (testnet) e 'bcrt' (regtest) e 'bc' (mainnet).
    """
    try:
        hrp, witver, witprog = b32.b32decode(address)
    except Exception as e:
        raise ValueError(f"Endereço inválido ({address}): {e}")

    if witver != 0 or len(witprog) != 20:
        raise ValueError("Apenas P2WPKH (witness v0, 20 bytes) é suportado por esta função")

    return bytes([0x00, 0x14]) + witprog

# ---------------------------
# Seleção de UTXOs / fees
# ---------------------------

def estimate_vbytes(n_inputs: int, n_outputs: int) -> int:
    """
    Estimativa simples para P2WPKH:
      - input ~ 68 vbytes
      - output ~ 31 vbytes
      - overhead ~ 10 vbytes
    Use apenas como estimativa para cálculo inicial de fee.
    """
    return int(n_inputs * 68 + n_outputs * 31 + 10)

def sats_for_fee(n_inputs: int, n_outputs: int, fee_rate: int) -> int:
    vb = estimate_vbytes(n_inputs, n_outputs)
    return vb * fee_rate

DUST_P2WPKH = 546  # referência; usado para evitar criar troco dust

def select_utxos(utxos: List[dict], amount_sats: int, fee_rate: int) -> Tuple[List[dict], int, int]:
    """
    Seleciona UTXOs ordenando por valor ascendente até cobrir amount + fee estimada.
    Retorna (selected_utxos, total_sats, fee_estimated)
    """
    usable = [u for u in utxos if u.get("status", {}).get("confirmed", False)]
    if not usable:
        usable = utxos[:]
    usable.sort(key=lambda u: u["value"])

    selected = []
    total = 0
    target_outputs = 2  # inicialmente: to + change

    for u in usable:
        selected.append(u)
        total += u["value"]
        fee_est = sats_for_fee(len(selected), target_outputs, fee_rate)
        if total >= amount_sats + fee_est:
            return selected, total, fee_est

    fee_est = sats_for_fee(len(selected), target_outputs, fee_rate)
    return [], total, fee_est

# ---------------------------
# Wallet helpers (derivation)
# ---------------------------

def get_address_path(address: str) -> Optional[str]:
    """
    Busca o derivation path de um endereço na carteira (wallet.json).
    Retorna o path ex.: "m/84'/1'/0'/0/0" ou None.
    """
    try:
        w = load_wallet()
        # espera-se w["addresses"] como dict index-> {address, path, index}
        for idx, addr_data in w.get("addresses", {}).items():
            if addr_data.get("address") == address:
                return addr_data.get("path")
        return None
    except Exception:
        return None

def derive_private_key_ctx(address: str, password: str) -> Tuple[str, SensitiveBytes]:
    """
    Deriva a chave privada para um endereço específico e retorna um contexto
    SensitiveBytes contendo os 32 bytes da chave privada (best-effort).
    Use com 'with' ou garanta que __exit__ seja chamado via bloco try/finally.
    """
    path = get_address_path(address)
    if not path:
        raise ValueError(f"Endereço {address} não encontrado na carteira")

    # mnemonic é str (imutável) — minimizar vida dessa variável
    mnemonic = get_mnemonic(password)
    seed = seed_from_mnemonic(mnemonic, passphrase="")

    try:
        rootxprv = rootxprv_from_seed(seed)
        child_xprv = derive(rootxprv, path)
        raw = child_xprv.key  # formato esperado: 0x00 + 32 bytes priv
        if not (isinstance(raw, (bytes, bytearray)) and len(raw) == 33 and raw[0] == 0x00):
            raise ValueError("Formato inesperado de chave XPRV.key")
        # cria contexto sensível com os 32 bytes
        prv_ctx = SensitiveBytes(raw[1:])
        return path, prv_ctx
    finally:
        # reduzir vida de variáveis imutáveis o quanto possível
        try:
            del mnemonic
            # seed é bytes imutável; sobrescrever com bytearray rápido
            seed_ba = bytearray(seed)
            secure_zeroize(seed_ba)
            del seed_ba
            del seed
        except Exception:
            pass
        try:
            del rootxprv
            del child_xprv
        except Exception:
            pass

# ---------------------------
# Construção de transações
# ---------------------------

def build_unsigned_tx(inputs: List[dict], outputs: Dict[str, int]) -> bytes:
    """
    Constrói transação sem witness (usada para cálculo de TXID).
    """
    tx = b''
    tx += struct.pack('<I', 2)  # version
    tx += varint_encode(len(inputs))
    for inp in inputs:
        txid_bytes = bytes.fromhex(inp['txid'])[::-1]
        tx += txid_bytes
        tx += struct.pack('<I', inp['vout'])
        tx += b'\x00'  # scriptSig length = 0
        tx += b'\xff\xff\xff\xff'  # sequence
    tx += varint_encode(len(outputs))
    for addr, amount in outputs.items():
        tx += struct.pack('<Q', amount)
        script_pubkey = serialize_script_pubkey(addr)
        tx += varint_encode(len(script_pubkey))
        tx += script_pubkey
    tx += b'\x00\x00\x00\x00'  # locktime
    return tx

def build_witness_commitment(input_idx: int, inputs: List[dict], outputs: Dict[str, int],
                             amount: int, script_code: bytes) -> bytes:
    """
    Constrói a mensagem a ser hasheada segundo BIP143 para SegWit v0.
    """
    # nVersion
    commit = struct.pack('<I', 2)

    # hashPrevouts
    prevouts = b''
    for inp in inputs:
        prevouts += bytes.fromhex(inp['txid'])[::-1]
        prevouts += struct.pack('<I', inp['vout'])
    commit += hash256(prevouts)

    # hashSequence
    sequences = b''
    for _ in inputs:
        sequences += b'\xff\xff\xff\xff'
    commit += hash256(sequences)

    # outpoint (current input)
    cur = inputs[input_idx]
    commit += bytes.fromhex(cur['txid'])[::-1]
    commit += struct.pack('<I', cur['vout'])

    # scriptCode
    commit += varint_encode(len(script_code))
    commit += script_code

    # amount
    commit += struct.pack('<Q', amount)

    # nSequence
    commit += b'\xff\xff\xff\xff'

    # hashOutputs
    outputs_ser = b''
    for addr, amt in outputs.items():
        outputs_ser += struct.pack('<Q', amt)
        script_pubkey = serialize_script_pubkey(addr)
        outputs_ser += varint_encode(len(script_pubkey))
        outputs_ser += script_pubkey
    commit += hash256(outputs_ser)

    # nLocktime
    commit += b'\x00\x00\x00\x00'

    # sighash type (SIGHASH_ALL)
    commit += struct.pack('<I', 1)

    return commit

# ---------------------------
# Assinatura do input (SegWit)
# ---------------------------

def sign_input_segwit(input_idx: int, inputs: List[dict], outputs: Dict[str, int],
                      from_address: str, password: str) -> Tuple[bytes, bytes]:
    """
    Assina um input SegWit (P2WPKH) e retorna (sig_der_with_sighash, pubkey_compressed).
    Usa derive_private_key_ctx para manter chave privada mutável e zeroizá-la após uso.
    """
    # Derivar chave privada em contexto
    path, prv_ctx = derive_private_key_ctx(from_address, password)
    # Usaremos pubkey derivado separadamente (temos que derivar xprv novamente para pegar pubkey)
    # Minimizar tempo de vida da chave privada
    try:
        # Derivar public key via seed (não extraímos chave privada em bytes imutáveis)
        mnemonic = get_mnemonic(password)
        seed = seed_from_mnemonic(mnemonic, passphrase="")
        rootxprv = rootxprv_from_seed(seed)
        child_xprv = derive(rootxprv, path)
        pub_key = pub_keyinfo_from_key(child_xprv)[0]

        # Sanity check: pubkey comprimida (33 bytes)
        if not (len(pub_key) == 33 and pub_key[0] in (0x02, 0x03)):
            raise ValueError("Chave pública obtida não está em formato comprimido (33 bytes).")

        # scriptCode P2WPKH (P2PKH-style for BIP143)
        pubkey_hash = hash160(pub_key)
        script_code = bytes([0x76, 0xa9, 0x14]) + pubkey_hash + bytes([0x88, 0xac])

        amount = inputs[input_idx]['value']
        commit = build_witness_commitment(input_idx, inputs, outputs, amount, script_code)
        sighash = hash256(commit)

        # Assinar: btclib.dsa.sign espera (digest, priv_key) -> (r, s)
        # prv_ctx.buf é bytearray(32). btclib aceita bytes -> inevitável cópia aqui.
        # Usamos memoryview pra reduzir cópias desnecessárias; mas btclib pode copiar internamente.
        with prv_ctx as prv_buf:
            # convert to bytes for library call
            priv_bytes = bytes(prv_buf)  # cópia inevitável
            sig_rs = dsa.sign(sighash, priv_bytes)

        # serializar DER (r,s) - manter compatibilidade com sua implementação anterior
        r_bytes = sig_rs[0].to_bytes(32, 'big').lstrip(b'\x00')
        if len(r_bytes) == 0:
            r_bytes = b'\x00'
        if r_bytes[0] >= 0x80:
            r_bytes = b'\x00' + r_bytes

        s_bytes = sig_rs[1].to_bytes(32, 'big').lstrip(b'\x00')
        if len(s_bytes) == 0:
            s_bytes = b'\x00'
        if s_bytes[0] >= 0x80:
            s_bytes = b'\x00' + s_bytes

        sig_der = (
            b'\x30' +
            bytes([len(r_bytes) + len(s_bytes) + 4]) +
            b'\x02' + bytes([len(r_bytes)]) + r_bytes +
            b'\x02' + bytes([len(s_bytes)]) + s_bytes +
            b'\x01'  # SIGHASH_ALL appended
        )

        return sig_der, pub_key
    finally:
        # best-effort: zerar seed e outros objetos temporários
        try:
            del mnemonic
            seed_ba = bytearray(seed)
            secure_zeroize(seed_ba)
            del seed_ba
            del seed
        except Exception:
            pass
        try:
            del rootxprv
            del child_xprv
        except Exception:
            pass
        # prv_ctx.__exit__ já foi chamado pelo 'with' acima; se não, garantir zeroização adicional:
        try:
            secure_zeroize(prv_ctx._buf)
            prv_ctx._buf = bytearray()
        except Exception:
            pass

# ---------------------------
# Montagem final da transação assinada (SegWit)
# ---------------------------

def build_signed_segwit_tx(inputs: List[dict], outputs: Dict[str, int],
                           from_address: str, password: str) -> str:
    """
    Constrói transação SegWit com witness assinado para cada input.
    Retorna hex da transação.
    OBS: atualmente assume que todos os inputs pertencem ao mesmo from_address.
    """
    raw = b''
    raw += struct.pack('<I', 2)  # version
    raw += b'\x00\x01'  # marker + flag (segwit)
    raw += varint_encode(len(inputs))

    # inputs (scriptSig vazio)
    for inp in inputs:
        raw += bytes.fromhex(inp['txid'])[::-1]
        raw += struct.pack('<I', inp['vout'])
        raw += b'\x00'  # scriptSig len
        # sequence: usar padrão; se quiser RBF, mude para 0xfffffffd
        raw += b'\xff\xff\xff\xff'

    # outputs
    raw += varint_encode(len(outputs))
    for addr, amt in outputs.items():
        raw += struct.pack('<Q', amt)
        script_pubkey = serialize_script_pubkey(addr)
        raw += varint_encode(len(script_pubkey))
        raw += script_pubkey

    # witness para cada input
    for i in range(len(inputs)):
        sig_der, pub_key = sign_input_segwit(i, inputs, outputs, from_address, password)
        # stack: [signature, pubkey]
        raw += b'\x02'
        raw += varint_encode(len(sig_der))
        raw += sig_der
        raw += varint_encode(len(pub_key))
        raw += pub_key

    # locktime
    raw += b'\x00\x00\x00\x00'
    return raw.hex()


def build_and_sign_tx(from_address: str, to_address: str, amount_sats: int,
                      password: str, fee_rate: int = 5, change_address: Optional[str] = None) -> Dict:
    """
    Constrói e assina transação pronta para broadcast (mas não broadcasta).
    Retorna dict com signed_tx_hex, txid (calculado sem witness), vbytes, fee estimado e metadados.
    """
    utxos = get_utxos(from_address)
    if not utxos:
        raise RuntimeError("Nenhum UTXO encontrado para este endereço.")

    selected, total_sel, fee_est = select_utxos(utxos, amount_sats, fee_rate)
    if not selected:
        raise RuntimeError(f"Saldo insuficiente: disponível {total_sel} sats; necessário ~{amount_sats + fee_est} sats.")

    # calcular change
    change = total_sel - amount_sats - fee_est
    outputs = {to_address: amount_sats}

    if change > 0:
        if change < DUST_P2WPKH:
            # não criar troco dust; somar ao fee
            fee_est += change
            change = 0
        else:
            if not change_address:
                change_address = from_address
            outputs[change_address] = change

    # preparar inputs
    inputs = [{"txid": u["txid"], "vout": u["vout"], "value": u["value"]} for u in selected]

    # assinar
    signed_hex = build_signed_segwit_tx(inputs, outputs, from_address, password)

    # recalcular vbytes aproximado e fee final
    vbytes = estimate_vbytes(len(inputs), len(outputs))
    fee_final = vbytes * fee_rate

    # calcular txid (sha256d da tx sem witness)
    txid = hash256(build_unsigned_tx(inputs, outputs))[::-1].hex()

    return {
        "signed_tx_hex": signed_hex,
        "txid": txid,
        "from_address": from_address,
        "to_address": to_address,
        "amount_sats": amount_sats,
        "fee_sats": fee_final,
        "change_sats": change,
        "change_address": change_address if change > 0 else None,
        "inputs": len(inputs),
        "outputs": len(outputs),
        "vbytes": vbytes,
        "total_input": total_sel,
        "network": "testnet"
    }

def build_tx_plan(from_address: str, to_address: str, amount_sats: int, fee_rate: int = 5,
                  change_address: Optional[str] = None) -> Dict:
    """
    Cria um plano de transação (não assinado) e salva em tx_plan.json.
    """
    utxos = get_utxos(from_address)
    if not utxos:
        raise RuntimeError("Nenhum UTXO encontrado para este endereço.")

    selected, total_sel, fee_est = select_utxos(utxos, amount_sats, fee_rate)
    if not selected:
        raise RuntimeError(f"Saldo insuficiente: disponível {total_sel} sats; necessário ~{amount_sats + fee_est} sats.")

    change = total_sel - amount_sats - fee_est
    outputs = {to_address: amount_sats}
    if change > 0:
        if change < DUST_P2WPKH:
            fee_est += change
            change = 0
        else:
            if not change_address:
                change_address = from_address
            outputs[change_address] = change

    inputs = [{"txid": u["txid"], "vout": u["vout"], "value": u["value"]} for u in selected]
    n_out = len(outputs)
    vbytes = estimate_vbytes(len(inputs), n_out)
    fee_final = vbytes * fee_rate

    plan = {
        "from_address": from_address,
        "to_address": to_address,
        "amount_sats": amount_sats,
        "fee_rate_sats_vb": fee_rate,
        "inputs": inputs,
        "outputs": outputs,
        "estimated_vbytes": vbytes,
        "estimated_fee_sats": fee_final,
        "change_sats": outputs.get(change_address, 0) if change > 0 else 0,
        "change_address": change_address if change > 0 else None,
        "network": "testnet",
        "note": "Plano não assinado. Use build_and_sign_tx() para assinar localmente."
    }

    with open("tx_plan.json", "w") as f:
        json.dump(plan, f, indent=2)

    return plan

def broadcast_tx_hex(signed_tx_hex: str) -> str:
    """
    Publica um TX HEX ASSINADO na Blockstream testnet.
    Retorna o txid (hex).
    """
    r = requests.post(f"{API}/tx", data=signed_tx_hex.strip(), headers={"Content-Type": "text/plain"}, timeout=30)
    r.raise_for_status()
    return r.text.strip()

def send_transaction(from_address: str, to_address: str, amount_sats: int,
                     password: str, fee_rate: int = 5, change_address: Optional[str] = None,
                     broadcast: bool = True) -> Dict:
    """
    Constrói, assina e (opcionalmente) envia a transação para a rede.
    Retorna dicionário com dados da transação (inclui txid_broadcast se enviado).
    """
    tx_data = build_and_sign_tx(from_address, to_address, amount_sats, password, fee_rate, change_address)

    if broadcast:
        txid = broadcast_tx_hex(tx_data["signed_tx_hex"])
        tx_data["txid_broadcast"] = txid
        tx_data["broadcast"] = True
    else:
        tx_data["broadcast"] = False

    return tx_data
