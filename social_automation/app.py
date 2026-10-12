"""Authenticated Streamlit dashboard for an explicit YouTube publishing queue."""

import asyncio
import hmac
import os
from pathlib import Path
import sqlite3
import uuid

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")

import database as db
from modules.base import VideoMeta
from modules.youtube import YouTubePlatform


MAX_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_BATCH_BYTES = 200 * 1024 * 1024
ALLOWED_SUFFIXES = {".mp4", ".mov", ".mkv"}
SESSION_DIR = Path(os.environ.get("SESSION_DIR", Path(__file__).parents[1] / "sessions")).expanduser().resolve()
PLATFORMS = {"YouTube": "youtube"}


def read_media_retention_days() -> int:
    raw_value = os.environ.get("MEDIA_RETENTION_DAYS", "0").strip()
    try:
        retention_days = int(raw_value)
    except ValueError as exc:
        raise ValueError("MEDIA_RETENTION_DAYS precisa ser um inteiro entre 0 e 36500.") from exc
    if not 0 <= retention_days <= 36500:
        raise ValueError("MEDIA_RETENTION_DAYS precisa estar entre 0 e 36500.")
    return retention_days


MEDIA_RETENTION_DAYS = read_media_retention_days()


def require_dashboard_password() -> None:
    configured_password = os.environ.get("DASHBOARD_PASSWORD", "")
    if len(configured_password) < 16:
        st.error("Configure uma DASHBOARD_PASSWORD com pelo menos 16 caracteres antes de iniciar o painel.")
        st.stop()

    if st.session_state.get("authenticated"):
        return

    st.title("Acesso ao painel")
    with st.form("login"):
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)
    if submitted:
        if hmac.compare_digest(password.encode("utf-8"), configured_password.encode("utf-8")):
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Senha inválida.")
    st.stop()


def save_upload(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Formato não suportado. Use MP4, MOV ou MKV.")
    if not uploaded_file.size or uploaded_file.size > MAX_UPLOAD_BYTES:
        raise ValueError("O vídeo precisa ter entre 1 byte e 200 MB.")
    data = uploaded_file.getvalue()
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("O arquivo está vazio ou ultrapassa o limite de 200 MB.")
    if suffix in {".mp4", ".mov"} and data[4:8] != b"ftyp":
        raise ValueError("O conteúdo do arquivo não corresponde a um vídeo MP4 ou MOV.")
    if suffix == ".mkv" and not data.startswith(b"\x1a\x45\xdf\xa3"):
        raise ValueError("O conteúdo do arquivo não corresponde a um vídeo Matroska.")

    assets_dir = db.DATA_DIR / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(assets_dir, 0o700)
    except OSError:
        pass
    destination = assets_dir / f"{uuid.uuid4().hex}{suffix}"
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as output:
        output.write(data)
    return destination


def publish_pending(platform: YouTubePlatform, privacy: str) -> tuple[int, int]:
    posted = 0
    failed = 0
    for target in db.list_pending_targets():
        if target["platform"] != "youtube":
            db.finish_target(target["target_id"], "error", "Integração indisponível nesta versão.")
            failed += 1
            continue
        if not db.claim_target(target["target_id"]):
            continue
        try:
            tags = [tag.strip() for tag in target["tags"].split(",") if tag.strip()]
            file_path = Path(target["file_path"]).expanduser().resolve()
            asset_root = (db.DATA_DIR / "assets").resolve()
            if not file_path.is_relative_to(asset_root):
                raise ValueError("O caminho do vídeo não pertence ao armazenamento da fila.")
            result = asyncio.run(
                platform.post_video(
                    VideoMeta(
                        file_path=file_path,
                        title=target["title"],
                        description=target["description"],
                        tags=tags,
                    ),
                    privacy=privacy,
                )
            )
            remote_id = result.get("video_id")
            db.finish_target(
                target["target_id"],
                "posted",
                f"Publicado no YouTube. ID: {remote_id}" if remote_id else "Publicado no YouTube.",
                remote_id=remote_id,
            )
            posted += 1
        except Exception as exc:
            # Provider details can contain private request data; keep only the error type.
            message = f"Falha no upload ({type(exc).__name__})."
            db.finish_target(target["target_id"], "error", message)
            failed += 1
    return posted, failed


st.set_page_config(page_title="Francos Corp — Publicação de vídeos", page_icon="🎬", layout="wide")
require_dashboard_password()
db.init_db()
youtube = YouTubePlatform(SESSION_DIR)

with st.sidebar:
    st.markdown("### Francos Corp")
    st.caption("Painel privado de publicação de vídeos")
    st.write("YouTube: " + ("🟢 conectado" if youtube.is_logged_in() else "🔴 sem credencial válida"))
    if st.button("Sair", use_container_width=True):
        st.session_state.pop("authenticated", None)
        st.rerun()

st.title("🎬 Publicação de vídeos")
st.caption("Os uploads só começam quando você aciona Publicar. A privacidade padrão é privada.")
tabs = st.tabs(["Visão geral", "Fila", "Conta YouTube", "Registros"])

with tabs[0]:
    stats = db.get_stats()
    columns = st.columns(5)
    for column, label, key in zip(
        columns,
        ("Vídeos", "Publicados", "Pendentes", "Em andamento", "Com falha"),
        ("total", "posted", "pending", "processing", "error"),
    ):
        column.metric(label, stats[key])
    if stats["partial"]:
        st.info(f"{stats['partial']} vídeo(s) têm destinos publicados e destinos com falha.")
    st.markdown("#### Integrações disponíveis")
    st.success("YouTube — API oficial do Google")
    st.info("Instagram, TikTok, Pinterest, X e LinkedIn ainda não estão disponíveis para publicação.")

with tabs[1]:
    st.subheader("Adicionar à fila")
    with st.form("queue_upload", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Selecione vídeos (MP4, MOV ou MKV; até 200 MB por envio)",
            type=["mp4", "mov", "mkv"],
            accept_multiple_files=True,
        )
        title = st.text_input("Título", max_chars=100)
        description = st.text_area("Descrição", max_chars=5000)
        tags_text = st.text_input("Tags separadas por vírgula")
        submitted = st.form_submit_button("Adicionar à fila", type="primary")
    if submitted:
        if not uploaded_files:
            st.error("Selecione ao menos um vídeo.")
        elif sum(uploaded_file.size for uploaded_file in uploaded_files) > MAX_BATCH_BYTES:
            st.error("O tamanho total dos vídeos deste envio ultrapassa 200 MB.")
        else:
            queued = 0
            for uploaded_file in uploaded_files:
                saved_path = None
                try:
                    saved_path = save_upload(uploaded_file)
                    clean_title = title.strip() or Path(uploaded_file.name).stem[:100] or "Vídeo"
                    tags = [tag.strip()[:500] for tag in tags_text.split(",") if tag.strip()][:500]
                    db.enqueue_video(saved_path, clean_title, description, tags, ["youtube"])
                    queued += 1
                except (OSError, ValueError, sqlite3.Error) as exc:
                    if saved_path is not None:
                        saved_path.unlink(missing_ok=True)
                    st.error(f"{uploaded_file.name}: {exc}")
            if queued:
                st.success(f"{queued} vídeo(s) adicionado(s) à fila do YouTube.")

    st.divider()
    st.subheader("Publicação manual")
    privacy = st.selectbox(
        "Privacidade no YouTube",
        options=["private", "unlisted", "public"],
        format_func={"private": "Privado", "unlisted": "Não listado", "public": "Público"}.get,
        help="Vídeos públicos ficam visíveis para qualquer pessoa. A opção padrão é Privado.",
    )
    public_confirmed = True
    if privacy == "public":
        public_confirmed = st.checkbox("Confirmo que estes vídeos serão publicados publicamente.")
    if st.button("Publicar vídeos pendentes", type="primary", disabled=(privacy == "public" and not public_confirmed)):
        if not youtube.is_logged_in():
            st.error("Conecte uma conta do YouTube na aba Conta YouTube antes de publicar.")
        else:
            with st.spinner("Enviando vídeos para o YouTube…"):
                posted, failed = publish_pending(youtube, privacy)
            st.success(f"Publicados: {posted} · Com falha: {failed}")
    if st.button("Recolocar falhas na fila"):
        retried = db.retry_failed_targets()
        st.info(f"{retried} destino(s) aguardando nova tentativa.")

    st.divider()
    st.subheader("Limpeza de mídias publicadas")
    if MEDIA_RETENTION_DAYS == 0:
        st.info("Limpeza desativada. Defina MEDIA_RETENTION_DAYS no .env para habilitar a ação manual.")
    else:
        eligible_media_count = db.count_expired_posted_media(MEDIA_RETENTION_DAYS)
        st.caption(
            f"Remove do disco somente vídeos com todos os destinos publicados há pelo menos "
            f"{MEDIA_RETENTION_DAYS} dia(s). {eligible_media_count} registro(s) elegível(is) agora. "
            "Itens pendentes, em andamento, com falha ou parciais são preservados."
        )
        with st.form("cleanup_posted_media", clear_on_submit=True):
            cleanup_confirmed = st.checkbox("Confirmo a remoção local dos arquivos elegíveis.")
            cleanup_submitted = st.form_submit_button(
                "Limpar mídias publicadas vencidas",
                disabled=not cleanup_confirmed or eligible_media_count == 0,
            )
        if cleanup_submitted:
            cleanup_result = db.cleanup_expired_posted_media(MEDIA_RETENTION_DAYS)
            st.success(
                f"Mídias removidas: {cleanup_result['deleted']} · "
                f"Candidatas preservadas: {cleanup_result['skipped']}"
            )

    rows = db.list_queue()
    if rows:
        frame = pd.DataFrame(rows)
        display_columns = ["id", "title", "status", "platform", "target_status", "message", "created_at"]
        st.dataframe(frame[display_columns], use_container_width=True, hide_index=True)
    else:
        st.info("A fila está vazia.")

with tabs[2]:
    st.subheader("Conta YouTube")
    if youtube.is_logged_in():
        st.success("Credencial OAuth disponível.")
        st.write("Token: " + str(youtube.token_file))
    else:
        st.warning("Nenhuma credencial válida foi encontrada.")
    st.markdown(
        "Para conectar, configure um OAuth Client ID de aplicativo para computador no Google Cloud "
        "e execute `python -m social_automation.youtube_auth` no computador que tem acesso ao navegador. "
        "O painel nunca recebe nem armazena a senha da conta Google."
    )
    if st.button("Desconectar YouTube"):
        if youtube.token_file.exists():
            youtube.token_file.unlink()
        st.success("Token removido.")
        st.rerun()

with tabs[3]:
    st.subheader("Registros recentes")
    logs = db.list_logs()
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro ainda.")
