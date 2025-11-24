# 💰 WowLie Wallet

**Carteira Bitcoin Testnet profissional** feita em Python com interface Streamlit e suporte para desktop (Electron).

![Bitcoin](https://img.shields.io/badge/Bitcoin-Testnet-orange?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## ✨ Recursos

- 🔐 **BIP39**: Geração de seed (12 palavras)
- 🔑 **BIP32**: Derivação hierárquica de chaves
- 📍 **BIP84**: Endereços SegWit `tb1...`
- 🌐 **Testnet**: Sem valor real (ambiente de testes)
- 💻 **Multi-interface**: CLI, Web (Streamlit) e Desktop (Electron)
- 🔒 **Segurança**: Criptografia AES-256-GCM
- 📦 **Instaladores**: `.exe` (Windows), `.dmg` (macOS), `.deb` (Linux)

## 🚀 Início Rápido

### Instalação Automática

**Windows:**
```powershell
SETUP.bat
```

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

### Instalação Manual

```bash
# Python
pip install -r requirements.txt

# Node.js (para desktop)
npm install
```

## 📱 Modos de Uso

### 1️⃣ Interface Web (Streamlit)
```bash
streamlit run streamlit_app.py
```
Abre no navegador padrão em `http://localhost:8501`

### 2️⃣ Desktop (Electron)
```bash
npm start
```
Abre em janela desktop nativa

### 3️⃣ Linha de Comando (CLI)
```bash
python cli.py init              # Criar nova carteira
python cli.py info              # Informações da carteira
python cli.py receive           # Gerar novo endereço
python cli.py balance           # Consultar saldo
python cli.py create-tx         # Criar plano de transação
python cli.py broadcast         # Enviar transação assinada
python cli.py utxos             # Listar UTXOs
python cli.py show-seed         # Ver seed (CUIDADO!)
python cli.py check-password    # Verificar senha
```

## 📦 Build para Produção

### Gerar Instaladores

**Windows (.exe + instalador):**
```bash
npm run build:win
```
📍 Saída: `dist-electron/WowLie Wallet Setup 1.0.0.exe`

**macOS (.dmg):**
```bash
npm run build:mac
```
📍 Saída: `dist-electron/WowLie Wallet-1.0.0.dmg`

**Linux (.deb + AppImage):**
```bash
npm run build:linux
```
📍 Saída: 
- `dist-electron/wowlie-wallet_1.0.0_amd64.deb`
- `dist-electron/WowLie Wallet-1.0.0.AppImage`

**Todas as plataformas:**
```bash
npm run build
```

📚 **Guia completo:** Veja `BUILD_GUIDE.md`

## 🔐 Segurança

### Arquitetura de Criptografia

```
Senha do Usuário
      ↓
PBKDF2 (100k iterações) ← Lento de propósito!
      ↓
Chave AES-256
      ↓
AES-GCM Encrypt
      ↓
Mnemonic Criptografada → ~/.wowlie/wallet.json
```

### Estrutura do wallet.json
```json
{
  "encrypted_mnemonic": {
    "salt": "256 bits aleatórios",
    "nonce": "96 bits aleatórios",
    "ciphertext": "AES-256-GCM(mnemonic)",
    "iterations": 100000
  }
}
```

### ⚠️ Avisos Importantes

- ✅ **Anote a seed**: Você verá as 12 palavras **uma única vez**
- ✅ **Guarde offline**: Papel, cofre, local seguro
- ✅ **Testnet apenas**: Esta versão é para testes (sem valor real)
- ❌ **Nunca compartilhe**: Nem seed, nem senha
- ❌ **Sem backup = perda total**: Sem seed, não há recuperação

## 📁 Estrutura do Projeto
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

