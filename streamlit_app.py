import io, os
import qrcode
import streamlit as st
from wallet.keys import init_wallet, next_address, verify_wallet_password
from wallet.utils import wallet_exists, load_addresses
from wallet.password import validate_password_strength
from wallet.network import get_balance
from wallet.transactions import build_tx_plan, broadcast_tx_hex, send_transaction


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

if "tx_plan" not in st.session_state:
    st.session_state.tx_plan = None

st.title("💰 WowLie Wallet")
st.caption("Carteira BigCute Testnet segura")

st.header("🪙 Criar carteira")

if st.session_state.wallet_created:
    st.info("✅ Uma carteira já existe neste dispositivo. Para criar outra, apague a atual em '⚠️ Apagar carteira'.")
else:
    st.markdown(
        "> **⚠️ Atenção:** A seed (12 palavras) será exibida **uma única vez** após a criação. "
        "Anote **offline** e guarde com segurança. Sem a seed **ou** sem a senha, você perde tudo."
    )

    with st.form("create_wallet_form", clear_on_submit=True):
        pwd = st.text_input("Defina a senha da carteira", type="password")
        pwd2 = st.text_input("Confirme a senha", type="password")
        submitted_create = st.form_submit_button("Criar carteira")

    if submitted_create:
        ok, errs = validate_password_strength(pwd)
        if not ok:
            st.error("❌ Senha fraca:")
            for e in errs:
                st.write(f"- {e}")
        elif pwd != pwd2:
            st.error("❌ As senhas não coincidem.")
        else:
            try:
                result = init_wallet(pwd)
                st.session_state.wallet_created = True
                st.session_state.unlocked = True
                st.session_state.just_created_seed = result["mnemonic"]
                st.session_state.first_address = result["first_address"]

                st.success("✅ Carteira criada.")

                with st.expander("📜 Seed (exibida apenas agora)", expanded=True):
                    st.warning("⚠️ ANOTE OFFLINE e mantenha em local seguro. NÃO compartilhe.")
                    st.code(st.session_state.just_created_seed)
                    if st.button("✅ Já anotei / ocultar seed"):
                        st.session_state.just_created_seed = None
                        st.rerun()

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
                st.error(f"❌ Erro ao criar carteira: {e}")

st.header("🔐 Entrar na carteira")

if not st.session_state.unlocked:
    if not st.session_state.wallet_created:
        st.info("Nenhuma carteira encontrada ainda. Crie uma acima em '🪙 Criar carteira'.")
    else:
        with st.form("login_form", clear_on_submit=True):
            pwd_try = st.text_input("Senha da carteira", type="password")
            submitted_login = st.form_submit_button("Entrar")
        
        if submitted_login:
            if not wallet_exists():
                st.error("❌ Não há carteira salva. Crie uma primeiro.")
            else:
                try:
                    if verify_wallet_password(pwd_try):
                        st.session_state.unlocked = True
                        st.success("✅ Carteira desbloqueada — sessão ativa.")
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta.")
                except Exception as e:
                    st.error(f"❌ Erro ao verificar senha: {e}")
else:
    col1, col2 = st.columns([3, 1])
    col1.success("✅ Sessão ativa: carteira desbloqueada.")
    if col2.button("Sair"):
        st.session_state.unlocked = False
        st.session_state.show_qr_current = False
        st.session_state.show_qr_new = False
        st.session_state.balance_result = None
        st.rerun()

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
        st.write("**Total de endereços derivados:**", len(addrs))

        if addrs:
            current_recv = addrs[-1]
            st.write("**Endereço de recebimento atual:**")
            st.code(current_recv)

            st.session_state.show_qr_current = st.checkbox(
                "Mostrar QR do endereço atual",
                value=st.session_state.show_qr_current
            )
            if st.session_state.show_qr_current:
                st.image(_qr_png_bytes(current_recv), caption="QR do endereço atual")
        else:
            st.info("Nenhum endereço derivado além do inicial.")

        with st.expander("Ver lista completa de endereços", expanded=False):
            st.caption("⚠️ Evite compartilhar esta lista. Revele apenas quando necessário.")
            page_size = st.number_input("Itens por página", min_value=3, max_value=100, value=8, step=1)
            total = len(addrs)
            total_pages = max(1, (total + page_size - 1) // page_size)
            page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1)
            start = (page - 1) * page_size
            end = min(start + page_size, total)

            if total == 0:
                st.info("Nenhum endereço derivado salvo.")
            else:
                for i in range(start, end):
                    st.write(f"- #{idxs[i]}: `{_redact(addrs[i])}`")

                reveal_idx = st.number_input(
                    "Revelar endereço completo (índice)", min_value=0, max_value=max(0, total - 1), value=start
                )
                if st.button("Revelar endereço completo"):
                    st.warning("⚠️ Revele com cuidado — não compartilhe publicamente.")
                    st.code(addrs[int(reveal_idx)])

                show_paths = st.checkbox("Mostrar derivation path (avançado)")
                if show_paths:
                    st.markdown("**Paths:**")
                    for i in range(start, end):
                        path = w["addresses"][str(idxs[i])]["path"]
                        st.write(f"- #{idxs[i]}: `{path}`")
    except Exception as e:
        st.error(f"❌ Erro ao carregar informações: {e}")

st.header("➕ Gerar novo endereço")

if not st.session_state.wallet_created:
    st.info("Crie uma carteira primeiro.")
elif not st.session_state.unlocked:
    st.info("Entre na carteira para poder gerar novos endereços.")
else:
    with st.form("new_address_form", clear_on_submit=True):
        pwd_addr = st.text_input("Senha da carteira", type="password")
        submitted_addr = st.form_submit_button("Gerar endereço")
    
    if submitted_addr:
        if not pwd_addr:
            st.error("❌ Informe a senha.")
        else:
            try:
                addr = next_address(pwd_addr) 
                st.session_state.last_new_address = addr
                st.success("✅ Novo endereço gerado.")
                st.write("**Endereço:**")
                st.code(addr)
                
                st.session_state.show_qr_new = st.checkbox(
                    "Mostrar QR do novo endereço",
                    value=st.session_state.show_qr_new,
                    key="show_qr_new_checkbox"
                )
                if st.session_state.show_qr_new:
                    st.image(_qr_png_bytes(addr), caption="QR do novo endereço")
            except Exception as e:
                st.error(f"❌ Erro ao gerar novo endereço: {e}")


st.header("💳 Consultar saldo")

if not st.session_state.wallet_created:
    st.info("Crie uma carteira para consultar saldo.")
elif not st.session_state.unlocked:
    st.info("Entre na carteira para consultar saldo dos seus endereços.")
else:
    try:
        idxs, addrs, _ = load_addresses()
        if not addrs:
            st.info("Nenhum endereço encontrado. Gere um em '➕ Gerar novo endereço'.")
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
                    "Somar todos",
                    value=False,
                    key="aggregate_balance"
                )

            c1, c2 = st.columns([1, 1])
            consultar = c1.button("Consultar saldo", type="primary")
            limpar = c2.button("Limpar resultado")

            if "balance_result" not in st.session_state:
                st.session_state.balance_result = None

            if limpar:
                st.session_state.balance_result = None

            if consultar:
                try:
                    if aggregate:
                        confirmed = unconfirmed = total = 0
                        with st.spinner("Consultando todos os endereços..."):
                            for a in addrs:
                                bal = get_balance(a)
                                confirmed += int(bal.get("confirmed", 0))
                                unconfirmed += int(bal.get("unconfirmed", 0))
                                total += int(bal.get("total", 0))
                        
                        st.session_state.balance_result = {
                            "type": "aggregate",
                            "confirmed": confirmed,
                            "unconfirmed": unconfirmed,
                            "total": total
                        }
                    else:
                        with st.spinner("Consultando saldo..."):
                            bal = get_balance(addr_selected)
                        
                        st.session_state.balance_result = {
                            "type": "single",
                            "address": addr_selected,
                            "confirmed": int(bal.get("confirmed", 0)),
                            "unconfirmed": int(bal.get("unconfirmed", 0)),
                            "total": int(bal.get("total", 0))
                        }
                except Exception as e:
                    st.error(f"❌ Erro ao consultar saldo: {e}")
                    st.session_state.balance_result = None

            if st.session_state.balance_result:
                result = st.session_state.balance_result
                
                if result["type"] == "aggregate":
                    st.subheader("💰 Saldo agregado (todos os endereços)")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Confirmado (sats)", f"{result['confirmed']:,}".replace(",", "."))
                    m2.metric("Não confirmado (sats)", f"{result['unconfirmed']:,}".replace(",", "."))
                    m3.metric("Total (sats)", f"{result['total']:,}".replace(",", "."))
                else:
                    st.subheader("💰 Saldo do endereço")
                    st.write("**Endereço:**", result["address"])
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Confirmado (sats)", f"{result['confirmed']:,}".replace(",", "."))
                    m2.metric("Não confirmado (sats)", f"{result['unconfirmed']:,}".replace(",", "."))
                    m3.metric("Total (sats)", f"{result['total']:,}".replace(",", "."))
                    
    except Exception as e:
        st.error(f"❌ Erro ao carregar endereços: {e}")

# ============= ENVIAR TRANSAÇÃO =============
st.header("📤 Enviar transação")

if not st.session_state.wallet_created:
    st.info("Crie uma carteira primeiro.")
elif not st.session_state.unlocked:
    st.info("Entre na carteira para enviar transações.")
else:
    st.markdown("""
    Você pode **(A)** criar um plano não assinado para usar em outra carteira (ex.: Sparrow),  
    ou **(B)** **assinar e enviar localmente** com a WowLie (testnet).
    """)

    # ------------------ (A) CRIAR PLANO (não assina) ------------------
    with st.expander("1️⃣ Criar plano de transação (não assina)", expanded=True):
        with st.form("tx_plan_form"):
            try:
                idxs, addrs, _ = load_addresses()
                from_addr = st.selectbox("Do endereço", addrs, index=len(addrs)-1)
            except Exception:
                from_addr = st.text_input("Do endereço")

            to_addr = st.text_input("Para endereço (destino)")
            amount = st.number_input("Quantia (satoshis)", min_value=1, value=10000, step=1000)
            fee_rate = st.number_input("Taxa (sats/vByte)", min_value=1, value=5, step=1)

            try:
                _, addrs_change, _ = load_addresses()
                if addrs_change:
                    change_addr = st.selectbox("Endereço de troco", addrs_change, index=len(addrs_change)-1)
                else:
                    change_addr = from_addr
            except Exception:
                change_addr = from_addr

            submitted_tx = st.form_submit_button("Criar plano de TX")

        if submitted_tx:
            if not to_addr:
                st.error("❌ Informe o endereço de destino.")
            elif amount <= 0:
                st.error("❌ Quantia deve ser maior que zero.")
            else:
                try:
                    with st.spinner("Criando plano de transação..."):
                        plan = build_tx_plan(
                            from_address=from_addr,
                            to_address=to_addr,
                            amount_sats=amount,
                            fee_rate=fee_rate,
                            change_address=change_addr
                        )

                    st.session_state.tx_plan = plan
                    st.success("✅ Plano criado.")

                    st.subheader("📋 Resumo do plano")
                    c1, c2 = st.columns(2)
                    c1.metric("Valor a enviar", f"{plan['amount_sats']:,} sats")
                    c2.metric("Taxa estimada", f"{plan['estimated_fee_sats']:,} sats")
                    c1.metric("Troco", f"{plan.get('change_sats', 0):,} sats")
                    c2.metric("Tamanho estimado", f"{plan['estimated_vbytes']} vBytes")

                    st.write("**De:**", plan['from_address'])
                    st.write("**Para:**", plan['to_address'])
                    if plan.get('change_address'):
                        st.write("**Troco para:**", plan['change_address'])

                    with st.expander("Ver JSON completo"):
                        st.json(plan)

                    st.info("""
                    **Se quiser assinar externamente:**
                    1. Abra o Sparrow Wallet em **testnet**
                    2. Importe sua seed (12 palavras)
                    3. Crie/assine a transação com os valores do plano
                    4. Copie o TX HEX assinado e faça broadcast abaixo
                    """)
                except Exception as e:
                    st.error(f"❌ Erro ao criar plano: {e}")

    # ------------------ (B) ASSINAR E ENVIAR LOCALMENTE ------------------
    with st.expander("2️⃣ Assinar e enviar localmente (WowLie)", expanded=False):
        with st.form("tx_send_form"):
            try:
                idxs2, addrs2, _ = load_addresses()
                from_addr2 = st.selectbox("Do endereço", addrs2, index=len(addrs2)-1, key="send_from_addr")
            except Exception:
                from_addr2 = st.text_input("Do endereço", key="send_from_addr_text")

            to_addr2 = st.text_input("Para endereço (destino)", key="send_to_addr")
            amount2 = st.number_input("Quantia (satoshis)", min_value=1, value=10000, step=1000, key="send_amount")
            fee_rate2 = st.number_input("Taxa (sats/vByte)", min_value=1, value=5, step=1, key="send_fee")
            try:
                _, addrs_change2, _ = load_addresses()
                if addrs_change2:
                    change_addr2 = st.selectbox("Endereço de troco", addrs_change2, index=len(addrs_change2)-1, key="send_change")
                else:
                    change_addr2 = from_addr2
            except Exception:
                change_addr2 = from_addr2

            no_broadcast = st.checkbox("Assinar mas não enviar (mostrar/salvar HEX)", value=False, key="send_no_broadcast")
            out_hex_name = st.text_input("Salvar HEX em arquivo (opcional)", value="", placeholder="ex.: signed_tx_hex.txt", key="send_hex_file")

            # Senha só para assinar localmente
            password_local = st.text_input("Senha da carteira", type="password", key="send_wallet_pwd")

            submitted_send = st.form_submit_button("Assinar (e enviar, se marcado)")

        if submitted_send:
            if not to_addr2:
                st.error("❌ Informe o endereço de destino.")
            elif amount2 <= 0:
                st.error("❌ Quantia deve ser maior que zero.")
            elif not password_local:
                st.error("❌ Digite a senha da carteira.")
            else:
                try:
                    with st.spinner("Construindo e assinando a transação..."):
                        tx_data = send_transaction(
                            from_address=from_addr2,
                            to_address=to_addr2,
                            amount_sats=amount2,
                            password=password_local,
                            fee_rate=fee_rate2,
                            change_address=change_addr2,
                            broadcast=not no_broadcast
                        )

                    st.success("✅ Transação assinada.")
                    st.subheader("Resumo")
                    c1, c2 = st.columns(2)
                    c1.metric("Valor enviado", f"{tx_data['amount_sats']:,} sats")
                    c2.metric("Taxa", f"{tx_data['fee_sats']:,} sats")
                    if tx_data.get("change_address"):
                        st.write(f"**Troco:** {tx_data['change_sats']:,} sats → {tx_data['change_address']}")
                    st.write(f"**Inputs:** {tx_data['inputs']}  |  **Outputs:** {tx_data['outputs']}")
                    st.write(f"**Tamanho estimado:** {tx_data['vbytes']} vBytes")
                    st.code(f"TXID (calculado): {tx_data['txid']}")

                    if no_broadcast:
                        st.info("Transação **não** enviada. Você pode usar o HEX abaixo em outra ferramenta.")
                        st.text_area("TX HEX assinado", tx_data["signed_tx_hex"], height=160)
                        if out_hex_name.strip():
                            st.download_button(
                                "Baixar HEX",
                                data=tx_data["signed_tx_hex"],
                                file_name=out_hex_name.strip(),
                                mime="text/plain"
                            )
                    else:
                        txid_brd = tx_data.get("txid_broadcast", tx_data["txid"])
                        st.success("Transação enviada para a rede (testnet).")
                        st.code(txid_brd)
                        st.markdown(f"[Ver na Blockstream](https://blockstream.info/testnet/tx/{txid_brd})")
                except Exception as e:
                    st.error(f"❌ Erro ao assinar/enviar: {e}")

    # ------------------ BROADCAST EXTERNO (HEX pronto) ------------------
    with st.expander("3️⃣ Fazer broadcast de TX assinado (externo)", expanded=False):
        st.markdown("Cole o **transaction hex** já assinado (de outra wallet).")
        tx_hex = st.text_area("Transaction HEX assinado", height=150, placeholder="0200000001...")

        if st.button("📡 Broadcast TX"):
            if not tx_hex or not tx_hex.strip():
                st.error("❌ Cole o TX HEX assinado.")
            else:
                try:
                    with st.spinner("Enviando transação para a rede..."):
                        txid = broadcast_tx_hex(tx_hex)
                    st.success("✅ Transação enviada com sucesso!")
                    st.code(txid)
                    st.markdown(f"[Ver na Blockstream](https://blockstream.info/testnet/tx/{txid})")
                except Exception as e:
                    st.error(f"❌ Erro ao enviar transação: {e}")


# ============= APAGAR CARTEIRA =============
st.header("⚠️ Apagar carteira local")

if not st.session_state.wallet_created:
    st.info("Nenhuma carteira local encontrada para apagar.")
else:
    st.markdown("""
    **⚠️ Isto é irreversível!**  
    Apagar a carteira remove o arquivo local.  
    Você **deve** ter sua **SEED** (12 palavras) anotada offline para poder recuperar depois.
    """)

    with st.form("delete_wallet_form", clear_on_submit=True):
        pwd_del = st.text_input("Senha da carteira", type="password")
        confirm_text = st.text_input("Para confirmar, digite: APAGAR")
        acknowledge = st.checkbox("Eu entendo que esta ação é irreversível.")
        submitted_delete = st.form_submit_button("Apagar carteira agora")

    if submitted_delete:
        if not acknowledge:
            st.error("❌ Você precisa marcar que entendeu a irreversibilidade.")
        elif confirm_text.strip().upper() != "APAGAR":
            st.error("❌ Digite exatamente APAGAR para confirmar.")
        elif not pwd_del:
            st.error("❌ Informe a senha.")
        else:
            try:
                if not verify_wallet_password(pwd_del):
                    st.error("❌ Senha incorreta.")
                else:
                    path = _wallet_file_path()
                    if os.path.exists(path):
                        os.remove(path)

                    # Limpa estados
                    st.session_state.wallet_created = False
                    st.session_state.unlocked = False
                    st.session_state.just_created_seed = None
                    st.session_state.first_address = None
                    st.session_state.last_new_address = None
                    st.session_state.tx_plan = None
                    st.session_state.balance_result = None
                    for k in ("show_qr_initial", "show_qr_current", "show_qr_new"):
                        if k in st.session_state:
                            st.session_state[k] = False

                    st.success("✅ Carteira local apagada com sucesso.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao apagar carteira: {e}")

# ============= RODAPÉ =============
with st.expander("🛡️ Boas práticas de segurança", expanded=False):
    st.markdown("""
    - **Endereços são públicos**, mas não exponha sua seed/senha
    - Mostrar endereços não revela chaves privadas, mas pode afetar sua **privacidade**
    - Evite compartilhar a lista completa de endereços publicamente
    - A **senha NÃO é armazenada**: cada ação pede a senha novamente e ela é descartada
    - Use **testnet** para aprendizado; para mainnet, redobre os cuidados
    - Para valores significativos, use **hardware wallets** (Ledger, Trezor)
    - **Faça backup** das 12 palavras em papel, em múltiplos locais seguros
    - Teste a recuperação da carteira antes de depositar valores importantes
    """)

st.divider()
st.caption("WowLie Wallet v1.0 - Testnet BigCute")