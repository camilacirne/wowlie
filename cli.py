import argparse
import getpass
from rich import print
from rich.table import Table
from wallet.keys import init_wallet, next_address, get_mnemonic, verify_wallet_password
from wallet.utils import load_wallet
from wallet.network import get_balance
from wallet.password import validate_password_strength

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


def main():
    p = argparse.ArgumentParser(description="WowLie Bitcoin Wallet (testnet)")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("info").set_defaults(func=cmd_info)
    sub.add_parser("receive").set_defaults(func=cmd_receive)
    sub.add_parser("balance").set_defaults(func=cmd_balance)
    sub.add_parser("show-seed").set_defaults(func=cmd_show_seed)
    sub.add_parser("check-password").set_defaults(func=cmd_check_password)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
