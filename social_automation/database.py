"""SQLite persistence for queued videos and per-platform publishing results."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sqlite3


DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parents[1] / "data")).expanduser().resolve()
DB_PATH = Path(os.environ.get("DB_PATH", DATA_DIR / "data.db")).expanduser().resolve()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    connection = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    try:
        os.chmod(DB_PATH, 0o600)
    except OSError:
        pass
    return connection


@contextmanager
def get_db():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(DATA_DIR, 0o700)
    except OSError:
        pass
    with get_db() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                posted_at TIMESTAMP
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS video_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
                platform TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending', 'processing', 'posted', 'error')),
                remote_id TEXT,
                message TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                posted_at TIMESTAMP,
                UNIQUE(video_id, platform)
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER REFERENCES videos(id) ON DELETE SET NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS accounts (
                platform TEXT PRIMARY KEY,
                connected BOOLEAN NOT NULL DEFAULT 0,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_video_targets_status ON video_targets(status, created_at)"
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC)")


def enqueue_video(
    file_path: Path,
    title: str,
    description: str,
    tags: list[str],
    platforms: list[str],
) -> int:
    normalized_platforms = list(dict.fromkeys(platforms))
    if not normalized_platforms:
        raise ValueError("Selecione pelo menos uma plataforma disponível.")
    with get_db() as connection:
        cursor = connection.execute(
            "INSERT INTO videos (file_path, title, description, tags) VALUES (?, ?, ?, ?)",
            (str(Path(file_path).resolve()), title.strip(), description.strip(), ",".join(tags)),
        )
        video_id = int(cursor.lastrowid)
        connection.executemany(
            "INSERT INTO video_targets (video_id, platform) VALUES (?, ?)",
            [(video_id, platform) for platform in normalized_platforms],
        )
        connection.executemany(
            "INSERT INTO logs (video_id, platform, status, message) VALUES (?, ?, ?, ?)",
            [(video_id, platform, "pending", "Adicionado à fila.") for platform in normalized_platforms],
        )
    return video_id


def list_queue(limit: int = 500) -> list[dict]:
    with get_db() as connection:
        rows = connection.execute(
            """SELECT v.id, v.title, v.status, v.created_at, v.file_path,
                      t.id AS target_id, t.platform, t.status AS target_status,
                      t.remote_id, t.message, t.posted_at
               FROM videos AS v
               LEFT JOIN video_targets AS t ON t.video_id = v.id
               ORDER BY v.created_at DESC, t.id ASC
               LIMIT ?""",
            (max(1, min(limit, 2000)),),
        ).fetchall()
    return [dict(row) for row in rows]


def list_pending_targets(limit: int = 100) -> list[dict]:
    with get_db() as connection:
        rows = connection.execute(
            """SELECT t.id AS target_id, t.video_id, t.platform,
                      v.file_path, v.title, v.description, v.tags
               FROM video_targets AS t
               JOIN videos AS v ON v.id = t.video_id
               WHERE t.status = 'pending'
               ORDER BY t.created_at ASC, t.id ASC
               LIMIT ?""",
            (max(1, min(limit, 500)),),
        ).fetchall()
    return [dict(row) for row in rows]


def claim_target(target_id: int) -> bool:
    with get_db() as connection:
        cursor = connection.execute(
            """UPDATE video_targets
               SET status = 'processing', message = 'Upload em andamento.',
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND status = 'pending'""",
            (target_id,),
        )
        if cursor.rowcount != 1:
            return False
        row = connection.execute(
            "SELECT video_id, platform FROM video_targets WHERE id = ?", (target_id,)
        ).fetchone()
        connection.execute(
            "INSERT INTO logs (video_id, platform, status, message) VALUES (?, ?, ?, ?)",
            (row["video_id"], row["platform"], "processing", "Upload iniciado pelo painel."),
        )
        connection.execute(
            "UPDATE videos SET status = 'processing', posted_at = NULL WHERE id = ?",
            (row["video_id"],),
        )
    return True


def finish_target(target_id: int, status: str, message: str, remote_id: str | None = None) -> None:
    if status not in {"posted", "error"}:
        raise ValueError("Status final de plataforma inválido.")
    clean_message = " ".join(str(message).split())[:500]
    with get_db() as connection:
        row = connection.execute(
            "SELECT video_id, platform FROM video_targets WHERE id = ?", (target_id,)
        ).fetchone()
        if row is None:
            raise LookupError("Destino da fila não encontrado.")
        connection.execute(
            """UPDATE video_targets
               SET status = ?, remote_id = ?, message = ?, updated_at = CURRENT_TIMESTAMP,
                   posted_at = CASE WHEN ? = 'posted' THEN CURRENT_TIMESTAMP ELSE NULL END
               WHERE id = ?""",
            (status, remote_id, clean_message, status, target_id),
        )
        connection.execute(
            "INSERT INTO logs (video_id, platform, status, message) VALUES (?, ?, ?, ?)",
            (row["video_id"], row["platform"], status, clean_message),
        )
        statuses = [
            item[0]
            for item in connection.execute(
                "SELECT status FROM video_targets WHERE video_id = ?", (row["video_id"],)
            ).fetchall()
        ]
        if statuses and all(item == "posted" for item in statuses):
            video_status, posted_at = "posted", "CURRENT_TIMESTAMP"
        elif "pending" in statuses or "processing" in statuses:
            video_status = "processing" if "processing" in statuses else "pending"
            posted_at = "NULL"
        elif "posted" in statuses and "error" in statuses:
            video_status, posted_at = "partial", "NULL"
        else:
            video_status, posted_at = "error", "NULL"
        connection.execute(
            f"UPDATE videos SET status = ?, posted_at = {posted_at} WHERE id = ?",
            (video_status, row["video_id"]),
        )


def retry_failed_targets() -> int:
    with get_db() as connection:
        rows = connection.execute(
            "SELECT video_id, platform FROM video_targets WHERE status = 'error'"
        ).fetchall()
        connection.execute(
            """UPDATE video_targets
               SET status = 'pending', message = 'Aguardando nova tentativa.',
                   updated_at = CURRENT_TIMESTAMP
               WHERE status = 'error'"""
        )
        connection.execute(
            "UPDATE videos SET status = 'pending', posted_at = NULL WHERE status IN ('error', 'partial')"
        )
        connection.executemany(
            "INSERT INTO logs (video_id, platform, status, message) VALUES (?, ?, ?, ?)",
            [(row["video_id"], row["platform"], "pending", "Falha recolocada na fila manualmente.") for row in rows],
        )
    return len(rows)


def _expired_posted_media_candidates(retention_days: int) -> tuple[list[tuple[int, str]], Path]:
    if type(retention_days) is not int or not 1 <= retention_days <= 36500:
        raise ValueError("A retenção deve estar entre 1 e 36500 dias.")

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_text = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    asset_root = (DATA_DIR / "assets").resolve()
    with get_db() as connection:
        candidates = connection.execute(
            """SELECT v.id, v.file_path
               FROM videos AS v
               WHERE v.status = 'posted' AND v.posted_at IS NOT NULL AND v.posted_at <= ?
                 AND EXISTS (
                     SELECT 1 FROM video_targets AS t WHERE t.video_id = v.id
                 )
                 AND NOT EXISTS (
                     SELECT 1 FROM video_targets AS t
                     WHERE t.video_id = v.id AND t.status != 'posted'
                 )
               ORDER BY v.posted_at, v.id""",
            (cutoff_text,),
        ).fetchall()
    return [(int(row["id"]), str(row["file_path"])) for row in candidates], asset_root


def count_expired_posted_media(retention_days: int) -> int:
    candidates, _ = _expired_posted_media_candidates(retention_days)
    return len(candidates)


def cleanup_expired_posted_media(retention_days: int) -> dict[str, int]:
    candidates, asset_root = _expired_posted_media_candidates(retention_days)

    result = {"deleted": 0, "skipped": 0}
    for video_id, stored_path in candidates:
        candidate = Path(stored_path).expanduser()
        log_id = None
        try:
            if candidate.is_symlink():
                result["skipped"] += 1
                continue
            file_path = candidate.resolve(strict=True)
            if not file_path.is_relative_to(asset_root) or not file_path.is_file():
                result["skipped"] += 1
                continue

            with get_db() as connection:
                cursor = connection.execute(
                    """INSERT INTO logs (video_id, platform, status, message)
                       VALUES (?, 'local-media', 'media_cleanup_started',
                               'Limpeza manual de mídia publicada iniciada.')""",
                    (video_id,),
                )
                log_id = int(cursor.lastrowid)
            file_path.unlink()
        except (OSError, RuntimeError):
            if log_id is not None:
                with get_db() as connection:
                    connection.execute(
                        "UPDATE logs SET status = 'media_cleanup_failed', message = ? WHERE id = ?",
                        ("Falha ao remover a mídia publicada.", log_id),
                    )
            result["skipped"] += 1
            continue

        with get_db() as connection:
            connection.execute(
                "UPDATE logs SET status = 'media_deleted', message = ? WHERE id = ?",
                ("Mídia local removida após o prazo de retenção.", log_id),
            )
        result["deleted"] += 1
    return result


def get_stats() -> dict[str, int]:
    with get_db() as connection:
        rows = connection.execute("SELECT status, COUNT(*) AS count FROM videos GROUP BY status").fetchall()
    result = {"total": 0, "posted": 0, "pending": 0, "processing": 0, "partial": 0, "error": 0}
    for row in rows:
        result[row["status"]] = row["count"]
        result["total"] += row["count"]
    return result


def list_logs(limit: int = 200) -> list[dict]:
    with get_db() as connection:
        rows = connection.execute(
            """SELECT id, video_id, platform, status, message, created_at
               FROM logs ORDER BY created_at DESC, id DESC LIMIT ?""",
            (max(1, min(limit, 1000)),),
        ).fetchall()
    return [dict(row) for row in rows]
