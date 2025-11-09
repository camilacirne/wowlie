import argparse
import getpass
import json
from rich import print
from rich.table import Table
from wallet.keys import init_wallet, next_address, get_mnemonic, verify_wallet_password
from wallet.utils import load_wallet, wallet_exists, load_addresses
from wallet.network import get_balance
from wallet.password import validate_password_strength
from wallet.transactions import get_utxos, broadcast_tx_hex, build_tx_plan

def _prompt_new_password() -> str:
    while True:
        pwd = getpass.getpass("Defina a senha da carteira: ")
        ok, errs = validate_password_strength(pwd)
        if not ok:
            print("[red]Senha fraca:[/red]")
            for e in errs:
                print(f"  - {e}")
            continue

        confirm = getpass.getpass("Confirme a senha: ")
        if pwd != confirm:
            print("[red]As senhas não coincidem. Tente novamente.[/red]")
            continue

        return pwd
    
def _prompt_wallet_password() -> str:
    return getpass.getpass("Digite a senha da carteira: ")

def cmd_init(_):
    print("[bold]Inicializando carteira (testnet)...[/bold]")
    password = _prompt_new_password()
    result = init_wallet(password)
    print("\n[green]Carteira criada![/green]")
    print("Seed (anote offline):")
    print(result["mnemonic"])
    print("\nEndereço inicial:", result["first_address"])
    print("[dim]Arquivo salvo em: ~/.wowlie/wallet.json[/dim]\n")

    del result, password

def cmd_info(_):
    w = load_wallet()
    t = Table(title="WowLie Wallet (Testnet)")
    t.add_column("Campo")
    t.add_column("Valor")
    t.add_row("Account path", w["account_path"])
    t.add_row("Próximo índice", str(w["next_index"]))
    last_idx = str(max(map(int, w["addresses"].keys())))
    t.add_row("Último endereço", w["addresses"][last_idx]["address"])
    print(t)

def cmd_receive(_):
    password = _prompt_wallet_password()
    try:
        addr = next_address(password)
        print("[bold green]Novo endereço de recebimento:[/bold green]")
        print(addr)
    except ValueError as e:
        print(f"[red]Erro:[/red] {e}")

def cmd_balance(_):
    w = load_wallet()
    last_idx = str(max(map(int, w["addresses"].keys())))
    addr = w["addresses"][last_idx]["address"]
    bal = get_balance(addr)
    print(f"Endereço: {addr}")
    print(f"Confirmado (sats):   {bal['confirmed']}")
    print(f"Não confirmado (sats): {bal['unconfirmed']}")
    print(f"Total (sats):        {bal['total']}")

def cmd_show_seed(_):
    password = _prompt_wallet_password()
    try:
        mnemonic = get_mnemonic(password)
        print("[yellow]SEED (backup):[/yellow]")
        print(mnemonic)
        del mnemonic
    except ValueError as e:
        print(f"[red]Erro:[/red] {e}")


def cmd_check_password(_):
    password = _prompt_wallet_password()
    ok = verify_wallet_password(password)
    print("[green]Senha correta.[/green]" if ok else "[red]Senha incorreta.[/red]")

def cmd_create_tx(args):
    """Cria plano de transação"""
    if not wallet_exists():
        print("Nenhuma carteira encontrada. Execute: wowlie init")
        return 1

    try:
        idxs, addrs, _ = load_addresses()

        if not addrs:
            print("Nenhum endereço encontrado.")
            return 1

        # Endereço de origem
        if args.from_addr:
            from_addr = args.from_addr
            if from_addr not in addrs:
                print(f"Endereço {from_addr} não pertence a esta carteira.")
                return 1
        else:
            from_addr = addrs[-1]  # último endereço derivado

        to_addr = args.to
        amount = args.amount
        fee_rate = args.fee_rate

        # Endereço de troco
        change_addr = args.change if args.change else from_addr

        print("\nCriando plano de transação...")
        print("=" * 70)
        print(f"De: {from_addr}")
        print(f"Para: {to_addr}")
        print(f"Quantia: {amount:,} sats")
        print(f"Taxa: {fee_rate} sats/vByte")
        print(f"Troco para: {change_addr}")
        print("=" * 70)

        # Criar plano
        plan = build_tx_plan(
            from_address=from_addr,
            to_address=to_addr,
            amount_sats=amount,
            fee_rate=fee_rate,
            change_address=change_addr,
        )

        print("\nPlano criado com sucesso!")
        print("=" * 70)
        print(f"Inputs: {len(plan['inputs'])}")
        print(f"Outputs: {len(plan['outputs'])}")
        print(f"Valor a enviar: {plan['amount_sats']:,} sats")
        print(f"Taxa estimada: {plan['estimated_fee_sats']:,} sats")
        print(f"Troco: {plan.get('change_sats', 0):,} sats")
        print(f"Tamanho estimado: {plan['estimated_vbytes']} vBytes")
        print("=" * 70)

        # Salvar plano
        output_file = args.output or "tx_plan.json"
        with open(output_file, "w") as f:
            json.dump(plan, f, indent=2)

        print(f"\nPlano salvo em: {output_file}")
        print("\nPróximos passos:")
        print("  1. Abra o Sparrow Wallet em modo testnet")
        print("  2. Importe sua seed (use: wowlie show-seed)")
        print("  3. Crie a transação com os valores acima")
        print("  4. Assine e copie o TX HEX")
        print("  5. Execute: wowlie broadcast --hex <TX_HEX>\n")

        return 0
    except RuntimeError as e:
        print(f"{e}")
        return 1
    except Exception as e:
        print(f"Erro ao criar plano: {e}")
        return 1


def cmd_broadcast(args):
    """Faz broadcast de transação assinada"""
    if args.hex:
        tx_hex = args.hex
    elif args.file:
        try:
            with open(args.file, "r") as f:
                tx_hex = f.read().strip()
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")
            return 1
    else:
        print("Use --hex <HEX> ou --file <arquivo>")
        return 1

    if not tx_hex:
        print("TX HEX vazio!")
        return 1

    print("\nEnviando transação para a rede testnet...")
    print("=" * 70)

    try:
        txid = broadcast_tx_hex(tx_hex)
        print("\nTransação enviada com sucesso!")
        print("=" * 70)
        print(f"TXID: {txid}")
        print("\nVer na Blockstream:")
        print(f"  https://blockstream.info/testnet/tx/{txid}\n")
        return 0
    except Exception as e:
        print(f"Erro ao enviar transação: {e}")
        return 1


def cmd_utxos(args):
    """Lista UTXOs de um endereço"""
    if not wallet_exists():
        print("Nenhuma carteira encontrada. Execute: wowlie init")
        return 1

    try:
        idxs, addrs, _ = load_addresses()

        if not addrs:
            print("Nenhum endereço encontrado.")
            return 1

        # Determinar endereço
        if args.address:
            addr = args.address
            if addr not in addrs:
                print(f"Endereço {addr} não pertence a esta carteira.")
                return 1
        else:
            addr = addrs[-1]

        print(f"\nUTXOs de: {addr}")
        print("=" * 70)

        utxos = get_utxos(addr)

        if not utxos:
            print("Nenhum UTXO encontrado (endereço sem fundos).")
        else:
            total = 0
            for i, utxo in enumerate(utxos, 1):
                value = utxo["value"]
                total += value
                confirmed = utxo.get("status", {}).get("confirmed", False)
                status = "Confirmado" if confirmed else "Não confirmado"
                print(f"\n[{i}] {status}")
                print(f"    TXID: {utxo['txid']}")
                print(f"    VOUT: {utxo['vout']}")
                print(f"    Valor: {value:,} sats")

            print("\n" + "=" * 70)
            print(f"Total: {total:,} sats em {len(utxos)} UTXO(s)")

        print()
        return 0
    except Exception as e:
        print(f"Erro ao listar UTXOs: {e}")
        return 1


def main():
    p = argparse.ArgumentParser(description="WowLie Bitcoin Wallet (testnet)")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("info").set_defaults(func=cmd_info)
    sub.add_parser("receive").set_defaults(func=cmd_receive)
    sub.add_parser("balance").set_defaults(func=cmd_balance)
    sub.add_parser("show-seed").set_defaults(func=cmd_show_seed)
    sub.add_parser("check-password").set_defaults(func=cmd_check_password)

    # --- transações ---
    p_create = sub.add_parser("create-tx", help="Criar plano de transação")
    p_create.add_argument("--to", required=True, help="Endereço de destino (testnet)")
    p_create.add_argument("--amount", type=int, required=True, help="Quantidade em satoshis")
    p_create.add_argument("--fee-rate", type=int, required=True, help="Taxa em sats/vByte")
    p_create.add_argument("--from-addr", help="Endereço de origem (da carteira)")
    p_create.add_argument("--change", help="Endereço de troco")
    p_create.add_argument("--output", help="Arquivo de saída do plano (padrão: tx_plan.json)")
    p_create.set_defaults(func=cmd_create_tx)

    p_brd = sub.add_parser("broadcast", help="Broadcast de transação assinada (HEX)")
    group_hex = p_brd.add_mutually_exclusive_group(required=True)
    group_hex.add_argument("--hex", help="Transação em HEX")
    group_hex.add_argument("--file", help="Arquivo contendo o HEX")
    p_brd.set_defaults(func=cmd_broadcast)

    p_utxos = sub.add_parser("utxos", help="Listar UTXOs de um endereço da carteira")
    p_utxos.add_argument("--address", help="Endereço específico (opcional)")
    p_utxos.set_defaults(func=cmd_utxos)

    args = p.parse_args()
    if hasattr(args, "func"):
        exit_code = args.func(args)
        if isinstance(exit_code, int):
            raise SystemExit(exit_code)
    else:
        p.print_help()


if __name__ == "__main__":
    main()

