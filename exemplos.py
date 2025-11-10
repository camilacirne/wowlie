"""
Exemplo de uso das funcionalidades da WowLie Wallet via Python
"""

from wallet.eth_wallet import EthWallet, create_eth_wallet
from wallet.memecoin import get_memecoin_contract
from wallet.keys import init_wallet, import_wallet
from wallet.network import get_balance
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def exemplo_bitcoin():
    """Exemplo de uso com Bitcoin"""
    console.print("\n[bold cyan]═══ Bitcoin Testnet ═══[/bold cyan]\n")
    
    # Escolher entre criar ou importar
    console.print("[bold]Escolha uma opção:[/bold]")
    console.print("1. Criar nova carteira")
    console.print("2. Importar carteira existente")
    
    escolha = input("\n> ").strip()
    
    if escolha == "1":
        # Criar carteira
        console.print("\n📝 Criando carteira Bitcoin...")
        wallet = init_wallet()
        
        console.print(Panel(
            f"[green]Mnemonic:[/green] {wallet['mnemonic']}\n"
            f"[green]Endereço:[/green] {wallet['addresses']['0']['address']}",
            title="✅ Carteira Criada",
            border_style="green"
        ))
        
    elif escolha == "2":
        # Importar carteira
        console.print("\n📥 Importar carteira existente")
        mnemonic = input("Digite sua seed phrase (12 ou 24 palavras): ").strip()
        passphrase = input("Senha adicional (Enter para pular): ").strip()
        
        try:
            console.print("\n📝 Importando carteira...")
            wallet = import_wallet(mnemonic, passphrase)
            
            console.print(Panel(
                f"[green]Endereço:[/green] {wallet['addresses']['0']['address']}",
                title="✅ Carteira Importada",
                border_style="green"
            ))
        except Exception as e:
            console.print(f"[red]❌ Erro ao importar: {e}[/red]")
            return
    else:
        console.print("[red]❌ Opção inválida[/red]")
        return
    
    # Consultar saldo
    address = wallet['addresses']['0']['address']
    console.print(f"\n🔍 Consultando saldo de: {address}")
    
    try:
        balance = get_balance(address)
        
        table = Table(title="💰 Saldo Bitcoin")
        table.add_column("Tipo", style="cyan")
        table.add_column("Satoshis", style="magenta")
        table.add_column("BTC", style="green")
        
        table.add_row(
            "Confirmado",
            str(balance['confirmed']),
            f"{balance['confirmed'] / 100000000:.8f}"
        )
        table.add_row(
            "Não confirmado",
            str(balance['unconfirmed']),
            f"{balance['unconfirmed'] / 100000000:.8f}"
        )
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{balance['total']}[/bold]",
            f"[bold]{balance['total'] / 100000000:.8f}[/bold]"
        )
        
        console.print(table)
        
        if balance['total'] == 0:
            console.print("\n[yellow]💡 Dica: Use uma faucet para receber Bitcoin testnet[/yellow]")
            console.print("[blue]🔗 Faucets recomendadas (2025):[/blue]")
            console.print("[blue]  🥇 https://coinfaucet.eu/en/btc-testnet/[/blue]")
            console.print("[blue]  🥈 https://bitcoinfaucet.uo1.net/[/blue]")
            console.print("[blue]  🥉 https://testnet-faucet.mempool.co/[/blue]")
            console.print("\n[dim]Veja FAUCETS_BITCOIN.md para mais opções[/dim]")
            
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


def exemplo_ethereum():
    """Exemplo de uso com Ethereum"""
    console.print("\n[bold cyan]═══ Ethereum Sepolia ═══[/bold cyan]\n")
    
    # Criar carteira
    console.print("📝 Criando carteira Ethereum...")
    wallet_data = create_eth_wallet()
    wallet = EthWallet(wallet_data['private_key'])
    
    console.print(Panel(
        f"[green]Endereço:[/green] {wallet_data['address']}\n"
        f"[yellow]Chave Privada:[/yellow] {wallet_data['private_key'][:20]}...",
        title="✅ Carteira Criada",
        border_style="green"
    ))
    
    # Status de conexão
    if wallet.is_connected():
        console.print("[green]🟢 Conectado à Sepolia Testnet[/green]")
    else:
        console.print("[red]🔴 Não conectado[/red]")
        return
    
    # Consultar saldo
    console.print(f"\n🔍 Consultando saldo...")
    try:
        balance = wallet.get_balance()
        
        console.print(f"\n💎 Saldo: [bold green]{balance:.6f} ETH[/bold green]")
        
        if balance == 0:
            console.print("\n[yellow]💡 Dica: Use uma faucet para receber Sepolia ETH[/yellow]")
            console.print("[blue]🔗 https://sepoliafaucet.com/[/blue]")
            console.print("[blue]🔗 https://www.alchemy.com/faucets/ethereum-sepolia[/blue]")
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


def exemplo_consultar_token():
    """Exemplo de consulta de token ERC-20"""
    console.print("\n[bold cyan]═══ Consultar Token ERC-20 ═══[/bold cyan]\n")
    
    # Aqui você precisa ter uma chave privada existente
    private_key = input("Digite sua chave privada (ou Enter para pular): ").strip()
    
    if not private_key:
        console.print("[yellow]⏭️ Pulando exemplo de token...[/yellow]")
        return
    
    token_address = input("Digite o endereço do token: ").strip()
    
    if not token_address:
        console.print("[yellow]⏭️ Pulando...[/yellow]")
        return
    
    try:
        wallet = EthWallet(private_key)
        console.print(f"📍 Carteira: {wallet.address}")
        
        console.print("\n🔍 Consultando token...")
        token_info = wallet.get_token_balance(token_address)
        
        console.print(Panel(
            f"[green]Token:[/green] {token_info['symbol']}\n"
            f"[green]Saldo:[/green] {token_info['balance']:,.2f}\n"
            f"[green]Decimais:[/green] {token_info['decimals']}",
            title="🪙 Informações do Token",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


def exemplo_memecoin():
    """Exemplo de deploy de memecoin"""
    console.print("\n[bold cyan]═══ Deploy de Memecoin ═══[/bold cyan]\n")
    
    console.print("[yellow]⚠️ Você precisa ter ETH na Sepolia para fazer deploy![/yellow]\n")
    
    # Perguntar se quer continuar
    continuar = input("Deseja fazer deploy de uma memecoin? (s/n): ").strip().lower()
    
    if continuar != 's':
        console.print("[yellow]⏭️ Pulando deploy de memecoin...[/yellow]")
        return
    
    private_key = input("Digite sua chave privada: ").strip()
    
    if not private_key:
        console.print("[red]❌ Chave privada necessária[/red]")
        return
    
    try:
        wallet = EthWallet(private_key)
        balance = wallet.get_balance()
        
        console.print(f"\n📍 Carteira: {wallet.address}")
        console.print(f"💰 Saldo: {balance:.6f} ETH")
        
        if balance < 0.001:
            console.print("\n[red]❌ Saldo insuficiente! Você precisa de pelo menos 0.001 ETH[/red]")
            return
        
        # Configurar token
        console.print("\n[bold]Configure sua memecoin:[/bold]")
        name = input("Nome do token (ex: Big Cute): ").strip() or "Big Cute"
        symbol = input("Símbolo (ex: BCUTE): ").strip() or "BCUTE"
        supply = input("Supply inicial (ex: 1000000): ").strip() or "1000000"
        
        try:
            supply = int(supply)
        except:
            console.print("[red]❌ Supply inválido[/red]")
            return
        
        # Confirmar
        console.print(f"\n[bold]Resumo:[/bold]")
        console.print(f"  Nome: {name}")
        console.print(f"  Símbolo: {symbol}")
        console.print(f"  Supply: {supply:,} tokens")
        
        confirmar = input("\n✅ Confirmar deploy? (s/n): ").strip().lower()
        
        if confirmar != 's':
            console.print("[yellow]⏭️ Deploy cancelado[/yellow]")
            return
        
        # Deploy
        console.print("\n[bold cyan]🚀 Fazendo deploy...[/bold cyan]")
        console.print("[dim]Isso pode levar até 30 segundos...[/dim]")
        
        contract_info = get_memecoin_contract()
        supply_with_decimals = supply * (10 ** 18)
        
        result = wallet.deploy_contract(
            contract_info['bytecode'],
            contract_info['abi'],
            name,
            symbol,
            supply_with_decimals
        )
        
        console.print("\n[bold green]🎉 Memecoin criada com sucesso![/bold green]")
        
        console.print(Panel(
            f"[green]Nome:[/green] {name}\n"
            f"[green]Símbolo:[/green] {symbol}\n"
            f"[green]Supply:[/green] {supply:,} tokens\n"
            f"[green]Contrato:[/green] {result['contract_address']}\n"
            f"[green]TX Hash:[/green] {result['tx_hash']}",
            title="✨ Sua Memecoin",
            border_style="green"
        ))
        
        console.print(f"\n[blue]🔗 Ver no Etherscan:[/blue]")
        console.print(f"https://sepolia.etherscan.io/address/{result['contract_address']}")
        
        console.print(f"\n[blue]📜 Transação:[/blue]")
        console.print(f"https://sepolia.etherscan.io/tx/{result['tx_hash']}")
        
        # Verificar saldo
        console.print("\n[cyan]Verificando seu saldo...[/cyan]")
        token_info = wallet.get_token_balance(result['contract_address'])
        console.print(f"💰 Você tem: [bold green]{token_info['balance']:,.2f} {token_info['symbol']}[/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Erro: {e}[/red]")


def menu():
    """Menu principal"""
    console.print("\n[bold magenta]═══════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]    💰 WowLie Wallet - Exemplos    [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════[/bold magenta]\n")
    
    while True:
        console.print("[bold]Escolha uma opção:[/bold]")
        console.print("1. 🪙 Exemplo Bitcoin Testnet")
        console.print("2. ⟠ Exemplo Ethereum Sepolia")
        console.print("3. 🪙 Consultar Token ERC-20")
        console.print("4. 🚀 Deploy de Memecoin")
        console.print("5. ❌ Sair")
        
        escolha = input("\n> ").strip()
        
        if escolha == "1":
            exemplo_bitcoin()
        elif escolha == "2":
            exemplo_ethereum()
        elif escolha == "3":
            exemplo_consultar_token()
        elif escolha == "4":
            exemplo_memecoin()
        elif escolha == "5":
            console.print("\n[bold cyan]👋 Até logo![/bold cyan]\n")
            break
        else:
            console.print("[red]❌ Opção inválida[/red]")
        
        console.print("\n" + "─" * 50 + "\n")


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️ Interrompido pelo usuário[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Erro fatal: {e}[/red]")
