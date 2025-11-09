# wallet/transactions.py
import json
import math
from typing import List, Dict, Tuple
import requests

from wallet.utils import load_wallet
from wallet.network import get_utxos  # se não tiver, copie a função do seu network.py

API = "https://blockstream.info/testnet/api"


def estimate_vbytes(n_inputs: int, n_outputs: int) -> int:
    """
    Estimativa simples para P2WPKH:
      - input ~ 68 vbytes
      - output ~ 31 vbytes
      - overhead ~ 10 vbytes
    """
    return int(n_inputs * 68 + n_outputs * 31 + 10)

def sats_for_fee(n_inputs: int, n_outputs: int, fee_rate: int) -> int:
    vb = estimate_vbytes(n_inputs, n_outputs)
    return vb * fee_rate

# ---------- Seleção de UTXO (greedy) ----------

def select_utxos(utxos: List[dict], amount_sats: int, fee_rate: int) -> Tuple[List[dict], int, int]:
    """
    Seleciona UTXOs ordenando por valor (asc), até cobrir amount + fee estimada.
    Retorna (utxos_selecionados, total_sats, fee_estimada).
    """
    # apenas utxos confirmados (status.confirmed == True) de preferência
    usable = [u for u in utxos if u.get("status", {}).get("confirmed", False)]
    if not usable:
        # se não houver confirmados, tenta usar os não confirmados mesmo
        usable = utxos[:]
    usable.sort(key=lambda u: u["value"])  # do menor para o maior

    selected = []
    total = 0
    # assume 2 outputs (destino + troco) para estimativa
    target_outputs = 2

    for u in usable:
        selected.append(u)
        total += u["value"]
        fee_est = sats_for_fee(len(selected), target_outputs, fee_rate)
        if total >= amount_sats + fee_est:
            return selected, total, fee_est

    # não conseguiu cobrir
    fee_est = sats_for_fee(len(selected), target_outputs, fee_rate)
    return [], total, fee_est

# ---------- Construção do "plano" (inputs/outputs) ----------

def build_tx_plan(from_address: str, to_address: str, amount_sats: int, fee_rate: int = 5,
                  change_address: str = None) -> Dict:
    """
    Cria um "plano de transação" (sem assinar) com:
      - inputs selecionados
      - outputs (destino + troco se houver)
      - fee estimada, tamanho estimado
    Esse plano pode ser assinado em outra carteira (Sparrow, por ex.) usando a mesma seed.
    Depois, publique com broadcast_tx_hex(tx_hex_assinado).
    """
    # 1) Buscar UTXOs do endereço de origem
    utxos = get_utxos(from_address)
    if not utxos:
        raise RuntimeError("Nenhum UTXO encontrado nesse endereço.")

    # 2) Selecionar UTXOs suficientes
    selected, total_sel, fee_est = select_utxos(utxos, amount_sats, fee_rate)
    if not selected:
        raise RuntimeError(f"Saldo insuficiente: disponível ~{total_sel} sats; necessário ~{amount_sats + fee_est} sats (com taxa).")

    # 3) Calcular troco
    change = total_sel - amount_sats - fee_est
    outputs = {to_address: amount_sats}
    if change > 0:
        if not change_address:
            # por ora: usar o MESMO endereço de origem para o troco (funciona, mas o ideal é m/84'/1'/0'/1/i)
            change_address = from_address
        outputs[change_address] = change

    # 4) Montar inputs legíveis
    inputs = [{
        "txid": u["txid"],
        "vout": u["vout"],
        "value": u["value"]
    } for u in selected]

    # 5) Estimar vbytes finais (se tiver change, outputs=2; senão 1)
    n_out = len(outputs)
    vbytes = estimate_vbytes(len(inputs), n_out)
    fee_final = vbytes * fee_rate  # pode ajustar a partir de agora, se quiser

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
        "note": "Plano não assinado. Assine com sua seed (ex.: Sparrow em testnet) ou integre a assinatura local."
    }
    # salvar para referência/uso externo
    with open("tx_plan.json", "w") as f:
        json.dump(plan, f, indent=2)
    return plan

# ---------- Broadcast (hex já assinado) ----------

def broadcast_tx_hex(signed_tx_hex: str) -> str:
    """
    Publica um TX HEX ASSINADO na Blockstream testnet.
    Retorna o txid.
    """
    r = requests.post(f"{API}/tx", data=signed_tx_hex.strip(),
                      headers={"Content-Type": "text/plain"}, timeout=30)
    r.raise_for_status()
    return r.text.strip()
