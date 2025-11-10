"""
Módulo para gerenciar carteira Ethereum e interagir com testnets
"""
from eth_account import Account
from web3 import Web3
import json
import os


# RPCs do Polygon Amoy Testnet (substitui Mumbai que foi descontinuado em 04/2024)
AMOY_RPCS = [
    "https://rpc-amoy.polygon.technology",
    "https://polygon-amoy.g.alchemy.com/v2/demo",
    "https://polygon-amoy-bor-rpc.publicnode.com",
]

class EthWallet:
    def __init__(self, private_key=None, network="amoy"):
        """
        Inicializa carteira Ethereum
        
        Args:
            private_key: Chave privada (opcional, gera nova se None)
            network: "sepolia" ou "amoy" (padrão: amoy - Polygon Testnet)
        """
        self.network = network
        
        # Seleciona RPCs baseado na rede
        rpcs = AMOY_RPCS if network == "amoy" else SEPOLIA_RPCS
        
        # Tenta conectar a múltiplos RPCs
        self.w3 = None
        for rpc in rpcs:
            try:
                w3_test = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
                if w3_test.is_connected():
                    self.w3 = w3_test
                    break
            except:
                continue
        
        # Se nenhum funcionou, usa o primeiro mesmo assim
        if not self.w3:
            self.w3 = Web3(Web3.HTTPProvider(rpcs[0]))
        
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()
    
    @property
    def address(self):
        """Retorna endereço da carteira"""
        return self.account.address
    
    @property
    def private_key(self):
        """Retorna chave privada (hex)"""
        return self.account.key.hex()
    
    def get_balance(self):
        """Retorna saldo em ETH"""
        balance_wei = self.w3.eth.get_balance(self.address)
        balance_eth = self.w3.from_wei(balance_wei, 'ether')
        return float(balance_eth)
    
    def get_balance_wei(self):
        """Retorna saldo em Wei"""
        return self.w3.eth.get_balance(self.address)
    
    def get_token_balance(self, token_address):
        """Retorna saldo de um token ERC-20"""
        # ABI mínimo para função balanceOf
        min_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]
        
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=min_abi
        )
        
        balance = contract.functions.balanceOf(self.address).call()
        decimals = contract.functions.decimals().call()
        symbol = contract.functions.symbol().call()
        
        # Tenta pegar o nome, mas alguns tokens podem não ter
        try:
            name = contract.functions.name().call()
        except:
            name = symbol  # Usa o símbolo como fallback
        
        balance_formatted = balance / (10 ** decimals)
        
        return {
            "balance": balance_formatted,
            "balance_raw": balance,
            "decimals": decimals,
            "symbol": symbol,
            "name": name
        }
    
    def send_transaction(self, to_address, amount_eth):
        """Envia ETH para outro endereço"""
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': self.w3.to_wei(amount_eth, 'ether'),
            'gas': 21000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': self.w3.eth.chain_id
        }
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        return tx_hash.hex()
    
    def deploy_contract(self, bytecode, abi, *constructor_args):
        """Deploy de um contrato inteligente"""
        Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        # Estima gas
        gas_estimate = Contract.constructor(*constructor_args).estimate_gas({
            'from': self.address
        })
        
        # Constrói transação
        tx = Contract.constructor(*constructor_args).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': gas_estimate,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Assina e envia
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Espera receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'contract_address': tx_receipt.contractAddress
        }
    
    def transfer_token(self, token_address, to_address, amount):
        """
        Transfere tokens ERC-20 para outro endereço
        
        Args:
            token_address: Endereço do contrato do token
            to_address: Endereço de destino
            amount: Quantidade de tokens (com decimais)
        
        Returns:
            dict com tx_hash e status
        """
        # ABI mínimo para transfer
        transfer_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        # Cria contrato
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=transfer_abi
        )
        
        # Pega decimais
        decimals = contract.functions.decimals().call()
        
        # Converte amount para unidade base (wei)
        amount_wei = int(amount * (10 ** decimals))
        
        # Prepara transação
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        # Build transaction
        tx = contract.functions.transfer(
            Web3.to_checksum_address(to_address),
            amount_wei
        ).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 100000,  # Gas padrão para transfer ERC-20
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Assina e envia
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Espera confirmação
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'status': tx_receipt.status,  # 1 = sucesso, 0 = falha
            'gas_used': tx_receipt.gasUsed
        }
    
    def is_connected(self):
        """Verifica se está conectado à rede"""
        return self.w3.is_connected()


def create_eth_wallet():
    """Cria nova carteira Ethereum"""
    wallet = EthWallet()
    return {
        'address': wallet.address,
        'private_key': wallet.private_key
    }


def load_eth_wallet(private_key):
    """Carrega carteira existente"""
    return EthWallet(private_key)
