# WowLie Wallet (Testnet)

Carteira Bitcoin feita em Python com `btclib`.

## Recursos
- BIP39: geração de seed (12 palavras)
- BIP32: derivação hierárquica de chaves
- BIP84: endereços SegWit `tb1...`
- Rede Testnet (sem valor real)
- CLI e interface Streamlit opcionais

## Instalação
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Segurança
```bash
wallet.json 
└── encrypted_mnemonic:
    ├── salt: random 256 bits
    ├── nonce: random 96 bits
    ├── ciphertext: AES-256-GCM(mnemonic)
    └── iterations: 100,000
```
Senha do Usuário
      ↓
PBKDF2 (100k iterações) ← Lento de propósito!
    ↓
Chave AES-256
    ↓
AES-GCM Encrypt
    ↓
Mnemonic Criptografada → wallet.json

## Usar pelo cli

```bash
python cli.py init
```

### Outros comandos
```bash
init              # Criar nova carteira
info              # Informações da carteira
receive           # Gerar novo endereço
balance           # Consultar saldo
create-tx         # Criar plano de transação
broadcast         # Enviar transação assinada
utxos             # Listar UTXOs
show-seed         # Ver seed (CUIDADO!)
check-password    # Verificar senha
```

## Interface

## Rodar o Streamlit
streamlit run streamlit_app.py

