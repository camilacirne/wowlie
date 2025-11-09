import io, os
import qrcode
import streamlit as st

from wallet.keys import init_wallet, next_address, verify_wallet_password
from wallet.utils import wallet_exists, load_addresses
from wallet.password import validate_password_strength
from wallet.network import get_balance


st.set_page_config(page_title="WowLie Wallet | BigCute", page_icon="💰", layout="centered")

def _qr_png_bytes(data: str) -> bytes:
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def _wallet_file_path() -> str:
    return os.path.expanduser("~/.wowlie/wallet.json")

def _redact(addr: str) -> str:
    if len(addr) <= 20:
        return addr
    return f"{addr[:10]}…{addr[-8:]}"

if "wallet_created" not in st.session_state:
    st.session_state.wallet_created = wallet_exists()

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if "just_created_seed" not in st.session_state:
    st.session_state.just_created_seed = None

if "first_address" not in st.session_state:
    st.session_state.first_address = None

if "last_new_address" not in st.session_state:
    st.session_state.last_new_address = None

if "show_qr_current" not in st.session_state:
    st.session_state.show_qr_current = False

if "show_qr_new" not in st.session_state:
    st.session_state.show_qr_new = False

if "show_qr_initial" not in st.session_state:
    st.session_state.show_qr_initial = False

if "balance_placeholder" not in st.session_state:
    st.session_state.balance_placeholder = st.empty() 

if "prev_addr_selected" not in st.session_state:
    st.session_state.prev_addr_selected = None

if "prev_aggregate" not in st.session_state:
    st.session_state.prev_aggregate = False


st.title("💰 WowLie Wallet")

st.header("🪙 Criar carteira ")

if st.session_state.wallet_created:
    st.info("Uma carteira já existe neste dispositivo. Para criar outra, apague o arquivo atual (~/.wowlie/wallet.json) manualmente.")
else:
    st.markdown(
        "> **Atenção:** a seed (12 palavras) será exibida **uma única vez** após a criação. "
        "Anote **offline** e guarde com segurança. Sem a seed **ou** sem a senha, você perde tudo."
    )

    with st.form("create_wallet_form", clear_on_submit=True):
        pwd = st.text_input("Defina a senha da carteira", type="password")
        pwd2 = st.text_input("Confirme a senha", type="password")
        submitted_create = st.form_submit_button("Criar carteira")

    if submitted_create:
        ok, errs = validate_password_strength(pwd)
        if not ok:
            st.error("Senha fraca:")
            for e in errs:
                st.write(f"- {e}")
        elif pwd != pwd2:
            st.error("As senhas não coincidem.")
        else:
            try:
                result = init_wallet(pwd)  # não imprime; retorna dados
                st.session_state.wallet_created = True
                st.session_state.unlocked = True           # desbloqueia UI (sem guardar senha)
                st.session_state.just_created_seed = result["mnemonic"]  # mostrar uma vez
                st.session_state.first_address = result["first_address"]

                st.success("Carteira criada e salva em ~/.wowlie/wallet.json")

                with st.expander("📜 Seed (exibida apenas agora)", expanded=True):
                    st.warning("ANOTE OFFLINE e mantenha em local seguro. NÃO compartilhe.")
                    st.code(st.session_state.just_created_seed)
                    if st.button("✅ Já anotei / ocultar seed"):
                        st.session_state.just_created_seed = None

                st.write("**Endereço inicial:**")
                st.code(st.session_state.first_address)


                st.session_state.show_qr_initial = st.checkbox(
                    "Mostrar QR do endereço inicial",
                    value=st.session_state.show_qr_initial,
                    key="show_qr_initial_checkbox"
                )
                if st.session_state.show_qr_initial:
                    st.image(_qr_png_bytes(st.session_state.first_address), caption="QR do endereço inicial")

            except Exception as e:
                st.error(f"Erro ao criar carteira: {e}")

st.header("🔐 Entrar na carteira")

if not st.session_state.unlocked:
    if not st.session_state.wallet_created:
        st.info("Nenhuma carteira encontrada ainda. Crie uma abaixo em “🪙 Criar carteira”.")
    with st.form("login_form", clear_on_submit=True):
        pwd_try = st.text_input("Senha da carteira", type="password")
        submitted_login = st.form_submit_button("Entrar")
    if submitted_login:
        if not wallet_exists():
            st.error("Não há carteira salva. Crie uma primeiro.")
        else:
            try:
                if verify_wallet_password(pwd_try):
                    st.session_state.unlocked = True
                    st.success("Carteira desbloqueada — sessão ativa (senha NÃO armazenada).")
                else:
                    st.error("Senha incorreta.")
            except Exception as e:
                st.error(f"Erro ao verificar senha: {e}")
else:
    col1, col2 = st.columns([3, 1])
    col1.success("Sessão ativa: carteira desbloqueada.")
    if col2.button("Sair"):
        st.session_state.unlocked = False
        st.session_state.show_qr_current = False if "show_qr_current" in st.session_state else False
    st.session_state.show_qr_new = False if "show_qr_new" in st.session_state else False
    if "balance_placeholder" in st.session_state and st.session_state.balance_placeholder:
        st.session_state.balance_placeholder.empty()
    st.info("Sessão encerrada.")


if not st.session_state.wallet_created:
    st.header("🪙 Criar carteira (testnet)")
    st.markdown(
        "> **Atenção:** a seed (12 palavras) será exibida **uma única vez** logo após a criação. "
        "Anote **offline** e guarde com segurança. Sem a seed **ou** sem a senha, você perde tudo."
    )

    with st.form("create_wallet_form", clear_on_submit=True):
        pwd = st.text_input("Defina a senha da carteira", type="password")
        pwd2 = st.text_input("Confirme a senha", type="password")
        submitted_create = st.form_submit_button("Criar carteira")

    if submitted_create:
        ok, errs = validate_password_strength(pwd)
        if not ok:
            st.error("Senha fraca:")
            for e in errs:
                st.write(f"- {e}")
        elif pwd != pwd2:
            st.error("As senhas não coincidem.")
        else:
            try:
                result = init_wallet(pwd)  
                st.session_state.wallet_created = True
                st.session_state.unlocked = True 
                st.session_state.just_created_seed = result["mnemonic"]  
                st.session_state.first_address = result["first_address"]
                st.success("Carteira criada e salva em ~/.wowlie/wallet.json")

                with st.expander("📜 Seed (exibida apenas agora)", expanded=True):
                    st.warning("ANOTE OFFLINE e mantenha em local seguro. NÃO compartilhe.")
                    st.code(st.session_state.just_created_seed)
                    if st.button("✅ Já anotei / ocultar seed"):
                        st.session_state.just_created_seed = None

                st.info("Endereço inicial gerado.")
                st.write("**Endereço inicial:**")
                st.code(st.session_state.first_address)
                st.session_state.show_qr_initial = st.checkbox(
                "Mostrar QR do endereço inicial",
                value=st.session_state.show_qr_initial,
                key="show_qr_initial_checkbox"
                )
                if st.session_state.show_qr_initial:
                    st.image(_qr_png_bytes(st.session_state.first_address), caption="QR do endereço inicial")
            except Exception as e:
                st.error(f"Erro ao criar carteira: {e}")

st.header("📄 Informações da carteira")

if not st.session_state.wallet_created:
    st.info("Nenhuma carteira criada ainda.")
elif not st.session_state.unlocked:
    st.info("Entre na carteira para visualizar informações e endereços.")
else:
    try:
        idxs, addrs, w = load_addresses()
        st.write("**Account path:**", w["account_path"])
        st.write("**Rede:**", w.get("network", "testnet"))
        st.write("**Total de endereços derivados (visíveis):**", len(addrs))

        if addrs:
            current_recv = addrs[-1]
            st.write("**Endereço de recebimento atual:**")
            st.code(current_recv)

            # QR opcional (só se marcar)
            if "show_qr_current" not in st.session_state:
                st.session_state.show_qr_current = False
            st.session_state.show_qr_current = st.checkbox(
                "Mostrar QR do endereço atual",
                value=st.session_state.show_qr_current
            )
            if st.session_state.show_qr_current:
                st.image(_qr_png_bytes(current_recv), caption="QR do endereço atual")
        else:
            st.info("Nenhum endereço derivado além do inicial.")

        # Lista completa opcional (redigida)
        with st.expander("Ver lista completa de endereços (opcional / privacidade)", expanded=False):
            st.caption("Evite compartilhar esta lista. Revele apenas quando necessário.")
            page_size = st.number_input("Itens por página", min_value=3, max_value=100, value=8, step=1)
            total = len(addrs)
            total_pages = max(1, (total + page_size - 1) // page_size)
            page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1)
            start = (page - 1) * page_size
            end = min(start + page_size, total)

            def _redact(a: str) -> str:
                return a if len(a) <= 20 else f"{a[:10]}…{a[-8:]}"

            if total == 0:
                st.info("Nenhum endereço derivado salvo.")
            else:
                for i in range(start, end):
                    st.write(f"- #{idxs[i]}: `{_redact(addrs[i])}`")

                reveal_idx = st.number_input(
                    "Revelar endereço completo (índice)", min_value=0, max_value=max(0, total - 1), value=start
                )
                if st.button("Revelar endereço completo"):
                    st.warning("Revele com cuidado — não compartilhe publicamente.")
                    st.code(addrs[int(reveal_idx)])

                show_paths = st.checkbox("Mostrar derivation path (avançado)")
                if show_paths:
                    st.markdown("**Paths:**")
                    for i in range(start, end):
                        path = w["addresses"][str(idxs[i])]["path"]
                        st.write(f"- #{idxs[i]}: `{path}`")
    except Exception as e:
        st.error(f"Erro ao carregar informações: {e}")

st.header("➕ Gerar novo endereço")

if not st.session_state.wallet_created:
    st.info("Crie uma carteira primeiro.")
elif not st.session_state.unlocked:
    st.info("Entre na carteira para poder gerar novos endereços.")
else:
    with st.form("new_address_form", clear_on_submit=True):
        pwd_addr = st.text_input("Senha da carteira (necessária para derivar)", type="password")
        submitted_addr = st.form_submit_button("Gerar endereço")
    if submitted_addr:
        if not pwd_addr:
            st.error("Informe a senha.")
        else:
            try:
                addr = next_address(pwd_addr) 
                st.session_state.last_new_address = addr
                st.success("Novo endereço gerado.")
                st.write("**Endereço:**", addr)
                st.session_state.show_qr_new = st.checkbox(
                    "Mostrar QR do novo endereço",
                    value=st.session_state.show_qr_new,
                    key="show_qr_new_checkbox"
                )
                if st.session_state.show_qr_new:
                    st.image(_qr_png_bytes(addr), caption="QR do novo endereço")
            except Exception as e:
                st.error(f"Erro ao gerar novo endereço: {e}")


st.header("💳 Saldo ")

if not st.session_state.wallet_created:
    st.info("Crie uma carteira para consultar saldo.")
elif not st.session_state.unlocked:
    st.info("Entre na carteira para consultar saldo dos seus endereços.")
else:
    # placeholders/estados para limpar resultados antigos
    if "balance_placeholder" not in st.session_state:
        st.session_state.balance_placeholder = st.empty()
    if "prev_addr_selected" not in st.session_state:
        st.session_state.prev_addr_selected = None
    if "prev_aggregate" not in st.session_state:
        st.session_state.prev_aggregate = False

    try:
        idxs, addrs, _ = load_addresses()
        if not addrs:
            st.info("Nenhum endereço encontrado. Gere um novo em “➕ Gerar novo endereço”.")
        else:
            col_left, col_right = st.columns([3, 1])
            with col_left:
                addr_selected = st.selectbox(
                    "Endereço para consulta",
                    addrs,
                    index=len(addrs) - 1,
                    key="addr_select_balance"
                )
            with col_right:
                aggregate = st.checkbox(
                    "Somar todos os endereços",
                    value=False,
                    key="aggregate_balance"
                )

            # limpa automaticamente se trocar seleção/opção
            if (st.session_state.prev_addr_selected is not None and
                st.session_state.prev_addr_selected != addr_selected) or \
               (st.session_state.prev_aggregate != aggregate):
                st.session_state.balance_placeholder.empty()

            st.session_state.prev_addr_selected = addr_selected
            st.session_state.prev_aggregate = aggregate

            c1, c2 = st.columns([1, 1])
            consultar = c1.button("Consultar saldo")
            limpar = c2.button("Limpar resultado")

            if limpar:
                st.session_state.balance_placeholder.empty()

            if consultar:
                ph = st.session_state.balance_placeholder
                ph.empty()
                try:
                    with ph.container():
                        if aggregate:
                            confirmed = unconfirmed = total = 0
                            with st.spinner("Consultando todos os endereços..."):
                                for a in addrs:
                                    bal = get_balance(a)
                                    confirmed += int(bal.get("confirmed", 0))
                                    unconfirmed += int(bal.get("unconfirmed", 0))
                                    total += int(bal.get("total", 0))
                            st.subheader("Saldo agregado (todos os endereços)")
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Confirmado (sats)", f"{confirmed:,}".replace(",", "."))
                            m2.metric("Não confirmado (sats)", f"{unconfirmed:,}".replace(",", "."))
                            m3.metric("Total (sats)", f"{total:,}".replace(",", "."))
                        else:
                            with st.spinner("Consultando saldo..."):
                                bal = get_balance(addr_selected)
                            st.subheader("Saldo do endereço selecionado")
                            st.write("**Endereço:**", addr_selected)
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Confirmado (sats)", f"{int(bal['confirmed']):,}".replace(",", "."))
                            m2.metric("Não confirmado (sats)", f"{int(bal['unconfirmed']):,}".replace(",", "."))
                            m3.metric("Total (sats)", f"{int(bal['total']):,}".replace(",", "."))
                except Exception as e:
                    st.error(f"Erro ao consultar saldo: {e}")
    except Exception as e:
        st.error(f"Erro ao carregar endereços: {e}")

st.header("⚠️ Apagar carteira local")

if not st.session_state.wallet_created:
    st.info("Nenhuma carteira local encontrada para apagar.")
else:
    st.markdown(
        """
**Isto é irreversível.**  
Apagar a carteira remove o arquivo local (`~/.wowlie/wallet.json`).  
Você deve ter sua **SEED** anotada offline para poder recuperar depois.
        """
    )

    with st.form("delete_wallet_form", clear_on_submit=True):
        pwd_del = st.text_input("Senha da carteira", type="password")
        confirm_text = st.text_input("Para confirmar, digite: APAGAR")
        acknowledge = st.checkbox("Eu entendo que esta ação é irreversível.")
        submitted_delete = st.form_submit_button("Apagar carteira agora")

    if submitted_delete:
        if not acknowledge:
            st.error("Você precisa marcar que entendeu a irreversibilidade.")
        elif confirm_text.strip().upper() != "APAGAR":
            st.error("Digite exatamente APAGAR para confirmar.")
        elif not pwd_del:
            st.error("Informe a senha.")
        else:
            try:
                # verifica a senha antes de remover o arquivo
                if not verify_wallet_password(pwd_del):
                    st.error("Senha incorreta.")
                else:
                    path = _wallet_file_path()
                    if os.path.exists(path):
                        os.remove(path)

                    # limpa estados da UI
                    st.session_state.wallet_created = False
                    st.session_state.unlocked = False
                    st.session_state.just_created_seed = None
                    st.session_state.first_address = None
                    st.session_state.last_new_address = None
                    if "balance_placeholder" in st.session_state and st.session_state.balance_placeholder:
                        st.session_state.balance_placeholder.empty()
                    # flags de QR opcionais, se você as usa
                    for k in ("show_qr_initial", "show_qr_current", "show_qr_new"):
                        if k in st.session_state:
                            st.session_state[k] = False

                    st.success("Carteira local apagada com sucesso. Você pode criar uma nova abaixo.")
            except Exception as e:
                st.error(f"Erro ao apagar carteira: {e}")

with st.expander("🛡️ Boas práticas (lembrete)", expanded=False):
    st.markdown(
        """
- Endereços são públicos (não exponha seed/xprv/xpub).
- Mostrar endereços não revela chaves privadas, mas **pode afetar sua privacidade**.
- Evite compartilhar a lista completa; revele endereços completos só quando necessário.
- A senha NÃO é armazenada: cada ação sensível pede a senha novamente e ela é descartada.
- Use testnet para aprendizado; para mainnet, redobre os cuidados.
        """
    )