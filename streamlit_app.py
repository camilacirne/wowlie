import streamlit as st
from wallet.keys import init_wallet, next_address
from wallet.utils import load_wallet
import qrcode, io

st.title("💰 WowLie Wallet (Testnet)")
if "wallet" not in st.session_state:
    st.session_state.wallet = None

if st.button("🪙 Criar nova carteira"):
    w = init_wallet()
    st.session_state.wallet = w
    st.success("Carteira criada!")
    st.code(w["mnemonic"])
    st.write("Endereço inicial:", w["addresses"]["0"]["address"])

if st.session_state.wallet:
    if st.button("➕ Novo endereço"):
        addr = next_address()
        st.info(f"Endereço novo: {addr}")
        img = qrcode.make(addr)
        buf = io.BytesIO(); img.save(buf, format="PNG")
        st.image(buf.getvalue())
