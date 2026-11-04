"""
Painel Visual (Dashboard Web) para o Monitor de Concursos do Instituto Avalia
Executável via: streamlit run dashboard.py
"""

import os
import json
import streamlit as st
from datetime import datetime

from avalia_api import get_concurso_info
from notifiers import NotificationDispatcher

st.set_page_config(
    page_title="Monitor Instituto Avalia",
    page_icon="🚨",
    layout="wide"
)

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"known_publicacoes": [], "known_links": [], "history": []}

config = load_config()
state = load_state()

st.title("🚨 Monitor Instituto Avalia - Concurso 619")
st.markdown("Painel de controle e acompanhamento em tempo real para publicações da banca **Instituto Avalia**.")

tab1, tab2, tab3 = st.tabs(["📊 Visão Geral & Publicações", "🔔 Configurar Alertas", "⚡ Teste de Notificação"])

with tab1:
    col1, col2, col3 = st.columns(3)
    
    with st.spinner("Consultando dados oficiais da banca Avalia..."):
        try:
            concurso_id = config.get("concurso_id", 619)
            info = get_concurso_info(concurso_id)
            total_pubs = len(info.get("publicacoes", []))
            total_links = len(info.get("links", []))
            
            col1.metric("Concurso", f"ID {concurso_id}")
            col2.metric("Total de Publicações", total_pubs)
            col3.metric("Links / Sistemas", total_links)
            
            st.subheader(f"🏛 {info.get('nome')}")
            st.caption(f"Status: **{info.get('status')}** | Edital: **{info.get('edital')}** | [Abrir Página Oficial](https://www.avalia.org.br/concursos/{concurso_id})")
            
            st.divider()
            st.write("### 📄 Publicações Recentes na Banca")
            
            pubs = info.get("publicacoes", [])
            if pubs:
                for idx, pub in enumerate(pubs[:15]):
                    with st.container():
                        c_title, c_btn = st.columns([4, 1])
                        c_title.markdown(f"**{pub.get('nome')}**  \n`ID: {pub.get('id')}`")
                        c_btn.link_button("📥 Abrir PDF", pub.get("url", "#"))
                        st.divider()
            else:
                st.info("Nenhuma publicação encontrada no momento.")
                
        except Exception as e:
            st.error(f"Erro ao consultar a banca: {e}")

with tab2:
    st.subheader("Configurações dos Canais de Notificação")
    st.info("Ative os meios que deseja receber o alerta assim que a banca publicar o resultado hoje.")
    
    with st.form("form_config"):
        st.write("#### 1. Push no Celular / Navegador (ntfy.sh - Recomendado & Grátis)")
        ntfy_enabled = st.checkbox("Ativar ntfy.sh", value=config.get("ntfy", {}).get("enabled", True))
        ntfy_topic = st.text_input("Tópico ntfy.sh", value=config.get("ntfy", {}).get("topic", "avalia_concurso_619_alerta"))
        st.caption(f"Abra no navegador do celular ou app ntfy: **https://ntfy.sh/{ntfy_topic}** e clique em Inscrever-se.")

        st.divider()
        st.write("#### 2. Notificação no Windows (PC)")
        win_enabled = st.checkbox("Ativar Pop-up no Windows", value=config.get("windows", {}).get("enabled", True))
        win_sound = st.checkbox("Tocar Alarme Sonoro (Beep de Atenção)", value=config.get("windows", {}).get("play_sound", True))

        st.divider()
        st.write("#### 3. E-mail (SMTP)")
        email_enabled = st.checkbox("Ativar Notificação por E-mail", value=config.get("email", {}).get("enabled", False))
        c_e1, c_e2 = st.columns(2)
        smtp_host = c_e1.text_input("Servidor SMTP", value=config.get("email", {}).get("smtp_host", "smtp.gmail.com"))
        smtp_port = c_e2.number_input("Porta", value=int(config.get("email", {}).get("smtp_port", 587)))
        smtp_user = c_e1.text_input("Usuário / E-mail Remetente", value=config.get("email", {}).get("smtp_user", ""))
        smtp_pass = c_e2.text_input("Senha de App (App Password)", value=config.get("email", {}).get("smtp_pass", ""), type="password")
        to_email = st.text_input("E-mail de Destino (onde receberá o alerta)", value=config.get("email", {}).get("to_email", ""))

        st.divider()
        st.write("#### 4. Telegram Bot")
        tg_enabled = st.checkbox("Ativar Telegram", value=config.get("telegram", {}).get("enabled", False))
        tg_token = st.text_input("Bot Token", value=config.get("telegram", {}).get("bot_token", ""))
        tg_chat = st.text_input("Chat ID", value=config.get("telegram", {}).get("chat_id", ""))

        st.divider()
        interval = st.number_input("Intervalo de Checagem (segundos)", min_value=15, max_value=600, value=int(config.get("interval_seconds", 60)))

        submit = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
        if submit:
            config["interval_seconds"] = int(interval)
            config.setdefault("windows", {})["enabled"] = win_enabled
            config["windows"]["play_sound"] = win_sound
            config.setdefault("ntfy", {})["enabled"] = ntfy_enabled
            config["ntfy"]["topic"] = ntfy_topic.strip()
            config.setdefault("email", {})["enabled"] = email_enabled
            config["email"]["smtp_host"] = smtp_host.strip()
            config["email"]["smtp_port"] = int(smtp_port)
            config["email"]["smtp_user"] = smtp_user.strip()
            config["email"]["smtp_pass"] = smtp_pass.strip()
            config["email"]["from_email"] = smtp_user.strip()
            config["email"]["to_email"] = to_email.strip()
            config.setdefault("telegram", {})["enabled"] = tg_enabled
            config["telegram"]["bot_token"] = tg_token.strip()
            config["telegram"]["chat_id"] = tg_chat.strip()

            save_config(config)
            st.success("Configurações salvas com sucesso!")

with tab3:
    st.subheader("Testar Disparo de Alertas")
    st.write("Clique abaixo para enviar uma mensagem teste para todos os canais que estiverem ativados.")
    if st.button("🚀 Enviar Notificação de Teste Agora", use_container_width=True):
        dispatcher = NotificationDispatcher(config)
        test_url = f"https://www.avalia.org.br/concursos/{config.get('concurso_id', 619)}"
        results = dispatcher.send_all(
            title="TESTE DE ALERTA - MONITOR AVALIA",
            message="Alerta de teste do monitor de concurso! Seu canal está funcionando 100%.",
            url=test_url,
            extra_data={"concurso_nome": config.get("nome_amigavel", "Concurso 619")}
        )
        for ch, status in results.items():
            if status:
                st.success(f"Canal **{ch.upper()}**: Notificação enviada com sucesso!")
            else:
                st.warning(f"Canal **{ch.upper()}**: Falha ou canal desativado.")

