# app.py - Streamlit dashboard
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import sys
import asyncio

# add modules path
sys.path.append(str(Path(__file__).parent))

from modules.youtube import YouTubePlatform
from modules.instagram import InstagramPlatform
from modules.tiktok import TikTokPlatform
from modules.pinterest import PinterestPlatform
from modules.x_twitter import XTwitterPlatform
from modules.linkedin import LinkedInPlatform
import database as db

st.set_page_config(page_title="Francos Corp - Social Automation", layout="wide")

# Initialize DB
db.init_db()

# Helper to run async functions
def run_async(coro):
    return asyncio.run(coro)

# Load platforms
SESSION_DIR = Path(__file__).parent / "sessions"
PLATFORMS = {
    "YouTube": YouTubePlatform(SESSION_DIR),
    "Instagram": InstagramPlatform(SESSION_DIR),
    "TikTok": TikTokPlatform(SESSION_DIR),
    "Pinterest": PinterestPlatform(SESSION_DIR),
    "X (Twitter)": XTwitterPlatform(SESSION_DIR),
    "LinkedIn": LinkedInPlatform(SESSION_DIR),
}

def get_conn():
    return sqlite3.connect(db.DB_PATH)

def load_videos():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM videos ORDER BY created_at DESC", conn)
    conn.close()
    return df

def load_logs():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY created_at DESC LIMIT 200", conn)
    conn.close()
    return df

def load_accounts():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM accounts", conn)
    conn.close()
    return df

st.title("🎬 Francos Corp – Social Automation Dashboard")

tabs = st.tabs(["🏠 Home", "🔐 Logins", "📤 Queue", "📜 Logs"])

# ---- Home ----
with tabs[0]:
    st.subheader("Status Geral")
    videos = load_videos()
    total = len(videos)
    posted = len(videos[videos["status"] == "posted"])
    pending = len(videos[videos["status"] == "pending"])
    error = len(videos[videos["status"] == "error"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("Postados", posted)
    c3.metric("Pendentes", pending)
    c4.metric("Erros", error)

    st.subheader("Conexões")
    accounts = load_accounts()
    if not accounts.empty:
        for _, row in accounts.iterrows():
            status = "🟢 Conectado" if row["connected"] else "🔴 Desconectado"
            st.write(f"{row['platform']}: {status}")
    else:
        st.info("Nenhuma conta registrada ainda.")

# ---- Logins ----
with tabs[1]:
    st.subheader("Gerenciar Logins")
    for name, platform in PLATFORMS.items():
        col1, col2 = st.columns([3,1])
        connected = platform.is_logged_in()
        col1.write(f"**{name}** – {'✅ Conectado' if connected else '❌ Desconectado'}")
        if col2.button(f"{'Desconectar' if connected else 'Conectar'} {name}", key=f"conn_{name}"):
            if connected:
                # logout: clear session file
                session_file = Path(__file__).parent / "sessions" / platform.platform_name / "session.json"
                if session_file.exists():
                    session_file.unlink()
                st.success(f"{name} desconectado.")
            else:
                with st.spinner(f"Abrindo navegador para login em {name}..."):
                    try:
                        run_async(platform.login_interactive())
                        st.success(f"{name} conectado!")
                    except Exception as e:
                        st.error(f"Erro ao conectar {name}: {e}")

# ---- Queue ----
with tabs[2]:
    st.subheader("Fila de Publicação")
    uploaded = st.file_uploader("Selecione vídeo(s)", type=["mp4","mov","mkv"], accept_multiple_files=True)
    title = st.text_input("Título")
    description = st.text_area("Descrição")
    tags = st.text_input("Tags (separadas por vírgula)")
    platforms_sel = st.multiselect("Plataformas", list(PLATFORMS.keys()), default=["YouTube","Instagram","TikTok"])
    if st.button("Adicionar à fila") and uploaded:
        conn = get_conn()
        cur = conn.cursor()
        for f in uploaded:
            path = Path("assets") / f.name
            path.parent.mkdir(exist_ok=True)
            with open(path, "wb") as out:
                out.write(f.getbuffer())
            cur.execute(
                "INSERT INTO videos (file_path,title,description,tags) VALUES (?,?,?,?)",
                (str(path), title, description, tags)
            )
        conn.commit()
        conn.close()
        st.success(f"{len(uploaded)} vídeo(s) adicionados à fila.")
        st.rerun()

    st.markdown("---")
    st.subheader("Fila atual")
    df = load_videos()
    if not df.empty:
        st.dataframe(df[["id","title","status","created_at"]], use_container_width=True)
        if st.button("Publicar pendentes"):
            # simple loop
            for _, row in df[df["status"]=="pending"].iterrows():
                for plat_name in platforms_sel:
                    platform = PLATFORMS[plat_name]
                    if not platform.is_logged_in():
                        st.warning(f"{plat_name} não conectado.")
                        continue
                    # TODO: async post
                    st.info(f"Postando {row['title']} no {plat_name} ...")
            st.success("Processamento iniciado (ver logs).")
    else:
        st.info("Nenhum vídeo na fila.")

# ---- Logs ----
with tabs[3]:
    st.subheader("Logs Recentes")
    logs = load_logs()
    if not logs.empty:
        st.dataframe(logs, use_container_width=True)
    else:
        st.info("Nenhum log ainda.")
