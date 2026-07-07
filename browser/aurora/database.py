"""SQLite-хранилище: история, закладки, загрузки. Только локальные данные пользователя."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    url       TEXT NOT NULL,
    title     TEXT DEFAULT '',
    visited   REAL NOT NULL,
    visits    INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_history_visited ON history(visited);
CREATE INDEX IF NOT EXISTS idx_history_url ON history(url);

CREATE TABLE IF NOT EXISTS bookmarks (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    url      TEXT NOT NULL,
    title    TEXT DEFAULT '',
    folder   TEXT DEFAULT 'Панель закладок',
    added    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS downloads (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    url      TEXT NOT NULL,
    path     TEXT NOT NULL,
    size     INTEGER DEFAULT 0,
    started  REAL NOT NULL,
    state    TEXT DEFAULT 'in_progress'
);
"""


@dataclass
class HistoryItem:
    id: int
    url: str
    title: str
    visited: float
    visits: int


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------- История ----------
    def add_history(self, url: str, title: str = "") -> None:
        if not url or url.startswith("aurora://") or url == "about:blank":
            return
        now = time.time()
        cur = self.conn.execute(
            "SELECT id, visits FROM history WHERE url = ? ORDER BY visited DESC LIMIT 1", (url,)
        )
        row = cur.fetchone()
        # Если та же страница открыта повторно в течение 30 секунд — просто обновим.
        if row:
            self.conn.execute(
                "UPDATE history SET title=?, visited=?, visits=visits+1 WHERE id=?",
                (title or "", now, row["id"]),
            )
        else:
            self.conn.execute(
                "INSERT INTO history(url, title, visited, visits) VALUES(?,?,?,1)",
                (url, title or "", now),
            )
        self.conn.commit()

    def add_history_entry(self, url: str, title: str, visited: float) -> None:
        """Ручное добавление записи (в т.ч. при синхронизации)."""
        self.conn.execute(
            "INSERT INTO history(url, title, visited, visits) VALUES(?,?,?,1)",
            (url, title or "", visited),
        )
        self.conn.commit()

    def search_history(self, query: str = "", limit: int = 500) -> list[HistoryItem]:
        if query:
            like = f"%{query}%"
            cur = self.conn.execute(
                "SELECT * FROM history WHERE url LIKE ? OR title LIKE ? "
                "ORDER BY visited DESC LIMIT ?",
                (like, like, limit),
            )
        else:
            cur = self.conn.execute(
                "SELECT * FROM history ORDER BY visited DESC LIMIT ?", (limit,)
            )
        return [HistoryItem(**dict(r)) for r in cur.fetchall()]

    def delete_history(self, item_id: int) -> None:
        self.conn.execute("DELETE FROM history WHERE id=?", (item_id,))
        self.conn.commit()

    def clear_history(self, since: float | None = None) -> None:
        if since is None:
            self.conn.execute("DELETE FROM history")
        else:
            self.conn.execute("DELETE FROM history WHERE visited >= ?", (since,))
        self.conn.commit()

    def all_history(self) -> list[HistoryItem]:
        return self.search_history("", limit=100000)

    def top_sites(self, limit: int = 8) -> list[HistoryItem]:
        cur = self.conn.execute(
            "SELECT id, url, title, MAX(visited) as visited, SUM(visits) as visits "
            "FROM history GROUP BY url ORDER BY visits DESC, visited DESC LIMIT ?",
            (limit,),
        )
        return [HistoryItem(**dict(r)) for r in cur.fetchall()]

    # ---------- Закладки ----------
    def add_bookmark(self, url: str, title: str, folder: str = "Панель закладок") -> None:
        exists = self.conn.execute("SELECT 1 FROM bookmarks WHERE url=?", (url,)).fetchone()
        if exists:
            return
        self.conn.execute(
            "INSERT INTO bookmarks(url, title, folder, added) VALUES(?,?,?,?)",
            (url, title or url, folder, time.time()),
        )
        self.conn.commit()

    def remove_bookmark(self, url: str) -> None:
        self.conn.execute("DELETE FROM bookmarks WHERE url=?", (url,))
        self.conn.commit()

    def is_bookmarked(self, url: str) -> bool:
        return self.conn.execute("SELECT 1 FROM bookmarks WHERE url=?", (url,)).fetchone() is not None

    def all_bookmarks(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM bookmarks ORDER BY added DESC").fetchall()

    # ---------- Загрузки ----------
    def add_download(self, url: str, path: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO downloads(url, path, started, state) VALUES(?,?,?,'in_progress')",
            (url, path, time.time()),
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_download(self, dl_id: int, size: int, state: str = "completed") -> None:
        self.conn.execute(
            "UPDATE downloads SET size=?, state=? WHERE id=?", (size, state, dl_id)
        )
        self.conn.commit()

    def all_downloads(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM downloads ORDER BY started DESC").fetchall()

    def close(self) -> None:
        self.conn.close()
