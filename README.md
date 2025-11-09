# WowLie Wallet (Testnet)

Carteira Bitcoin **educacional** feita em Python com `btclib`.

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

streamlit run streamlit_app.py;