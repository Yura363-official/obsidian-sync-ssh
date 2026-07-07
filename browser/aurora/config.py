"""Пути, настройки по умолчанию и хранилище конфигурации Aurora."""
from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "Aurora"

# Все пользовательские данные храним в домашней папке пользователя (локально).
DATA_DIR = Path(os.environ.get("AURORA_HOME", Path.home() / ".aurora"))
PROFILE_DIR = DATA_DIR / "profile"
EXTENSIONS_DIR = DATA_DIR / "extensions"
DB_PATH = DATA_DIR / "aurora.db"
CONFIG_PATH = DATA_DIR / "config.json"
GOOGLE_CLIENT_SECRET = DATA_DIR / "google_client_secret.json"
GOOGLE_TOKEN = DATA_DIR / "google_token.json"

# Репозиторий с примерами расширений (рядом с пакетом).
BUILTIN_EXTENSIONS_DIR = Path(__file__).resolve().parent.parent / "extensions"

DEFAULTS = {
    "home_page": "aurora://home",
    "search_engine": "https://www.google.com/search?q={q}",
    "search_suggest": "https://suggestqueries.google.com/complete/search?client=firefox&q={q}",
    "theme": "dark",              # dark | light
    "restore_tabs": True,
    "block_ads": False,           # простой блокировщик по хостам
    "do_not_track": True,
    "default_zoom": 1.0,
    "download_dir": str(Path.home() / "Downloads"),
    "sync_enabled": False,
    "sync_interval_min": 10,
}

SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={q}",
    "DuckDuckGo": "https://duckduckgo.com/?q={q}",
    "Bing": "https://www.bing.com/search?q={q}",
    "Yandex": "https://yandex.ru/search/?text={q}",
}


def ensure_dirs() -> None:
    for p in (DATA_DIR, PROFILE_DIR, EXTENSIONS_DIR):
        p.mkdir(parents=True, exist_ok=True)


class Config:
    """Простое JSON-хранилище настроек с доступом как к словарю."""

    def __init__(self) -> None:
        ensure_dirs()
        self._data = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        if CONFIG_PATH.exists():
            try:
                self._data.update(json.loads(CONFIG_PATH.read_text("utf-8")))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        ensure_dirs()
        CONFIG_PATH.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), "utf-8")

    def get(self, key: str, default=None):
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def as_dict(self) -> dict:
        return dict(self._data)
