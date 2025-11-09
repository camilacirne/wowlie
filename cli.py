import argparse
from rich import print
from rich.table import Table
from wallet.keys import init_wallet, next_address
from wallet.utils import load_wallet
from wallet.network import get_balance

def cmd_init(_):
    w = init_wallet()
    print("[green]Carteira criada![/green]")
    print("Seed (anote offline):")
    print(w["mnemonic"])
    print("\nEndereço inicial:", w["addresses"]["0"]["address"])

def cmd_info(_):
    w = load_wallet()
    t = Table(title="WowLie Wallet (Testnet)")
    t.add_column("Campo")
    t.add_column("Valor")
    t.add_row("Account path", w["account_path"])
    t.add_row("Próximo índice", str(w["next_index"]))
    print(t)

def cmd_receive(_):
    addr = next_address()
    print("[bold green]Novo endereço de recebimento:[/bold green]")
    print(addr)

def cmd_balance(_):
    w = load_wallet()
    # usa o último endereço gerado
    last_idx = str(max(map(int, w["addresses"].keys())))
    addr = w["addresses"][last_idx]["address"]
    bal = get_balance(addr)
    print(f"Endereço: {addr}")
    print(f"Confirmado (sats):   {bal['confirmed']}")
    print(f"Não confirmado (sats): {bal['unconfirmed']}")
    print(f"Total (sats):        {bal['total']}")

def main():
    p = argparse.ArgumentParser(description="WowLie Bitcoin Wallet (testnet)")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("info").set_defaults(func=cmd_info)
    sub.add_parser("receive").set_defaults(func=cmd_receive)
    sub.add_parser("balance").set_defaults(func=cmd_balance)
    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
